# app/services/chantier_service.py
# Module de gestion du transfert des chantiers
# Ce fichier contient les fonctions nécessaires pour transférer les données
# des chantiers depuis SQL Server vers PostgreSQL

import psycopg2
from app.services.connex import connect_to_sqlserver, connect_to_postgres, load_credentials, recup_batisimply_token

import requests
import json
from datetime import date, datetime, timedelta


def transfer_heures_to_postgres():
    """
    Transfère les heures depuis BatiSimply vers PostgreSQL pour une période
    allant d'aujourd'hui à +5 ans.
    
    Returns:
        bool: True si succès, False sinon.
    """
    try:
        token = recup_batisimply_token()
        if not token:
            print("❌ Token BatiSimply manquant.")
            return False

        creds = load_credentials()
        if not creds or "postgres" not in creds:
            print("❌ Informations Postgres manquantes.")
            return False

        pg = creds["postgres"]
        postgres_conn = connect_to_postgres(
            pg["host"], pg["user"], pg["password"], pg["database"], pg.get("port", "5432")
        )
        if not postgres_conn:
            print("❌ Connexion à la base Postgres échouée.")
            return False

        postgres_cursor = postgres_conn.cursor()

        # Dates au format UTC avec "Z"
        today = datetime.utcnow()
        end_date = today + timedelta(days=5 * 365)  # ~ 5 ans

        start_date_str = today.strftime("%Y-%m-%dT00:00:00Z")
        end_date_str = end_date.strftime("%Y-%m-%dT00:00:00Z")

        API_URL = "https://api.staging.batisimply.fr/api/timeSlotManagement/allUsers"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        params = {
            "startDate": start_date_str,
            "endDate": end_date_str
        }

        response = requests.get(API_URL, headers=headers, params=params)
        if response.status_code != 200:
            print(f"❌ Erreur API : {response.status_code} → {response.text}")
            return False

        heures = response.json()
        for h in heures:
            heure_id = h["id"]
            date_debut = h["startDate"]
            date_fin = h["endDate"]
            user_id = h["user"]["id"]
            id_projet = h.get("project", {}).get("id")
            status = h["managementStatus"]
            total_heure = h["totalTimeMinutes"]
            panier = h.get("hasPackedLunch", False)
            trajet = h.get("hasHomeToWorkJourney", False)

            postgres_cursor.execute("""
                INSERT INTO batigest_heures(
                    id_heure, date_debut, date_fin, id_utilisateur,
                    id_projet, status_management,
                    total_heure, panier, trajet
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id_heure) DO NOTHING
            """, (
                heure_id, date_debut, date_fin, user_id,
                id_projet, status,
                total_heure, panier, trajet
            ))

        postgres_conn.commit()
        postgres_cursor.close()
        postgres_conn.close()

        print("✅ Transfert terminé avec succès.")
        return True

    except Exception as e:
        print(f"❌ Exception lors du transfert : {e}")
        return False
