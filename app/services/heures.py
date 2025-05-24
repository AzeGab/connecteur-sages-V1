# app/services/heures_service.py
# Module de gestion du transfert des heures
# Ce fichier contient les fonctions nécessaires pour transférer les données
# des heures depuis SQL Server vers PostgreSQL et BatiSimply

import psycopg2
from app.services.connex import connect_to_sqlserver, connect_to_postgres, load_credentials, recup_batisimply_token
import requests
import json
from datetime import date, datetime, timedelta

# ============================================================================
# TRANSFERT VERS POSTGRESQL
# ============================================================================

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
                    total_heure, panier, trajet, sync
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id_heure) DO NOTHING
            """, (
                heure_id, date_debut, date_fin, user_id,
                id_projet, status,
                total_heure, panier, trajet, False
            ))

        postgres_conn.commit()
        postgres_cursor.close()
        postgres_conn.close()

        print("✅ Transfert terminé avec succès.")
        return True

    except Exception as e:
        print(f"❌ Exception lors du transfert : {e}")
        return False


def transfer_heures_to_sqlserver():
    try:
        creds = load_credentials()
        if not creds or "sqlserver" not in creds or "postgres" not in creds:
            print("❌ Informations de connexion manquantes")
            return False

        sql = creds["sqlserver"]
        pg = creds["postgres"]

        sqlserver_conn = connect_to_sqlserver(
            sql["server"], sql["user"], sql["password"], sql["database"]
        )
        postgres_conn = connect_to_postgres(
            pg["host"], pg["user"], pg["password"], pg["database"], pg.get("port", "5432")
        )

        if not sqlserver_conn or not postgres_conn:
            print("❌ Connexions aux bases échouées")
            return False

        sqlserver_cursor = sqlserver_conn.cursor()
        postgres_cursor = postgres_conn.cursor()

        print("✅ Connexion SQL Server réussie")
        print("✅ Connexion PostgreSQL réussie")

        postgres_cursor.execute("""
            SELECT id_heure, date_debut, id_utilisateur, code_projet, total_heure, panier, trajet
            FROM batigest_heures
            WHERE status_management = 'VALIDATED' AND NOT sync
        """)
        heures = postgres_cursor.fetchall()
        print(f"📦 {len(heures)} heure(s) à traiter...")

        transferred_ids = []

        for h in heures:
            id_heure, date_debut, id_utilisateur, code_projet, total_heure, panier, trajet = h

            sqlserver_cursor.execute("SELECT Code FROM Salarie WHERE CODEBS = ?", (id_utilisateur,))
            columns = [column[0] for column in sqlserver_cursor.description]
            print("📋 Colonnes disponibles dans 'Salarie' :", columns)
            result = sqlserver_cursor.fetchone()
            if not result:
                print(f"⚠️ Utilisateur {id_utilisateur} non trouvé dans SQL Server.")
                continue

            code_salarie = result[0]  # ici on prend la colonne 'Code'
            code_chantier = code_projet
            nb_h0 = (total_heure / 60)
            nb_h3 = 1 if trajet else 0
            nb_h4 = 1 if panier else 0

            print("🟢 Insertion :", code_chantier, code_salarie, date_debut, nb_h0, nb_h3, nb_h4)
            sqlserver_cursor.execute("""
                INSERT INTO SuiviMO
                ([CodeChantier], [CodeSalarie], [Date], [NbH0], [NbH3], [NbH4])
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                code_chantier, code_salarie, date_debut,
                nb_h0, nb_h3, nb_h4
            ))

            transferred_ids.append(id_heure)

        sqlserver_conn.commit()

        if transferred_ids:
            postgres_cursor.execute(
                "UPDATE batigest_heures SET sync = TRUE WHERE id_heure = ANY(%s)",
                (transferred_ids,)
            )
            postgres_conn.commit()

        sqlserver_cursor.close()
        postgres_cursor.close()
        sqlserver_conn.close()
        postgres_conn.close()

        print(f"✅ {len(transferred_ids)} heure(s) transférée(s) avec succès")
        return True

    except Exception as e:
        print(f"❌ Erreur lors du transfert : {e}")
        return False

