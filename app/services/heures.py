# app/services/heures_service.py
# Module de gestion du transfert des heures
# Ce fichier contient les fonctions nécessaires pour transférer les données
# des heures depuis SQL Server vers PostgreSQL et BatiSimply

import psycopg2
from app.services.connex import connect_to_sqlserver, connect_to_postgres, load_credentials, recup_batisimply_token
import requests
import json
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

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

        # Fenêtre temporelle: X derniers jours jusqu'à aujourd'hui (configurable)
        window_days = 180
        try:
            # facultatif: surcharge via credentials.json → { "heures_window_days": 180 }
            window_days = int(creds.get("heures_window_days", window_days))
        except Exception:
            pass

        now_utc = datetime.utcnow()
        start_utc = now_utc - timedelta(days=window_days)
        end_utc = now_utc

        start_date_str = start_utc.strftime("%Y-%m-%dT00:00:00Z")
        end_date_str = end_utc.strftime("%Y-%m-%dT23:59:59Z")
        print(f"🗓️ Fenêtre d'import des heures: {start_date_str} → {end_date_str}")

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
        # Fuseau horaire local (par défaut Europe/Paris)
        tz_name = creds.get("timezone", "Europe/Paris")
        local_tz = ZoneInfo(tz_name)
        utc_tz = ZoneInfo("UTC")
        for h in heures:
            heure_id = h["id"]
            start_iso = h["startDate"]
            end_iso = h["endDate"]
            # Normalisation timezone: API renvoie en UTC (Z). Convertir en heure locale naive.
            try:
                if isinstance(start_iso, str) and start_iso.endswith("Z"):
                    start_iso = start_iso.replace("Z", "+00:00")
                if isinstance(end_iso, str) and end_iso.endswith("Z"):
                    end_iso = end_iso.replace("Z", "+00:00")
                start_dt_aware = datetime.fromisoformat(start_iso)
                end_dt_aware = datetime.fromisoformat(end_iso)
                if start_dt_aware.tzinfo is None:
                    start_dt_aware = start_dt_aware.replace(tzinfo=utc_tz)
                if end_dt_aware.tzinfo is None:
                    end_dt_aware = end_dt_aware.replace(tzinfo=utc_tz)
                date_debut = start_dt_aware.astimezone(local_tz).replace(tzinfo=None)
                date_fin = end_dt_aware.astimezone(local_tz).replace(tzinfo=None)
                # Normaliser à la minute (éviter secondes 01/57 qui varient côté API/UI)
                date_debut = date_debut.replace(second=0, microsecond=0)
                date_fin = date_fin.replace(second=0, microsecond=0)
            except Exception:
                # En cas de format inattendu, fallback sur la valeur brute
                date_debut = h["startDate"]
                date_fin = h["endDate"]
            user_id = h["user"]["id"]
            id_projet = h.get("project", {}).get("id")
            status = h["managementStatus"]
            total_heure = h["totalTimeMinutes"]
            panier = h.get("hasPackedLunch", False)
            trajet = h.get("hasHomeToWorkJourney", False)

            # Upsert: met à jour si l'heure existe déjà et remet sync=false si modification
            postgres_cursor.execute("""
                INSERT INTO batigest_heures(
                    id_heure, date_debut, date_fin, id_utilisateur,
                    id_projet, status_management,
                    total_heure, panier, trajet, sync
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id_heure) DO UPDATE SET
                    date_debut = EXCLUDED.date_debut,
                    date_fin = EXCLUDED.date_fin,
                    id_utilisateur = EXCLUDED.id_utilisateur,
                    id_projet = EXCLUDED.id_projet,
                    status_management = EXCLUDED.status_management,
                    total_heure = EXCLUDED.total_heure,
                    panier = EXCLUDED.panier,
                    trajet = EXCLUDED.trajet,
                    sync = CASE WHEN (
                        batigest_heures.date_debut IS DISTINCT FROM EXCLUDED.date_debut OR
                        batigest_heures.date_fin IS DISTINCT FROM EXCLUDED.date_fin OR
                        batigest_heures.id_utilisateur IS DISTINCT FROM EXCLUDED.id_utilisateur OR
                        batigest_heures.id_projet IS DISTINCT FROM EXCLUDED.id_projet OR
                        batigest_heures.status_management IS DISTINCT FROM EXCLUDED.status_management OR
                        batigest_heures.total_heure IS DISTINCT FROM EXCLUDED.total_heure OR
                        batigest_heures.panier IS DISTINCT FROM EXCLUDED.panier OR
                        batigest_heures.trajet IS DISTINCT FROM EXCLUDED.trajet
                    ) THEN FALSE ELSE batigest_heures.sync END
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

        # Assurer l'existence de la table de mapping côté PostgreSQL
        postgres_cursor.execute("""
            CREATE TABLE IF NOT EXISTS batigest_heures_map (
                id_heure VARCHAR PRIMARY KEY,
                code_chantier VARCHAR NOT NULL,
                code_salarie VARCHAR NOT NULL,
                date_sqlserver TIMESTAMP NOT NULL
            )
        """)

        postgres_cursor.execute("""
            SELECT id_heure, date_debut, id_utilisateur, code_projet, total_heure, panier, trajet
            FROM batigest_heures
            WHERE status_management = 'VALIDATED' AND NOT sync AND code_projet IS NOT NULL
        """)
        heures = postgres_cursor.fetchall()
        print(f"📦 {len(heures)} heure(s) à traiter...")

        transferred_ids = []

        for h in heures:
            id_heure, date_debut, id_utilisateur, code_projet, total_heure, panier, trajet = h

            # Vérification de la structure de la table Salarie
            sqlserver_cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'Salarie'
            """)
            columns_info = sqlserver_cursor.fetchall()
            print("\n📋 Structure de la table Salarie :")
            for col in columns_info:
                print(f"  - {col[0]}: {col[1]}")

            # Recherche de l'utilisateur avec plus de détails
            print(f"\n🔍 Recherche de l'utilisateur {id_utilisateur} dans Salarie...")
            sqlserver_cursor.execute("""
                SELECT TOP 5 * 
                FROM Salarie 
                WHERE codebs = ?
            """, (id_utilisateur,))
            
            # Affichage des résultats de la recherche
            results = sqlserver_cursor.fetchall()
            if results:
                print("✅ Utilisateurs trouvés :")
                for row in results:
                    print(f"  - {row}")
            else:
                print(f"⚠️ Aucun utilisateur trouvé avec l'ID {id_utilisateur}")
                continue

            code_salarie = results[0][0]  # On prend le Code du premier résultat
            if not code_projet:
                print(f"⏭️ id_heure {id_heure} ignorée: code_projet manquant")
                continue
            code_chantier = str(code_projet)
            nb_h0 = (total_heure / 60)
            nb_h3 = 1 if trajet else 0
            nb_h4 = 1 if panier else 0

            # Lire mapping existant pour cet id_heure
            postgres_cursor.execute(
                "SELECT code_chantier, code_salarie, date_sqlserver FROM batigest_heures_map WHERE id_heure = %s",
                (id_heure,)
            )
            map_row = postgres_cursor.fetchone()

            # Vérifier une correspondance exacte sur la nouvelle clé
            sqlserver_cursor.execute(
                """
                SELECT [NbH0], [NbH3], [NbH4]
                FROM SuiviMO
                WHERE [CodeChantier] = ? AND [CodeSalarie] = ? AND [Date] = ?
                """,
                (code_chantier, code_salarie, date_debut)
            )
            new_exists = sqlserver_cursor.fetchone()

            if map_row:
                old_code_chantier, old_code_salarie, old_date = map_row
                keys_changed = (
                    str(old_code_chantier) != str(code_chantier)
                    or str(old_code_salarie) != str(code_salarie)
                    or old_date != date_debut
                )

                if keys_changed:
                    print("🛈 Clé modifiée pour id_heure", id_heure,
                          f": ({old_code_chantier}, {old_code_salarie}, {old_date}) → ({code_chantier}, {code_salarie}, {date_debut})")

                    # Tenter une mise à jour de l'ancienne ligne vers la nouvelle clé et valeurs
                    sqlserver_cursor.execute(
                        """
                        UPDATE SuiviMO
                        SET [CodeChantier] = ?, [CodeSalarie] = ?, [Date] = ?, [NbH0] = ?, [NbH3] = ?, [NbH4] = ?
                        WHERE [CodeChantier] = ? AND [CodeSalarie] = ? AND [Date] = ?
                        """,
                        (
                            code_chantier, code_salarie, date_debut, nb_h0, nb_h3, nb_h4,
                            old_code_chantier, old_code_salarie, old_date
                        )
                    )

                    if sqlserver_cursor.rowcount == 0:
                        # Si l'ancienne clé n'existe pas (suppression externe ?), fallback: upsert sur la nouvelle clé
                        if new_exists:
                            existing_h0, existing_h3, existing_h4 = new_exists
                            if existing_h0 != nb_h0 or existing_h3 != nb_h3 or existing_h4 != nb_h4:
                                sqlserver_cursor.execute(
                                    """
                                    UPDATE SuiviMO
                                    SET [NbH0] = ?, [NbH3] = ?, [NbH4] = ?
                                    WHERE [CodeChantier] = ? AND [CodeSalarie] = ? AND [Date] = ?
                                    """,
                                    (nb_h0, nb_h3, nb_h4, code_chantier, code_salarie, date_debut)
                                )
                        else:
                            sqlserver_cursor.execute(
                                """
                                INSERT INTO SuiviMO([CodeChantier], [CodeSalarie], [Date], [NbH0], [NbH3], [NbH4])
                                VALUES (?, ?, ?, ?, ?, ?)
                                """,
                                (code_chantier, code_salarie, date_debut, nb_h0, nb_h3, nb_h4)
                            )

                else:
                    # Clé inchangée: upsert des valeurs sur la nouvelle clé
                    if new_exists:
                        existing_h0, existing_h3, existing_h4 = new_exists
                        if existing_h0 != nb_h0 or existing_h3 != nb_h3 or existing_h4 != nb_h4:
                            sqlserver_cursor.execute(
                                """
                                UPDATE SuiviMO
                                SET [NbH0] = ?, [NbH3] = ?, [NbH4] = ?
                                WHERE [CodeChantier] = ? AND [CodeSalarie] = ? AND [Date] = ?
                                """,
                                (nb_h0, nb_h3, nb_h4, code_chantier, code_salarie, date_debut)
                            )
                    else:
                        sqlserver_cursor.execute(
                            """
                            INSERT INTO SuiviMO([CodeChantier], [CodeSalarie], [Date], [NbH0], [NbH3], [NbH4])
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (code_chantier, code_salarie, date_debut, nb_h0, nb_h3, nb_h4)
                        )

                # Upsert mapping vers la nouvelle clé
                postgres_cursor.execute(
                    """
                    INSERT INTO batigest_heures_map(id_heure, code_chantier, code_salarie, date_sqlserver)
                    VALUES(%s, %s, %s, %s)
                    ON CONFLICT (id_heure)
                    DO UPDATE SET code_chantier=EXCLUDED.code_chantier,
                                  code_salarie=EXCLUDED.code_salarie,
                                  date_sqlserver=EXCLUDED.date_sqlserver
                    """,
                    (id_heure, code_chantier, str(code_salarie), date_debut)
                )
                transferred_ids.append(id_heure)
                continue

            # Pas de mapping existant (nouvelle heure) → upsert sur la nouvelle clé
            if new_exists:
                existing_h0, existing_h3, existing_h4 = new_exists
                if existing_h0 != nb_h0 or existing_h3 != nb_h3 or existing_h4 != nb_h4:
                    sqlserver_cursor.execute(
                        """
                        UPDATE SuiviMO
                        SET [NbH0] = ?, [NbH3] = ?, [NbH4] = ?
                        WHERE [CodeChantier] = ? AND [CodeSalarie] = ? AND [Date] = ?
                        """,
                        (nb_h0, nb_h3, nb_h4, code_chantier, code_salarie, date_debut)
                    )
            else:
                sqlserver_cursor.execute(
                    """
                    INSERT INTO SuiviMO([CodeChantier], [CodeSalarie], [Date], [NbH0], [NbH3], [NbH4])
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (code_chantier, code_salarie, date_debut, nb_h0, nb_h3, nb_h4)
                )

            # Enregistrer le mapping pour cette nouvelle heure
            postgres_cursor.execute(
                """
                INSERT INTO batigest_heures_map(id_heure, code_chantier, code_salarie, date_sqlserver)
                VALUES(%s, %s, %s, %s)
                ON CONFLICT (id_heure)
                DO UPDATE SET code_chantier=EXCLUDED.code_chantier,
                              code_salarie=EXCLUDED.code_salarie,
                              date_sqlserver=EXCLUDED.date_sqlserver
                """,
                (id_heure, code_chantier, str(code_salarie), date_debut)
            )
            transferred_ids.append(id_heure)
            continue

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
        return len(transferred_ids)

    except Exception as e:
        print(f"❌ Erreur lors du transfert : {e}")
        return 0

