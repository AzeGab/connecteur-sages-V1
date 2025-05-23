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
                ON CONFLICT (code) DO NOTHING
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
    4. Les envoie à l'API BatiSimply
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

        # Envoi à l'API et mise à jour du statut
        response = requests.post(API_URL, headers=headers, data=json.dumps(data))
        if response.status_code == 201:
            print(f"✅ Projet '{code}' envoyé avec succès")
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