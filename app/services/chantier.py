# app/services/chantier_service.py
# Module de gestion du transfert des chantiers
# Ce fichier contient les fonctions nécessaires pour transférer les données
# des chantiers depuis SQL Server vers PostgreSQL

import psycopg2
from app.services.connex import connect_to_sqlserver, connect_to_postgres, load_credentials, recup_batisimply_token
import requests
import json
from datetime import date

# ============================================================================
# TRANSFERT VERS POSTGRESQL
# ============================================================================

def transfer_chantiers():
    """
    Transfère les données des chantiers depuis SQL Server vers PostgreSQL.
    
    Cette fonction :
    1. Vérifie les identifiants de connexion
    2. Établit les connexions aux deux bases de données
    3. Récupère les chantiers depuis SQL Server
    4. Les insère dans PostgreSQL en ignorant les doublons
    5. Ferme proprement les connexions
    
    Returns:
        tuple: (bool, str)
            - bool: True si le transfert a réussi, False sinon
            - str: Message décrivant le résultat de l'opération
    """
    try:
        # Vérification des identifiants
        creds = load_credentials()
        if not creds or "sqlserver" not in creds or "postgres" not in creds:
            return False, "❌ Informations de connexion manquantes"

        sql = creds["sqlserver"]
        pg = creds["postgres"]

        # Établissement des connexions
        sqlserver_conn = connect_to_sqlserver(
            sql["server"], sql["user"], sql["password"], sql["database"]
        )
        postgres_conn = connect_to_postgres(
            pg["host"], pg["user"], pg["password"], pg["database"], pg.get("port", "5432")
        )

        if not sqlserver_conn or not postgres_conn:
            return False, "❌ Connexion aux bases échouée"

        # Création des curseurs pour l'exécution des requêtes
        sqlserver_cursor = sqlserver_conn.cursor()
        postgres_cursor = postgres_conn.cursor()

        # Récupération des chantiers depuis SQL Server
        sqlserver_cursor.execute("""
            SELECT ChantierDef.Code, DateDebut, DateFin, NomClient, Libelle, AdrChantier, CPChantier, VilleChantier, SUM(TempsMO) AS "TotalMo"
            FROM dbo.ChantierDef
            JOIN Devis ON devis.CodeClient = ChantierDef.CodeClient
            WHERE Devis.Etat = 3
            GROUP BY chantierDef.Code, DateDebut, DateFin, NomClient, Libelle, AdrChantier, CPChantier, VilleChantier
        """)
        rows = sqlserver_cursor.fetchall()

        # Insertion des chantiers dans PostgreSQL
        for row in rows:
            code, date_debut, date_fin, nom_client, description, adr_chantier, cp_chantier, ville_chantier, TotalMo = row
            # Utilisation de ON CONFLICT pour éviter les doublons
            postgres_cursor.execute(
                """
                INSERT INTO batigest_chantiers 
                (code, date_debut, date_fin, nom_client, description, adr_chantier, cp_chantier, ville_chantier, total_mo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (code) DO UPDATE SET 
                date_debut = EXCLUDED.date_debut,
                date_fin = EXCLUDED.date_fin,
                nom_client = EXCLUDED.nom_client,
                description = EXCLUDED.description,
                adr_chantier = EXCLUDED.adr_chantier,
                cp_chantier = EXCLUDED.cp_chantier,
                ville_chantier = EXCLUDED.ville_chantier,
                total_mo = EXCLUDED.total_mo,
                sync = EXCLUDED.sync = False
                """,
                (code, date_debut, date_fin, nom_client, description, adr_chantier, cp_chantier, ville_chantier, TotalMo)
            )

        # Validation des modifications dans PostgreSQL
        postgres_conn.commit()

        # Fermeture propre des connexions
        sqlserver_cursor.close()
        postgres_cursor.close()
        sqlserver_conn.close()
        postgres_conn.close()

        return True, "✅ Transfert terminé avec succès"

    except Exception as e:
        # En cas d'erreur, on retourne le message d'erreur
        return False, f"❌ Erreur lors du transfert : {e}"

# ============================================================================
# TRANSFERT VERS BATISIMPLY
# ============================================================================

def transfer_chantiers_vers_batisimply():
    """
    Transfère les chantiers depuis PostgreSQL vers BatiSimply.
    
    Cette fonction :
    1. Récupère le token d'authentification
    2. Vérifie les identifiants PostgreSQL
    3. Récupère les chantiers non synchronisés
    4. Les envoie à l'API BatiSimply (POST pour nouveaux, PUT pour existants)
    5. Met à jour le statut de synchronisation
    
    Returns:
        bool: True si au moins un chantier a été transféré avec succès, False sinon
    """
    # Récupération du token
    token = recup_batisimply_token()
    if not token:
        print("Impossible de continuer sans token.")
        return False

    # Vérification des identifiants PostgreSQL
    creds = load_credentials()
    if not creds or "postgres" not in creds:
        print("❌ Informations Postgres manquantes.")
        return False

    # Connexion à PostgreSQL
    pg = creds["postgres"]
    postgres_conn = connect_to_postgres(
        pg["host"], pg["user"], pg["password"], pg["database"], pg.get("port", "5432")
    )

    if not postgres_conn:
        print("❌ Connexion à la base Postgres échouée.")
        return False

    # Configuration de l'API BatiSimply
    API_URL = "https://api.staging.batisimply.fr/api/project"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Récupération des chantiers non synchronisés
    postgres_cursor = postgres_conn.cursor()
    postgres_cursor.execute("""
        SELECT code, date_debut, date_fin, nom_client, description, adr_chantier, cp_chantier, ville_chantier, total_mo
        FROM batigest_chantiers
        WHERE sync = false
    """)

    rows = postgres_cursor.fetchall()
    success = False

    # Récupération des chantiers existants dans BatiSimply
    existing_projects = {}
    response = requests.get(API_URL, headers=headers)
    if response.status_code == 200:
        projects = response.json().get("elements", [])
        for project in projects:
            existing_projects[project.get('projectCode')] = project.get('id')

    # Traitement de chaque chantier
    for row in rows:
        code, date_debut, date_fin, nom_client, description, adr, cp, ville, total_mo = row

        # Préparation des données pour l'API
        data = {
            "address": {
                "city": ville,
                "countryCode": "FR",
                "geoPoint": {
                    "xLon": 3.8777,
                    "yLat": 43.6119
                },
                "googleFormattedAddress": f"{adr}, {cp} {ville}, France",
                "postalCode": cp,
                "street": adr
            },
            "budget": {
                "amount": 500000.0,
                "currency": "EUR"
            },
            "endEstimated": date_fin.strftime("%Y-%m-%d") if date_fin else None,
            "headQuarter": {
                "id": 33
            },
            "hoursSold": total_mo,
            "projectCode": code,
            "comment": description,
            "projectName": nom_client,
            "customerName": nom_client,
            "projectManager": "DEFINIR",
            "startEstimated": date_debut.strftime("%Y-%m-%d") if date_debut else None,
            "isArchived": False,
            "isFinished": False,
            "projectColor": "#9b1ff1"
        }

        # Détermination de la méthode HTTP
        if code in existing_projects:
            project_id = existing_projects[code]
            method = "PUT"
            url = API_URL
            # Inclure l'id dans le payload pour la mise à jour
            data["id"] = project_id
            print(f"🔄 Mise à jour du projet existant '{code}' (ID: {data['id']})")
        else:
            method = "POST"
            url = API_URL
            print(f"➕ Création du nouveau projet '{code}'")

        # Envoi à l'API et mise à jour du statut
        response = requests.request(method, url, headers=headers, data=json.dumps(data))
        if response.status_code in [200, 201]:
            print(f"✅ Projet '{code}' traité avec succès")
            postgres_cursor.execute(
                "UPDATE batigest_chantiers SET sync = true, sync_date = NOW() WHERE code = %s", (code,))
            postgres_conn.commit()
            success = True
        else:
            print(f"❌ Erreur pour le projet '{code}' : {response.status_code} → {response.text}")

    # Nettoyage
    postgres_cursor.close()
    postgres_conn.close()

    return success

# ============================================================================
# Récupération des chantiers depuis Batisimply
# ============================================================================

def recup_chantiers_batisimply():
    """
    Récupère les chantiers depuis BatiSimply.
    
    Cette fonction :
    1. Récupère le token d'authentification
    2. Récupère les chantiers depuis BatiSimply via l'API
    3. Stocke les données dans une variable
    4. Retourne la variable
    """
    # Récupération du token
    token = recup_batisimply_token()
    if not token:
        print("Impossible de continuer sans token.")
        return False

    # Configuration de l'API BatiSimply
    API_URL = "https://api.staging.batisimply.fr/api/project"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Récupération des chantiers depuis BatiSimply
    response = requests.get(API_URL, headers=headers)
    if response.status_code == 200:
        chantiers_json = response.json()
        chantiers = chantiers_json.get("elements", [])
        return chantiers
    else:
        print(f"❌ Erreur pour la récupération des chantiers : {response.status_code} → {response.text}")
        return False
    
# ============================================================================
# Récupération des chantiers depuis Batigest
# ============================================================================

def recup_chantiers_postgres():
    """
    Récupère les chantiers depuis Batigest.
    
    Cette fonction :
    1. Récupère les chantiers de Batigest depuis PostgreSQL
    2. Stocke les données dans une variable
    3. Retourne la variable
    """
    # Connexions à PostgreSQL
    creds = load_credentials()
    pg = creds["postgres"]
    postgres_conn = connect_to_postgres(
        pg["host"], pg["user"], pg["password"], pg["database"], pg.get("port", "5432")
    )
    if not postgres_conn:
        print("❌ Connexion à la base PostgreSQL échouée.")
        return False
    
    # Récupération des chantiers de Batigest depuis PostgreSQL
    postgres_cursor = postgres_conn.cursor()
    postgres_cursor.execute("SELECT code FROM batigest_chantiers")
    chantiers_batigest = postgres_cursor.fetchall()
    postgres_cursor.close()
    postgres_conn.close()
    return chantiers_batigest

# ============================================================================
# Récupération du code projet des chantiers
# ============================================================================

def recup_code_projet_chantiers():
    """
    Récupère les codes projet des chantiers en commun entre Batisimply et Batigest.
    
    Cette fonction :
    1. Récupère les chantiers depuis Batisimply
    2. Récupère les chantiers depuis Batigest
    3. Compare les codes des chantiers
    4. Retourne les codes en commun
    """
    # Récupération des chantiers depuis Batisimply
    chantiers_batisimply = recup_chantiers_batisimply()
    if not chantiers_batisimply:
        print("❌ Impossible de récupérer les chantiers depuis BatiSimply")
        return []

    # Récupération des chantiers depuis Batigest
    chantiers_batigest = recup_chantiers_postgres()
    if not chantiers_batigest:
        print("❌ Impossible de récupérer les chantiers depuis Batigest")
        return []

    # Comparaison des codes des chantiers
    codes_projet_communs = []
    for chantier in chantiers_batisimply:
        try:
            code = chantier.get('projectCode')
            id_projet = chantier.get('id')
            if code and id_projet and code in [c[0] for c in chantiers_batigest]:
                codes_projet_communs.append({
                    'code': code,
                    'id_projet': id_projet
                })
        except Exception as e:
            print(f"❌ Erreur lors du traitement du chantier : {e}")
            continue

    print(f"✅ {len(codes_projet_communs)} codes projet trouvés")
    return codes_projet_communs

# ============================================================================
# Vérification du contenu de la table batigest_heures
# ============================================================================

def check_batigest_heures_content():
    """
    Vérifie le contenu de la table batigest_heures pour déboguer.
    Cette fonction :
    1. Vérifie le contenu de la table batigest_heures
    2. Affiche le contenu de la table
    3. Ferme la connexion à PostgreSQL
    """

    print("\n=== VÉRIFICATION DU CONTENU DE LA TABLE BATIGEST_HEURES ===")
    
    # Connexion PostgreSQL
    creds = load_credentials()
    if not creds or "postgres" not in creds:
        print("❌ Informations Postgres manquantes.")
        return False

    pg = creds["postgres"]
    postgres_conn = connect_to_postgres(
        pg["host"], pg["user"], pg["password"], pg["database"], pg.get("port", "5432")
    )
    if not postgres_conn:
        print("❌ Connexion à PostgreSQL échouée.")
        return False

    postgres_cursor = postgres_conn.cursor()

    # Vérification des enregistrements
    postgres_cursor.execute("""
        SELECT code_projet, COUNT(*) as count 
        FROM batigest_heures 
        WHERE code_projet IS NOT NULL 
        GROUP BY code_projet
    """)
    
    results = postgres_cursor.fetchall()
    print("\n📊 Contenu de la table batigest_heures :")
    if results:
        for code, count in results:
            print(f"  - Code: {code}, Nombre d'enregistrements: {count}")
    else:
        print("  ⚠️ Aucun enregistrement trouvé avec un code_projet non NULL")

    # Fermeture propre
    postgres_cursor.close()
    postgres_conn.close()
    
    print("=== FIN DE LA VÉRIFICATION ===")
    return True

# ============================================================================
# Mise à jour des codes projet des chantiers
# ============================================================================

def update_code_projet_chantiers():
    """
    Met à jour les codes projet des chantiers dans PostgreSQL.

    Cette fonction :
    1. Récupère les correspondances code ↔ id_projet entre Batisimply et Batigest
    2. Met à jour la table `batigest_heures` en insérant le `code_projet` pour chaque `code`
    3. Ferme la connexion à PostgreSQL
    4. Affiche le nombre de mises à jour effectuées
    5. Affiche le détail des mises à jour effectuées
    6. Affiche un message de succès si les mises à jour ont été effectuées
    7. Affiche un message d'erreur si aucune mise à jour n'a été effectuée
    """
    print("=== DÉBUT DE LA MISE À JOUR DES CODES PROJET ===")
    
    # Vérification du contenu actuel
    check_batigest_heures_content()
    
    # Récupération des correspondances depuis les deux systèmes
    codes_projet_communs = recup_code_projet_chantiers()
    print(f"✅ {len(codes_projet_communs)} codes projet trouvés")
    
    if not codes_projet_communs:
        print("❌ Aucun code projet trouvé")
        return False

    print("\n📊 Nombre de correspondances trouvées :", len(codes_projet_communs))
    print("Détail des correspondances :")
    for code_projet in codes_projet_communs:
        print(f"  - Code: {code_projet['code']}, ID Projet: {code_projet['id_projet']}")

    # Connexion PostgreSQL
    creds = load_credentials()
    if not creds or "postgres" not in creds:
        print("❌ Informations Postgres manquantes.")
        return False

    pg = creds["postgres"]
    postgres_conn = connect_to_postgres(
        pg["host"], pg["user"], pg["password"], pg["database"], pg.get("port", "5432")
    )
    if not postgres_conn:
        print("❌ Connexion à PostgreSQL échouée.")
        return False

    print("✅ Connexion PostgreSQL réussie")
    postgres_cursor = postgres_conn.cursor()

    # Vérification de la structure de la table
    postgres_cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'batigest_heures'
    """)
    columns = postgres_cursor.fetchall()
    print("\n📋 Vérification de la structure de la table :")
    for col in columns:
        print(f"  - {col[0]}: {col[1]}")

    print("\n🔄 Début des mises à jour :")
    updates_count = 0

    # Mise à jour ligne par ligne
    for code_projet in codes_projet_communs:
        try:
            code = code_projet.get('code')
            id_projet = code_projet.get('id_projet')
            if code is None or id_projet is None:
                raise ValueError(f"Données manquantes : {code_projet}")

            print(f"\n🔍 Traitement du code : {code} -> id_projet : {id_projet}")
            
            # Mise à jour sans condition
            postgres_cursor.execute(
                "UPDATE batigest_heures SET code_projet = %s WHERE id_projet = %s",
                (str(code), id_projet)
            )
            
            # Vérification après mise à jour
            postgres_cursor.execute(
                "SELECT COUNT(*) FROM batigest_heures WHERE code_projet = %s",
                (str(code),)
            )
            updated_count = postgres_cursor.fetchone()[0]
            print(f"  ✅ Mise à jour effectuée : {updated_count} enregistrements modifiés")
            
            updates_count += updated_count

        except Exception as e:
            print(f"❌ Erreur pour le code projet {code_projet} : {e}")

    # Commit final
    postgres_conn.commit()
    print(f"\n📊 Total des mises à jour effectuées : {updates_count}")

    # Fermeture propre
    postgres_cursor.close()
    postgres_conn.close()

    if updates_count == 0:
        print("\n⚠️ Aucune mise à jour n'a été effectuée.")
    else:
        print("\n✅ Mise à jour des codes projet terminée avec succès.")
    
    print("=== FIN DE LA MISE À JOUR DES CODES PROJET ===")
    return True

# ============================================================================
# SYNCHRONISATION DE BATIGEST VERS BATISIMPLY
# ============================================================================

def sync_batigest_to_batisimply():
    """
    Synchronise les chantiers de Batigest vers Batisimply via PostgreSQL.
    
    Flux : Batigest (SQL Server) → PostgreSQL → Batisimply
    
    Returns:
        tuple: (bool, str)
            - bool: True si la synchronisation a réussi, False sinon
            - str: Message décrivant le résultat de l'opération
    """
    try:
        print("\n=== DÉBUT DE LA SYNCHRONISATION BATIGEST → BATISIMPLY ===")
        
        # Récupération du token Batisimply
        token = recup_batisimply_token()
        if not token:
            return False, "❌ Impossible de continuer sans token Batisimply"

        # Configuration de l'API BatiSimply
        API_URL = "https://api.staging.batisimply.fr/api/project"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Connexion aux bases de données
        creds = load_credentials()
        if not creds or "postgres" not in creds or "sqlserver" not in creds:
            return False, "❌ Informations de connexion manquantes"

        pg = creds["postgres"]
        sql = creds["sqlserver"]

        postgres_conn = connect_to_postgres(
            pg["host"], pg["user"], pg["password"], pg["database"], pg.get("port", "5432")
        )
        sqlserver_conn = connect_to_sqlserver(
            sql["server"], sql["user"], sql["password"], sql["database"]
        )

        if not postgres_conn or not sqlserver_conn:
            return False, "❌ Connexion aux bases de données échouée"

        print("✅ Connexions aux bases de données établies")

        # 1. Synchronisation Batigest → PostgreSQL
        print("\n🔄 Synchronisation Batigest → PostgreSQL")
        sqlserver_cursor = sqlserver_conn.cursor()
        postgres_cursor = postgres_conn.cursor()

        # Récupération des chantiers actifs depuis Batigest
        sqlserver_cursor.execute("""
            SELECT 
                Code,
                DateDebut,
                DateFin,
                NomClient,
                Libelle,
                AdrChantier,
                CPChantier,
                VilleChantier
            FROM dbo.ChantierDef
            WHERE DateFin IS NULL OR DateFin > GETDATE()
        """)
        
        batigest_chantiers = sqlserver_cursor.fetchall()
        print(f"📊 {len(batigest_chantiers)} chantiers récupérés depuis Batigest")

        # Mise à jour de PostgreSQL avec les données de Batigest
        updated_batigest = 0
        for chantier in batigest_chantiers:
            try:
                code, date_debut, date_fin, nom_client, description, adr, cp, ville = chantier
                
                # Mise à jour dans PostgreSQL
                postgres_cursor.execute("""
                    INSERT INTO batigest_chantiers 
                    (code, date_debut, date_fin, nom_client, description, adr_chantier, 
                     cp_chantier, ville_chantier, last_modified_batigest)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (code) DO UPDATE SET 
                    date_debut = EXCLUDED.date_debut,
                    date_fin = EXCLUDED.date_fin,
                    nom_client = EXCLUDED.nom_client,
                    description = EXCLUDED.description,
                    adr_chantier = EXCLUDED.adr_chantier,
                    cp_chantier = EXCLUDED.cp_chantier,
                    ville_chantier = EXCLUDED.ville_chantier,
                    last_modified_batigest = NOW()
                """, (code, date_debut, date_fin, nom_client, description, adr, cp, ville))
                updated_batigest += 1
                print(f"✅ Chantier {code} mis à jour dans PostgreSQL")
            except Exception as e:
                print(f"❌ Erreur lors de la mise à jour du chantier {code} dans PostgreSQL : {e}")

        # 2. Synchronisation PostgreSQL → Batisimply
        print("\n🔄 Synchronisation PostgreSQL → Batisimply")
        
        # Récupération des chantiers modifiés dans Batigest
        postgres_cursor.execute("""
            SELECT code, date_debut, date_fin, nom_client, description, adr_chantier, 
                   cp_chantier, ville_chantier, total_mo
            FROM batigest_chantiers
            WHERE last_modified_batigest > COALESCE(last_modified_batisimply, '1970-01-01'::timestamp)
        """)
        
        # Récupération des chantiers existants dans Batisimply
        response = requests.get(API_URL, headers=headers)
        if response.status_code != 200:
            return False, f"❌ Erreur lors de la récupération des chantiers Batisimply : {response.status_code}"

        batisimply_projects = {}
        for project in response.json().get("elements", []):
            code = project.get('projectCode')
            if code:
                batisimply_projects[code] = project

        # Synchronisation vers Batisimply
        updated_to_batisimply = 0
        for row in postgres_cursor.fetchall():
            try:
                code, date_debut, date_fin, nom_client, description, adr, cp, ville, total_mo = row
                
                # Préparation des données pour l'API
                data = {
                    "address": {
                        "city": ville,
                        "countryCode": "FR",
                        "geoPoint": {
                            "xLon": 3.8777,
                            "yLat": 43.6119
                        },
                        "googleFormattedAddress": f"{adr}, {cp} {ville}, France",
                        "postalCode": cp,
                        "street": adr
                    },
                    "budget": {
                        "amount": 500000.0,
                        "currency": "EUR"
                    },
                    "endEstimated": date_fin.strftime("%Y-%m-%d") if date_fin else None,
                    "headQuarter": {
                        "id": 33
                    },
                    "hoursSold": total_mo,
                    "projectCode": code,
                    "comment": description,
                    "projectName": nom_client,
                    "customerName": nom_client,
                    "projectManager": "DEFINIR",
                    "startEstimated": date_debut.strftime("%Y-%m-%d") if date_debut else None,
                    "isArchived": False,
                    "isFinished": False,
                    "projectColor": "#9b1ff1"
                }

                # Détermination de la méthode HTTP
                if code in batisimply_projects:
                    method = "PUT"
                    url = API_URL
                    # Inclure l'id dans le payload pour la mise à jour
                    data["id"] = batisimply_projects[code].get("id")
                    print(f"→ Mise à jour du projet existant {code} (ID: {data['id']})")
                else:
                    method = "POST"
                    url = API_URL
                    print(f"→ Création d'un nouveau projet {code}")

                # Envoi à l'API
                response = requests.request(method, url, headers=headers, data=json.dumps(data))
                if response.status_code in [200, 201]:
                    updated_to_batisimply += 1
                    # Mise à jour du timestamp dans PostgreSQL
                    postgres_cursor.execute("""
                        UPDATE batigest_chantiers 
                        SET last_modified_batisimply = NOW()
                        WHERE code = %s
                    """, (code,))
                    print(f"✅ Chantier {code} synchronisé vers Batisimply")
                else:
                    print(f"❌ Erreur API pour le chantier {code} : {response.status_code} → {response.text}")
            except Exception as e:
                print(f"❌ Erreur lors de la synchronisation du chantier {code} vers Batisimply : {e}")

        # Validation des modifications
        postgres_conn.commit()
        postgres_cursor.close()
        postgres_conn.close()
        sqlserver_cursor.close()
        sqlserver_conn.close()

        print("\n=== FIN DE LA SYNCHRONISATION BATIGEST → BATISIMPLY ===")

        # Préparation du message final
        message = "✅ Synchronisation Batigest → Batisimply terminée :\n"
        message += f"- {updated_batigest} chantiers mis à jour depuis Batigest vers PostgreSQL\n"
        message += f"- {updated_to_batisimply} chantiers synchronisés de PostgreSQL vers Batisimply"

        return True, message

    except Exception as e:
        print(f"\n❌ Erreur lors de la synchronisation : {e}")
        return False, f"❌ Erreur lors de la synchronisation : {e}"

# ============================================================================
# SYNCHRONISATION DE BATISIMPLY VERS BATIGEST
# ============================================================================

def sync_batisimply_to_batigest():
    """
    Synchronise les chantiers de Batisimply vers Batigest via PostgreSQL.
    
    Flux : Batisimply → PostgreSQL → Batigest (SQL Server)
    
    Returns:
        tuple: (bool, str)
            - bool: True si la synchronisation a réussi, False sinon
            - str: Message décrivant le résultat de l'opération
    """
    try:
        print("\n=== DÉBUT DE LA SYNCHRONISATION BATISIMPLY → BATIGEST ===")
        
        # Récupération du token Batisimply
        token = recup_batisimply_token()
        if not token:
            return False, "❌ Impossible de continuer sans token Batisimply"

        # Configuration de l'API BatiSimply
        API_URL = "https://api.staging.batisimply.fr/api/project"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Connexion aux bases de données
        creds = load_credentials()
        if not creds or "postgres" not in creds or "sqlserver" not in creds:
            return False, "❌ Informations de connexion manquantes"

        pg = creds["postgres"]
        sql = creds["sqlserver"]

        postgres_conn = connect_to_postgres(
            pg["host"], pg["user"], pg["password"], pg["database"], pg.get("port", "5432")
        )
        sqlserver_conn = connect_to_sqlserver(
            sql["server"], sql["user"], sql["password"], sql["database"]
        )

        if not postgres_conn or not sqlserver_conn:
            return False, "❌ Connexion aux bases de données échouée"

        print("✅ Connexions aux bases de données établies")

        # 1. Synchronisation Batisimply → PostgreSQL
        print("\n🔄 Synchronisation Batisimply → PostgreSQL")
        
        # Récupération des chantiers depuis Batisimply
        response = requests.get(API_URL, headers=headers)
        if response.status_code != 200:
            return False, f"❌ Erreur lors de la récupération des chantiers Batisimply : {response.status_code}"

        batisimply_projects = response.json().get("elements", [])
        print(f"📊 {len(batisimply_projects)} chantiers récupérés depuis Batisimply")

        # Mise à jour de PostgreSQL avec les données de Batisimply
        postgres_cursor = postgres_conn.cursor()
        updated_batisimply = 0
        for project in batisimply_projects:
            try:
                code = project.get('projectCode')
                if not code:
                    continue

                # Préparation des données
                data = {
                    'code': code,
                    'date_debut': project.get('startEstimated'),
                    'date_fin': project.get('endEstimated'),
                    'nom_client': project.get('customerName'),
                    'description': project.get('comment'),
                    'adr_chantier': project.get('address', {}).get('street'),
                    'cp_chantier': project.get('address', {}).get('postalCode'),
                    'ville_chantier': project.get('address', {}).get('city'),
                    'total_mo': project.get('hoursSold', 0)
                }

                # Mise à jour dans PostgreSQL
                postgres_cursor.execute("""
                    INSERT INTO batigest_chantiers 
                    (code, date_debut, date_fin, nom_client, description, adr_chantier, 
                     cp_chantier, ville_chantier, total_mo, last_modified_batisimply)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (code) DO UPDATE SET 
                    date_debut = EXCLUDED.date_debut,
                    date_fin = EXCLUDED.date_fin,
                    nom_client = EXCLUDED.nom_client,
                    description = EXCLUDED.description,
                    adr_chantier = EXCLUDED.adr_chantier,
                    cp_chantier = EXCLUDED.cp_chantier,
                    ville_chantier = EXCLUDED.ville_chantier,
                    total_mo = EXCLUDED.total_mo,
                    last_modified_batisimply = NOW()
                """, (
                    data['code'], data['date_debut'], data['date_fin'],
                    data['nom_client'], data['description'], data['adr_chantier'],
                    data['cp_chantier'], data['ville_chantier'], data['total_mo']
                ))
                updated_batisimply += 1
                print(f"✅ Chantier {code} mis à jour dans PostgreSQL")
            except Exception as e:
                print(f"❌ Erreur lors de la mise à jour du chantier {code} dans PostgreSQL : {e}")

        # 2. Synchronisation PostgreSQL → Batigest
        print("\n🔄 Synchronisation PostgreSQL → Batigest")
        
        # Récupération des chantiers modifiés dans Batisimply
        postgres_cursor.execute("""
            SELECT code, date_debut, date_fin, nom_client, description, adr_chantier, 
                   cp_chantier, ville_chantier
            FROM batigest_chantiers
            WHERE last_modified_batisimply > COALESCE(last_modified_batigest, '1970-01-01'::timestamp)
        """)
        
        # Mise à jour dans Batigest
        sqlserver_cursor = sqlserver_conn.cursor()
        updated_to_batigest = 0
        for row in postgres_cursor.fetchall():
            try:
                code, date_debut, date_fin, nom_client, description, adr, cp, ville = row
                
                # Mise à jour dans Batigest
                sqlserver_cursor.execute("""
                    UPDATE dbo.ChantierDef
                    SET DateDebut = ?,
                        DateFin = ?,
                        NomClient = ?,
                        Libelle = ?,
                        AdrChantier = ?,
                        CPChantier = ?,
                        VilleChantier = ?
                    WHERE Code = ?
                """, (date_debut, date_fin, nom_client, description, adr, cp, ville, code))
                
                updated_to_batigest += 1
                print(f"✅ Chantier {code} mis à jour dans Batigest")
            except Exception as e:
                print(f"❌ Erreur lors de la mise à jour du chantier {code} dans Batigest : {e}")

        # Validation des modifications
        postgres_conn.commit()
        sqlserver_conn.commit()
        postgres_cursor.close()
        postgres_conn.close()
        sqlserver_cursor.close()
        sqlserver_conn.close()

        print("\n=== FIN DE LA SYNCHRONISATION BATISIMPLY → BATIGEST ===")

        # Préparation du message final
        message = "✅ Synchronisation Batisimply → Batigest terminée :\n"
        message += f"- {updated_batisimply} chantiers mis à jour depuis Batisimply vers PostgreSQL\n"
        message += f"- {updated_to_batigest} chantiers synchronisés de PostgreSQL vers Batigest"

        return True, message

    except Exception as e:
        print(f"\n❌ Erreur lors de la synchronisation : {e}")
        return False, f"❌ Erreur lors de la synchronisation : {e}"

# ============================================================================
# INITIALISATION DE LA BASE DE DONNÉES
# ============================================================================

def init_postgres_table():
    """
    Initialise la table PostgreSQL avec les colonnes nécessaires pour le suivi des modifications.
    
    Cette fonction :
    1. Vérifie si les colonnes de dates de modification existent
    2. Les ajoute si elles n'existent pas
    3. Met à jour les dates existantes si nécessaire
    """
    try:
        # Connexion à PostgreSQL
        creds = load_credentials()
        if not creds or "postgres" not in creds:
            print("❌ Informations PostgreSQL manquantes")
            return False

        pg = creds["postgres"]
        postgres_conn = connect_to_postgres(
            pg["host"], pg["user"], pg["password"], pg["database"], pg.get("port", "5432")
        )
        if not postgres_conn:
            print("❌ Connexion à PostgreSQL échouée")
            return False

        postgres_cursor = postgres_conn.cursor()

        # Vérification de l'existence des colonnes
        postgres_cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'batigest_chantiers'
        """)
        existing_columns = [row[0] for row in postgres_cursor.fetchall()]

        # Ajout des colonnes si elles n'existent pas
        if 'last_modified_batisimply' not in existing_columns:
            postgres_cursor.execute("""
                ALTER TABLE batigest_chantiers 
                ADD COLUMN last_modified_batisimply TIMESTAMP WITH TIME ZONE
            """)
            print("✅ Colonne last_modified_batisimply ajoutée")

        if 'last_modified_batigest' not in existing_columns:
            postgres_cursor.execute("""
                ALTER TABLE batigest_chantiers 
                ADD COLUMN last_modified_batigest TIMESTAMP WITH TIME ZONE
            """)
            print("✅ Colonne last_modified_batigest ajoutée")

        # Validation des modifications
        postgres_conn.commit()
        postgres_cursor.close()
        postgres_conn.close()

        return True

    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation de la table : {e}")
        return False

# ============================================================================
    