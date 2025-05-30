# app/services/chantier_service.py
# Module de gestion du transfert des chantiers
# Ce fichier contient les fonctions nécessaires pour transférer les données
# des chantiers depuis SQL Server vers PostgreSQL

import psycopg2
from app.services.connex import connect_to_sqlserver, connect_to_postgres, load_credentials, recup_batisimply_token, connexion
import requests
import json
from datetime import date
from app.services.heures import transfer_heures_to_postgres, transfer_heures_to_sqlserver
from app.services.devis import transfer_devis, transfer_devis_vers_batisimply

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

        # Établissement des connexions
        postgres_conn, sqlserver_conn = connexion()
        if not sqlserver_conn or not postgres_conn:
            return False, "❌ Connexion aux bases échouée"

        # Création des curseurs pour l'exécution des requêtes
        sqlserver_cursor = sqlserver_conn.cursor()
        postgres_cursor = postgres_conn.cursor()

        # Récupération des chantiers actifs depuis Batigest avec heures vendues
        sqlserver_cursor.execute("""
            SELECT 
                ChantierDef.Code,
                DateDebut,
                DateFin,
                NomClient,
                Libelle,
                AdrChantier,
                CPChantier,
                VilleChantier,
                SUM(Devis.TempsMO) AS TotalMo
            FROM dbo.ChantierDef
            JOIN Devis ON Devis.CodeClient = ChantierDef.CodeClient
            WHERE (ChantierDef.DateFin IS NULL OR ChantierDef.DateFin > GETDATE())
              AND Devis.Etat = 3
            GROUP BY ChantierDef.Code, DateDebut, DateFin, NomClient, Libelle, AdrChantier, CPChantier, VilleChantier
        """)
        
        batigest_chantiers = sqlserver_cursor.fetchall()
        print(f"📊 {len(batigest_chantiers)} chantiers récupérés depuis Batigest")

        # Insertion des chantiers dans PostgreSQL
        for row in batigest_chantiers:
            code, date_debut, date_fin, nom_client, description, adr_chantier, cp_chantier, ville_chantier, total_mo = row
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
                sync = False
                """,
                (code, date_debut, date_fin, nom_client, description, adr_chantier, cp_chantier, ville_chantier, total_mo)
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
            "hoursSold": total_mo if total_mo is not None else 0,
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
    Synchronise les données de Batigest vers Batisimply via PostgreSQL.
    - Étape 1 : Récupère les données depuis Batigest (SQL Server) vers PostgreSQL.
    - Étape 2 : Transfère les heures de Batigest vers PostgreSQL.
    - Étape 3 : Transfère les chantiers depuis PostgreSQL vers BatiSimply.
    
    Returns:
        tuple: (bool, str)
    """
    try:
        print("\n=== DÉBUT DE LA SYNCHRONISATION BATIGEST → BATISIMPLY ===")

        # 1. Récupération des credentials et du mode
        creds = load_credentials()
        if not creds:
            return False, "❌ Impossible de charger les credentials."

        mode = creds.get("mode", "chantier")
        print(f"\n🔁 Mode de synchronisation : {mode}")

        # 2. Transfert des données Batigest → PostgreSQL
        print("\n🔄 Transfert des données Batigest vers PostgreSQL...")
        if mode == "devis":
            success, message = transfer_devis()
        else:
            success, message = transfer_chantiers()

        if not success:
            return False, f"❌ Échec du transfert SQL Server → PostgreSQL : {message}"
        print(f"✅ {message}")

        print("\n🔄 Transfert des chantiers PostgreSQL → Batisimply...")
        if mode == "devis":
            success = transfer_devis_vers_batisimply()
        else:
            success = transfer_chantiers_vers_batisimply()

        if not success:
            return False, f"❌ Échec du transfert SQL Server → PostgreSQL : {message}"
        print(f"✅ {message}")

        print("\n=== SYNCHRONISATION TERMINÉE AVEC SUCCÈS ===")
        return True, "✅ Synchronisation complète Batigest → Batisimply réussie."

    except Exception as e:
        print(f"\n❌ Erreur inattendue : {e}")
        return False, f"❌ Erreur lors de la synchronisation : {e}"


# ============================================================================
# SYNCHRONISATION DE BATISIMPLY VERS BATIGEST
# ============================================================================

def sync_batisimply_to_batigest():
    """
    Synchronise les heures de Batisimply vers Batigest via PostgreSQL.
    
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

        postgres_conn, sqlserver_conn = connexion()

        print("✅ Connexions aux bases de données établies")

        # 1. Synchronisation Batisimply → PostgreSQL
        print("\n🔄 Synchronisation Batisimply → PostgreSQL")
        
        # Récupération des heures depuis Batisimply et envoi vers PostgreSQL
    
        transfer_heures_to_postgres()
        update_code_projet_chantiers()
        # 2. Synchronisation PostgreSQL → Batigest
        transfer_heures_to_sqlserver()

        # Fermeture des connexions
        postgres_conn.close()
        sqlserver_conn.close()

        print("\n=== FIN DE LA SYNCHRONISATION BATISIMPLY → BATIGEST ===")
        return True, "✅ Synchronisation complète Batisimply → Batigest réussie."

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
        if 'sync' not in existing_columns:
            postgres_cursor.execute("""
                ALTER TABLE batigest_chantiers 
                ADD COLUMN sync BOOLEAN
            """)
            print("✅ Colonne sync ajoutée")

        # Validation des modifications
        postgres_conn.commit()
        postgres_cursor.close()
        postgres_conn.close()

        return True

    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation de la table : {e}")
        return False

# ============================================================================




    