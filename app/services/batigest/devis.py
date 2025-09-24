# app/services/batigest/devis.py
# Module de gestion du transfert des devis Batigest
# Ce fichier contient les fonctions nécessaires pour transférer les devis
# entre SQL Server, PostgreSQL et BatiSimply

import psycopg2
from app.services.connex import connect_to_sqlserver, connect_to_postgres, load_credentials, recup_batisimply_token
import requests
import json

# ============================================================================
# TRANSFERT SQLSERVER VERS POSTGRESQL (DEVIS)
# ============================================================================

def transfer_devis():
    """
    Transfère les données des devis depuis SQL Server vers PostgreSQL.
    
    Cette fonction :
    1. Vérifie les identifiants de connexion
    2. Établit les connexions aux deux bases de données
    3. Récupère les devis depuis SQL Server
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
        postgres_conn = connect_to_postgres(
            creds["postgres"]["host"],
            creds["postgres"]["user"],
            creds["postgres"]["password"],
            creds["postgres"]["database"],
            creds["postgres"].get("port", "5432")
        )
        
        sqlserver_conn = connect_to_sqlserver(
            creds["sqlserver"]["host"],
            creds["sqlserver"]["user"],
            creds["sqlserver"]["password"],
            creds["sqlserver"]["database"],
            creds["sqlserver"].get("port", "1433")
        )
        
        if not sqlserver_conn or not postgres_conn:
            return False, "❌ Connexion aux bases échouée"

        # Création des curseurs pour l'exécution des requêtes
        sqlserver_cursor = sqlserver_conn.cursor()
        postgres_cursor = postgres_conn.cursor()

        # Récupération des devis depuis Batigest
        sqlserver_cursor.execute("""
            SELECT 
                Devis.Code,
                Devis.DateDevis,
                Devis.DateFin,
                Client.NomClient,
                Devis.Libelle,
                Devis.AdrChantier,
                Devis.CPChantier,
                Devis.VilleChantier,
                Devis.TempsMO,
                Devis.Etat
            FROM dbo.Devis
            JOIN Client ON Client.Code = Devis.CodeClient
            WHERE Devis.Etat = 3
        """)
        
        batigest_devis = sqlserver_cursor.fetchall()
        print(f"📊 {len(batigest_devis)} devis récupérés depuis Batigest")

        # Insertion des devis dans PostgreSQL
        for row in batigest_devis:
            code, date_devis, date_fin, nom_client, libelle, adr_chantier, cp_chantier, ville_chantier, temps_mo, etat = row
            # Utilisation de ON CONFLICT pour éviter les doublons
            postgres_cursor.execute(
                """
                INSERT INTO batigest_devis 
                (code, date_devis, date_fin, nom_client, libelle, adr_chantier, cp_chantier, ville_chantier, temps_mo, etat)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (code) DO UPDATE SET 
                date_devis = EXCLUDED.date_devis,
                date_fin = EXCLUDED.date_fin,
                nom_client = EXCLUDED.nom_client,
                libelle = EXCLUDED.libelle,
                adr_chantier = EXCLUDED.adr_chantier,
                cp_chantier = EXCLUDED.cp_chantier,
                ville_chantier = EXCLUDED.ville_chantier,
                temps_mo = EXCLUDED.temps_mo,
                etat = EXCLUDED.etat,
                sync = False
                """,
                (code, date_devis, date_fin, nom_client, libelle, adr_chantier, cp_chantier, ville_chantier, temps_mo, etat)
            )

        # Validation des modifications dans PostgreSQL
        postgres_conn.commit()

        # Fermeture propre des connexions
        sqlserver_cursor.close()
        postgres_cursor.close()
        sqlserver_conn.close()
        postgres_conn.close()

        return True, "✅ Transfert des devis terminé avec succès"

    except Exception as e:
        # En cas d'erreur, on retourne le message d'erreur
        return False, f"❌ Erreur lors du transfert des devis : {e}"

# ============================================================================
# TRANSFERT POSTGRESQL VERS BATISIMPLY (DEVIS)
# ============================================================================

def transfer_devis_vers_batisimply():
    """
    Transfère les devis depuis PostgreSQL vers BatiSimply.
    
    Cette fonction :
    1. Récupère le token d'authentification
    2. Vérifie les identifiants PostgreSQL
    3. Récupère les devis non synchronisés
    4. Les envoie à l'API BatiSimply (POST pour nouveaux, PUT pour existants)
    5. Met à jour le statut de synchronisation
    
    Returns:
        bool: True si au moins un devis a été transféré avec succès, False sinon
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

    # Récupération des devis non synchronisés
    postgres_cursor = postgres_conn.cursor()
    postgres_cursor.execute("""
        SELECT code, date_devis, date_fin, nom_client, libelle, adr_chantier, cp_chantier, ville_chantier, temps_mo, etat
        FROM batigest_devis
        WHERE sync = false
    """)

    rows = postgres_cursor.fetchall()
    success = False

    # Récupération des projets existants dans BatiSimply
    existing_projects = {}
    response = requests.get(API_URL, headers=headers)
    if response.status_code == 200:
        projects = response.json().get("elements", [])
        for project in projects:
            existing_projects[project.get('projectCode')] = project.get('id')

    # Traitement de chaque devis
    for row in rows:
        code, date_devis, date_fin, nom_client, libelle, adr, cp, ville, temps_mo, etat = row

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
            "hoursSold": temps_mo if temps_mo is not None else 0,
            "projectCode": code,
            "comment": libelle,
            "projectName": nom_client,
            "customerName": nom_client,
            "projectManager": "DEFINIR",
            "startEstimated": date_devis.strftime("%Y-%m-%d") if date_devis else None,
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
            print(f"🔄 Mise à jour du devis existant '{code}' (ID: {data['id']})")
        else:
            method = "POST"
            url = API_URL
            print(f"➕ Création du nouveau devis '{code}'")

        # Envoi à l'API et mise à jour du statut
        response = requests.request(method, url, headers=headers, data=json.dumps(data))
        if response.status_code in [200, 201]:
            print(f"✅ Devis '{code}' traité avec succès")
            postgres_cursor.execute(
                "UPDATE batigest_devis SET sync = true, sync_date = NOW() WHERE code = %s", (code,))
            postgres_conn.commit()
            success = True
        else:
            print(f"❌ Erreur pour le devis '{code}' : {response.status_code} → {response.text}")

    # Nettoyage
    postgres_cursor.close()
    postgres_conn.close()

    return success
