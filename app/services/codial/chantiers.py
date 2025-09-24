# app/services/codial/chantiers.py
# Module de gestion du transfert des chantiers Codial
# Ce fichier contient les fonctions nécessaires pour transférer les chantiers
# entre HFSQL (Codial), PostgreSQL et BatiSimply

import psycopg2
from app.services.connex import connect_to_hfsql, connect_to_postgres, load_credentials, recup_batisimply_token
import requests
import json

# ============================================================================
# TRANSFERT HFSQL VERS POSTGRESQL
# ============================================================================

def transfer_chantiers_codial():
    """
    Transfère les données des chantiers depuis HFSQL (Codial) vers PostgreSQL.
    
    Cette fonction :
    1. Vérifie les identifiants de connexion
    2. Établit les connexions aux deux bases de données
    3. Récupère les chantiers depuis HFSQL
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
        if not creds or "hfsql" not in creds or "postgres" not in creds:
            return False, "❌ Informations de connexion manquantes"

        # Établissement des connexions
        postgres_conn = connect_to_postgres(
            creds["postgres"]["host"],
            creds["postgres"]["user"],
            creds["postgres"]["password"],
            creds["postgres"]["database"],
            creds["postgres"].get("port", "5432")
        )
        
        hfsql_conn = connect_to_hfsql(
            creds["hfsql"]["host"],
            creds["hfsql"]["user"],
            creds["hfsql"].get("password", ""),
            creds["hfsql"]["database"],
            creds["hfsql"].get("port", "4900"),
            creds["hfsql"].get("dsn", "")
        )
        
        if not hfsql_conn or not postgres_conn:
            return False, "❌ Connexion aux bases échouée"

        # Création des curseurs pour l'exécution des requêtes
        hfsql_cursor = hfsql_conn.cursor()
        postgres_cursor = postgres_conn.cursor()

        # Récupération des chantiers actifs depuis Codial
        # TODO: Adapter la requête selon la structure de la base Codial
        hfsql_cursor.execute("""
            SELECT 
                Code,
                DateDebut,
                DateFin,
                NomClient,
                Libelle,
                AdrChantier,
                CPChantier,
                VilleChantier,
                TotalMO
            FROM ChantierDef
            WHERE (DateFin IS NULL OR DateFin > NOW())
        """)
        
        codial_chantiers = hfsql_cursor.fetchall()
        print(f"📊 {len(codial_chantiers)} chantiers récupérés depuis Codial")

        # Insertion des chantiers dans PostgreSQL
        for row in codial_chantiers:
            code, date_debut, date_fin, nom_client, description, adr_chantier, cp_chantier, ville_chantier, total_mo = row
            # Utilisation de ON CONFLICT pour éviter les doublons
            postgres_cursor.execute(
                """
                INSERT INTO codial_chantiers 
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
        hfsql_cursor.close()
        postgres_cursor.close()
        hfsql_conn.close()
        postgres_conn.close()

        return True, "✅ Transfert Codial terminé avec succès"

    except Exception as e:
        # En cas d'erreur, on retourne le message d'erreur
        return False, f"❌ Erreur lors du transfert Codial : {e}"

# ============================================================================
# TRANSFERT POSTGRESQL VERS BATISIMPLY (CODIAL)
# ============================================================================

def transfer_chantiers_codial_vers_batisimply():
    """
    Transfère les chantiers Codial depuis PostgreSQL vers BatiSimply.
    
    Cette fonction :
    1. Récupère le token d'authentification
    2. Vérifie les identifiants PostgreSQL
    3. Récupère les chantiers Codial non synchronisés
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

    # Récupération des chantiers Codial non synchronisés
    postgres_cursor = postgres_conn.cursor()
    postgres_cursor.execute("""
        SELECT code, date_debut, date_fin, nom_client, description, adr_chantier, cp_chantier, ville_chantier, total_mo
        FROM codial_chantiers
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
            print(f"🔄 Mise à jour du projet Codial existant '{code}' (ID: {data['id']})")
        else:
            method = "POST"
            url = API_URL
            print(f"➕ Création du nouveau projet Codial '{code}'")

        # Envoi à l'API et mise à jour du statut
        response = requests.request(method, url, headers=headers, data=json.dumps(data))
        if response.status_code in [200, 201]:
            print(f"✅ Projet Codial '{code}' traité avec succès")
            postgres_cursor.execute(
                "UPDATE codial_chantiers SET sync = true, sync_date = NOW() WHERE code = %s", (code,))
            postgres_conn.commit()
            success = True
        else:
            print(f"❌ Erreur pour le projet Codial '{code}' : {response.status_code} → {response.text}")

    # Nettoyage
    postgres_cursor.close()
    postgres_conn.close()

    return success
