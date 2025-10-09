# app/services/batigest/batisimply_to_sqlserver.py
# Module de gestion du flux BatiSimply -> PostgreSQL -> SQL Server (Batigest)
# Ce fichier contient les fonctions pour transférer les données depuis BatiSimply vers Batigest (SQL Server)

import psycopg2
import requests
import json
from datetime import date, datetime, timedelta
from app.services.connex import connect_to_sqlserver, connect_to_postgres, load_credentials, recup_batisimply_token

# ============================================================================
# TRANSFERT DES CHANTIERS BATISIMPLY -> POSTGRESQL -> SQL SERVER
# ============================================================================

def transfer_chantiers_batisimply_to_postgres():
    """
    Transfère les chantiers depuis BatiSimply vers PostgreSQL.
    """
    try:
        # Vérification des identifiants
        creds = load_credentials()
        if not creds or "postgres" not in creds:
            return False, "❌ Informations de connexion PostgreSQL manquantes"

        # Récupération du token BatiSimply
        token = recup_batisimply_token()
        if not token:
            return False, "❌ Impossible de récupérer le token BatiSimply"

        # Connexion PostgreSQL
        postgres_conn = connect_to_postgres(
            creds["postgres"]["host"],
            creds["postgres"]["user"],
            creds["postgres"]["password"],
            creds["postgres"]["database"],
            creds["postgres"].get("port", "5432")
        )
        if not postgres_conn:
            return False, "❌ Connexion PostgreSQL échouée"

        postgres_cursor = postgres_conn.cursor()

        # Récupération des chantiers depuis BatiSimply
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        response = requests.get(
            'https://api.staging.batisimply.fr/api/project',
            headers=headers,
            timeout=30
        )

        if response.status_code != 200:
            return False, f"❌ Erreur API BatiSimply : {response.status_code}"

        try:
            chantiers = response.json()
        except json.JSONDecodeError as e:
            return False, f"❌ Erreur de parsing JSON de l'API BatiSimply : {str(e)}. Réponse: {response.text[:200]}"

        # Vérifier que chantiers est une liste ou un dictionnaire
        if isinstance(chantiers, dict):
            # Si c'est un dictionnaire, vérifier s'il contient une liste de chantiers
            if 'content' in chantiers:
                chantiers = chantiers['content']
            elif 'data' in chantiers:
                chantiers = chantiers['data']
            elif 'items' in chantiers:
                chantiers = chantiers['items']
            else:
                # Si c'est un dictionnaire simple, le traiter comme un seul chantier
                chantiers = [chantiers]
        elif not isinstance(chantiers, list):
            return False, f"❌ Format de réponse inattendu de l'API BatiSimply. Attendu: liste ou dict, reçu: {type(chantiers)}"

        # Insertion dans PostgreSQL avec gestion des conflits
        for chantier in chantiers:
            # Vérifier que chantier est un dictionnaire
            if not isinstance(chantier, dict):
                print(f"⚠️ Chantier ignoré (format inattendu): {type(chantier)} - {chantier}")
                continue
            code = chantier.get('id')  # L'ID BatiSimply devient le code
            nom_client = chantier.get('name')
            date_debut = chantier.get('startDate')
            date_fin = chantier.get('endDate')
            description = chantier.get('status', '')  # Utiliser le statut comme description
            
            query_postgres = """
            INSERT INTO batigest_chantiers (code, date_debut, date_fin, nom_client, description, sync)
            VALUES (%s, %s, %s, %s, %s, FALSE)
            ON CONFLICT (code) DO UPDATE SET
                date_debut = EXCLUDED.date_debut,
                date_fin = EXCLUDED.date_fin,
                nom_client = EXCLUDED.nom_client,
                description = EXCLUDED.description,
                sync = FALSE
            """
            
            postgres_cursor.execute(query_postgres, (code, date_debut, date_fin, nom_client, description))

        postgres_conn.commit()
        postgres_cursor.close()
        postgres_conn.close()

        return True, f"✅ {len(chantiers)} chantier(s) transféré(s) depuis BatiSimply vers PostgreSQL"

    except Exception as e:
        return False, f"❌ Erreur lors du transfert BatiSimply -> PostgreSQL : {str(e)}"

def transfer_chantiers_postgres_to_sqlserver():
    """
    Transfère les chantiers depuis PostgreSQL vers SQL Server (Batigest).
    """
    try:
        # Vérification des identifiants
        creds = load_credentials()
        if not creds or "sqlserver" not in creds or "postgres" not in creds:
            return False, "❌ Informations de connexion manquantes"

        # Établissement des connexions
        sqlserver_conn = connect_to_sqlserver(
            creds["sqlserver"]["server"],
            creds["sqlserver"]["user"],
            creds["sqlserver"]["password"],
            creds["sqlserver"]["database"]
        )
        postgres_conn = connect_to_postgres(
            creds["postgres"]["host"],
            creds["postgres"]["user"],
            creds["postgres"]["password"],
            creds["postgres"]["database"],
            creds["postgres"].get("port", "5432")
        )
        
        if not sqlserver_conn or not postgres_conn:
            return False, "❌ Connexion aux bases échouée"

        # Création des curseurs
        sqlserver_cursor = sqlserver_conn.cursor()
        postgres_cursor = postgres_conn.cursor()

        # Vérifier la structure de la table ChantierDef pour adapter les limites
        try:
            sqlserver_cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'ChantierDef' AND TABLE_SCHEMA = 'dbo'
            """)
            columns_info = sqlserver_cursor.fetchall()
            print("📋 Structure de la table ChantierDef :")
            for col in columns_info:
                print(f"  - {col[0]}: {col[1]} (max: {col[2]})")
        except Exception as e:
            print(f"⚠️ Impossible de récupérer la structure de la table: {e}")

        # Récupération des chantiers non synchronisés
        query = "SELECT * FROM batigest_chantiers WHERE sync = FALSE"
        postgres_cursor.execute(query)
        chantiers = postgres_cursor.fetchall()

        # Insertion dans SQL Server
        for chantier in chantiers:
            # Structure: id, code, date_debut, date_fin, nom_client, description, adr_chantier, cp_chantier, ville_chantier, sync_date, sync, total_mo, last_modified_batisimply, last_modified_batigest
            id, code, date_debut, date_fin, nom_client, description, adr_chantier, cp_chantier, ville_chantier, sync_date, sync, total_mo, last_modified_batisimply, last_modified_batigest = chantier
            
            # Tronquer les chaînes selon les limites de la table SQL Server
            code_truncated = str(code)[:8] if code else ''  # Code: max 8 chars
            nom_client_truncated = str(nom_client)[:30] if nom_client else ''  # NomClient: max 30 chars
            # Pour Etat (1 char), on prend le premier caractère de la description ou un caractère par défaut
            description_truncated = str(description)[:1] if description else 'A'  # Etat: max 1 char, défaut 'A'
            
            # Gérer les valeurs NULL pour DateDebut et DateFin
            date_debut_safe = date_debut if date_debut else datetime.now().date()
            date_fin_safe = date_fin if date_fin else datetime.now().date()
            
            # Debug: afficher les longueurs des chaînes
            print(f"🔍 Debug chantier: code='{code_truncated}' (len={len(code_truncated)}), nom_client='{nom_client_truncated}' (len={len(nom_client_truncated)}), etat='{description_truncated}' (len={len(description_truncated)})")
            print(f"   Données originales: code='{code}', nom_client='{nom_client}', description='{description}'")
            
            # Ignorer les chantiers avec des données vides
            if not code_truncated or not nom_client_truncated:
                print(f"⚠️ Chantier ignoré (données vides): code='{code_truncated}', nom='{nom_client_truncated}'")
                continue
            
            # Vérifier si le chantier existe déjà dans SQL Server
            check_query = "SELECT COUNT(*) FROM dbo.ChantierDef WHERE Code = ?"
            sqlserver_cursor.execute(check_query, (code_truncated,))
            exists = sqlserver_cursor.fetchone()[0] > 0
            
            try:
                if exists:
                    # Mise à jour
                    update_query = """
                    UPDATE dbo.ChantierDef 
                    SET NomClient = ?, DateDebut = ?, DateFin = ?, Etat = ?
                    WHERE Code = ?
                    """
                    sqlserver_cursor.execute(update_query, (nom_client_truncated, date_debut_safe, date_fin_safe, description_truncated, code_truncated))
                else:
                    # Insertion
                    insert_query = """
                    INSERT INTO dbo.ChantierDef (Code, NomClient, DateDebut, DateFin, Etat)
                    VALUES (?, ?, ?, ?, ?)
                    """
                    sqlserver_cursor.execute(insert_query, (code_truncated, nom_client_truncated, date_debut_safe, date_fin_safe, description_truncated))
            except Exception as e:
                print(f"⚠️ Erreur lors de l'insertion/mise à jour du chantier {code_truncated}: {e}")
                print(f"   Données: code='{code_truncated}', nom='{nom_client_truncated}', desc='{description_truncated}'")
                continue
            
            # Marquer comme synchronisé dans PostgreSQL
            update_postgres = "UPDATE batigest_chantiers SET sync = TRUE WHERE code = %s"
            postgres_cursor.execute(update_postgres, (code,))

        sqlserver_conn.commit()
        postgres_conn.commit()
        
        # Fermeture des connexions
        sqlserver_cursor.close()
        postgres_cursor.close()
        sqlserver_conn.close()
        postgres_conn.close()

        return True, f"✅ {len(chantiers)} chantier(s) transféré(s) vers SQL Server"

    except Exception as e:
        return False, f"❌ Erreur lors du transfert PostgreSQL -> SQL Server : {str(e)}"

# ============================================================================
# TRANSFERT DES HEURES BATISIMPLY -> POSTGRESQL -> SQL SERVER
# ============================================================================

def transfer_heures_batisimply_to_postgres():
    """
    Transfère les heures depuis BatiSimply vers PostgreSQL.
    """
    try:
        # Vérification des identifiants
        creds = load_credentials()
        if not creds or "postgres" not in creds:
            return False, "❌ Informations de connexion PostgreSQL manquantes"

        # Récupération du token BatiSimply
        token = recup_batisimply_token()
        if not token:
            return False, "❌ Impossible de récupérer le token BatiSimply"

        # Connexion PostgreSQL
        postgres_conn = connect_to_postgres(
            creds["postgres"]["host"],
            creds["postgres"]["user"],
            creds["postgres"]["password"],
            creds["postgres"]["database"],
            creds["postgres"].get("port", "5432")
        )
        if not postgres_conn:
            return False, "❌ Connexion PostgreSQL échouée"

        postgres_cursor = postgres_conn.cursor()

        # Fenêtre temporelle configurable (par défaut 180 jours)
        window_days = 180
        try:
            window_days = int(creds.get("heures_window_days", window_days))
        except Exception:
            pass

        # Calcul des dates avec timezone UTC
        now_utc = datetime.utcnow()
        start_utc = now_utc - timedelta(days=window_days)
        end_utc = now_utc

        start_date_str = start_utc.strftime("%Y-%m-%dT00:00:00Z")
        end_date_str = end_utc.strftime("%Y-%m-%dT23:59:59Z")
        print(f"🗓️ Fenêtre d'import des heures: {start_date_str} → {end_date_str}")

        # Récupération des heures depuis BatiSimply
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        params = {
            "startDate": start_date_str,
            "endDate": end_date_str
        }
        
        response = requests.get(
            'https://api.staging.batisimply.fr/api/timeSlotManagement/allUsers',
            headers=headers,
            params=params,
            timeout=30
        )

        if response.status_code != 200:
            return False, f"❌ Erreur API BatiSimply : {response.status_code}. Réponse: {response.text[:200]}"

        try:
            heures = response.json()
        except json.JSONDecodeError as e:
            return False, f"❌ Erreur de parsing JSON de l'API BatiSimply : {str(e)}. Réponse: {response.text[:200]}"

        # Vérifier que heures est une liste ou un dictionnaire
        if isinstance(heures, dict):
            if 'content' in heures:
                heures = heures['content']
            elif 'data' in heures:
                heures = heures['data']
            elif 'items' in heures:
                heures = heures['items']
            else:
                heures = [heures]
        elif not isinstance(heures, list):
            return False, f"❌ Format de réponse inattendu de l'API BatiSimply. Attendu: liste ou dict, reçu: {type(heures)}"

        # Configuration du timezone
        tz_name = creds.get("timezone", "Europe/Paris")
        try:
            from zoneinfo import ZoneInfo
            local_tz = ZoneInfo(tz_name)
            utc_tz = ZoneInfo("UTC")
        except ImportError:
            # Fallback pour Python < 3.9
            import pytz
            local_tz = pytz.timezone(tz_name)
            utc_tz = pytz.UTC

        # Insertion dans PostgreSQL avec gestion des conflits
        for h in heures:
            # Vérifier que heure est un dictionnaire
            if not isinstance(h, dict):
                print(f"⚠️ Heure ignorée (format inattendu): {type(h)} - {h}")
                continue
                
            heure_id = h.get("id")
            start_iso = h.get("startDate")
            end_iso = h.get("endDate")
            
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
                date_debut = h.get("startDate")
                date_fin = h.get("endDate")
                
            user_id = h.get("user", {}).get("id")
            id_projet = h.get("project", {}).get("id")
            status = h.get("managementStatus")
            total_heure = h.get("totalTimeMinutes")
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

        return True, f"✅ {len(heures)} heure(s) transférée(s) depuis BatiSimply vers PostgreSQL"

    except Exception as e:
        return False, f"❌ Erreur lors du transfert BatiSimply -> PostgreSQL : {str(e)}"

def transfer_heures_postgres_to_sqlserver():
    """
    Transfère les heures depuis PostgreSQL vers SQL Server (Batigest).
    """
    try:
        # Vérification des identifiants
        creds = load_credentials()
        if not creds or "sqlserver" not in creds or "postgres" not in creds:
            return False, "❌ Informations de connexion manquantes"

        # Établissement des connexions
        sqlserver_conn = connect_to_sqlserver(
            creds["sqlserver"]["server"],
            creds["sqlserver"]["user"],
            creds["sqlserver"]["password"],
            creds["sqlserver"]["database"]
        )
        postgres_conn = connect_to_postgres(
            creds["postgres"]["host"],
            creds["postgres"]["user"],
            creds["postgres"]["password"],
            creds["postgres"]["database"],
            creds["postgres"].get("port", "5432")
        )
        
        if not sqlserver_conn or not postgres_conn:
            return False, "❌ Connexion aux bases échouée"

        # Création des curseurs
        sqlserver_cursor = sqlserver_conn.cursor()
        postgres_cursor = postgres_conn.cursor()

        # Assurer l'existence de la table de mapping côté PostgreSQL
        postgres_cursor.execute("""
            CREATE TABLE IF NOT EXISTS batigest_heures_map (
                id_heure VARCHAR PRIMARY KEY,
                code_chantier VARCHAR NOT NULL,
                code_salarie VARCHAR NOT NULL,
                date_sqlserver TIMESTAMP NOT NULL
            )
        """)

        # Récupération des heures non synchronisées avec code_projet
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
            nb_h0 = (total_heure / 60) if total_heure else 0
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
                    print("🔄 Clé modifiée pour id_heure", id_heure,
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

        return True, f"✅ {len(transferred_ids)} heure(s) transférée(s) vers SQL Server"

    except Exception as e:
        return False, f"❌ Erreur lors du transfert PostgreSQL -> SQL Server : {str(e)}"

def update_code_projet_chantiers():
    """
    Met à jour les codes projet des heures en utilisant la correspondance avec les chantiers.
    """
    try:
        creds = load_credentials()
        if not creds or "postgres" not in creds:
            return False, "❌ Informations de connexion PostgreSQL manquantes"

        postgres_conn = connect_to_postgres(
            creds["postgres"]["host"],
            creds["postgres"]["user"],
            creds["postgres"]["password"],
            creds["postgres"]["database"],
            creds["postgres"].get("port", "5432")
        )
        if not postgres_conn:
            return False, "❌ Connexion PostgreSQL échouée"

        postgres_cursor = postgres_conn.cursor()

        # Mettre à jour les codes projet des heures en utilisant la correspondance avec les chantiers
        postgres_cursor.execute("""
            UPDATE batigest_heures 
            SET code_projet = batigest_chantiers.code
            FROM batigest_chantiers 
            WHERE batigest_heures.id_projet::text = batigest_chantiers.code
            AND batigest_heures.code_projet IS NULL
        """)

        updated_count = postgres_cursor.rowcount
        postgres_conn.commit()
        postgres_cursor.close()
        postgres_conn.close()

        return True, f"✅ {updated_count} heure(s) mise(s) à jour avec le code projet"

    except Exception as e:
        return False, f"❌ Erreur lors de la mise à jour des codes projet : {str(e)}"

# ============================================================================
# TRANSFERT DES DEVIS BATISIMPLY -> POSTGRESQL -> SQL SERVER
# ============================================================================

def transfer_devis_batisimply_to_postgres():
    """
    Transfère les devis depuis BatiSimply vers PostgreSQL.
    """
    try:
        # Vérification des identifiants
        creds = load_credentials()
        if not creds or "postgres" not in creds:
            return False, "❌ Informations de connexion PostgreSQL manquantes"

        # Récupération du token BatiSimply
        token = recup_batisimply_token()
        if not token:
            return False, "❌ Impossible de récupérer le token BatiSimply"

        # Connexion PostgreSQL
        postgres_conn = connect_to_postgres(
            creds["postgres"]["host"],
            creds["postgres"]["user"],
            creds["postgres"]["password"],
            creds["postgres"]["database"],
            creds["postgres"].get("port", "5432")
        )
        if not postgres_conn:
            return False, "❌ Connexion PostgreSQL échouée"

        postgres_cursor = postgres_conn.cursor()

        # Récupération des devis depuis BatiSimply
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        # Essayer différents endpoints possibles pour les devis
        endpoints_to_try = [
            'https://api.staging.batisimply.fr/api/quote',
            'https://api.staging.batisimply.fr/api/quotes',
            'https://api.staging.batisimply.fr/api/estimate',
            'https://api.staging.batisimply.fr/api/estimates'
        ]
        
        response = None
        for endpoint in endpoints_to_try:
            try:
                response = requests.get(endpoint, headers=headers, timeout=30)
                if response.status_code == 200 and response.headers.get('content-type', '').startswith('application/json'):
                    break
            except Exception as e:
                print(f"⚠️ Erreur avec l'endpoint {endpoint}: {e}")
                continue
        
        if not response:
            return True, "ℹ️ Aucun endpoint valide trouvé pour les devis - fonctionnalité non disponible"

        if response.status_code != 200:
            return False, f"❌ Erreur API BatiSimply : {response.status_code}. Réponse: {response.text[:200]}"

        # Vérifier si la réponse est du HTML (erreur 404 ou redirection)
        if response.headers.get('content-type', '').startswith('text/html'):
            return True, "ℹ️ L'API des devis retourne du HTML - fonctionnalité non disponible via cette API"

        try:
            devis = response.json()
        except json.JSONDecodeError as e:
            return False, f"❌ Erreur de parsing JSON de l'API BatiSimply : {str(e)}. Réponse: {response.text[:200]}"

        # Vérifier que devis est une liste ou un dictionnaire
        if isinstance(devis, dict):
            # Si c'est un dictionnaire, vérifier s'il contient une liste de devis
            if 'content' in devis:
                devis = devis['content']
            elif 'data' in devis:
                devis = devis['data']
            elif 'items' in devis:
                devis = devis['items']
            else:
                # Si c'est un dictionnaire simple, le traiter comme un seul devis
                devis = [devis]
        elif not isinstance(devis, list):
            return False, f"❌ Format de réponse inattendu de l'API BatiSimply. Attendu: liste ou dict, reçu: {type(devis)}"

        # Insertion dans PostgreSQL avec gestion des conflits
        for devi in devis:
            # Vérifier que devi est un dictionnaire
            if not isinstance(devi, dict):
                print(f"⚠️ Devis ignoré (format inattendu): {type(devi)} - {devi}")
                continue
            code = devi.get('id')  # L'ID BatiSimply devient le code
            nom = devi.get('name')
            date_creation = devi.get('creationDate')
            sujet = devi.get('description', '')  # Utiliser la description comme sujet
            
            query_postgres = """
            INSERT INTO batigest_devis (code, date, nom, sujet, sync)
            VALUES (%s, %s, %s, %s, FALSE)
            ON CONFLICT (code) DO UPDATE SET
                date = EXCLUDED.date,
                nom = EXCLUDED.nom,
                sujet = EXCLUDED.sujet,
                sync = FALSE
            """
            
            postgres_cursor.execute(query_postgres, (code, date_creation, nom, sujet))

        postgres_conn.commit()
        postgres_cursor.close()
        postgres_conn.close()

        return True, f"✅ {len(devis)} devi(s) transféré(s) depuis BatiSimply vers PostgreSQL"

    except Exception as e:
        return False, f"❌ Erreur lors du transfert BatiSimply -> PostgreSQL : {str(e)}"

def transfer_devis_postgres_to_sqlserver():
    """
    Transfère les devis depuis PostgreSQL vers SQL Server (Batigest).
    """
    try:
        # Vérification des identifiants
        creds = load_credentials()
        if not creds or "sqlserver" not in creds or "postgres" not in creds:
            return False, "❌ Informations de connexion manquantes"

        # Établissement des connexions
        sqlserver_conn = connect_to_sqlserver(
            creds["sqlserver"]["server"],
            creds["sqlserver"]["user"],
            creds["sqlserver"]["password"],
            creds["sqlserver"]["database"]
        )
        postgres_conn = connect_to_postgres(
            creds["postgres"]["host"],
            creds["postgres"]["user"],
            creds["postgres"]["password"],
            creds["postgres"]["database"],
            creds["postgres"].get("port", "5432")
        )
        
        if not sqlserver_conn or not postgres_conn:
            return False, "❌ Connexion aux bases échouée"

        # Création des curseurs
        sqlserver_cursor = sqlserver_conn.cursor()
        postgres_cursor = postgres_conn.cursor()

        # Récupération des devis non synchronisés
        query = "SELECT * FROM batigest_devis WHERE sync = FALSE"
        postgres_cursor.execute(query)
        devis = postgres_cursor.fetchall()

        # Insertion dans SQL Server
        for devi in devis:
            # Structure: code, date, nom, adr, cp, ville, sujet, dateconcretis, tempsmo, sync_date, sync
            code, date, nom, adr, cp, ville, sujet, dateconcretis, tempsmo, sync_date, sync = devi
            
            # Vérifier si le devis existe déjà dans SQL Server
            check_query = "SELECT COUNT(*) FROM dbo.Devis WHERE Code = ?"
            sqlserver_cursor.execute(check_query, (code,))
            exists = sqlserver_cursor.fetchone()[0] > 0
            
            if exists:
                # Mise à jour
                update_query = """
                UPDATE dbo.Devis 
                SET Nom = ?, Date = ?, Sujet = ?
                WHERE Code = ?
                """
                sqlserver_cursor.execute(update_query, (nom, date, sujet, code))
            else:
                # Insertion
                insert_query = """
                INSERT INTO dbo.Devis (Code, Nom, Date, Sujet)
                VALUES (?, ?, ?, ?)
                """
                sqlserver_cursor.execute(insert_query, (code, nom, date, sujet))
            
            # Marquer comme synchronisé dans PostgreSQL
            update_postgres = "UPDATE batigest_devis SET sync = TRUE WHERE code = %s"
            postgres_cursor.execute(update_postgres, (code,))

        sqlserver_conn.commit()
        postgres_conn.commit()
        
        # Fermeture des connexions
        sqlserver_cursor.close()
        postgres_cursor.close()
        sqlserver_conn.close()
        postgres_conn.close()

        return True, f"✅ {len(devis)} devi(s) transféré(s) vers SQL Server"

    except Exception as e:
        return False, f"❌ Erreur lors du transfert PostgreSQL -> SQL Server : {str(e)}"

# ============================================================================
# FONCTIONS DE SYNCHRONISATION COMPLÈTE
# ============================================================================

def sync_batisimply_to_sqlserver():
    """
    Synchronisation complète BatiSimply -> PostgreSQL -> SQL Server.
    """
    print("=== DÉBUT DE LA SYNCHRONISATION BATISIMPLY → SQL SERVER ===")
    messages = []
    overall_success = True
    
    try:
        # 1. Transfert des chantiers
        print("🔄 Synchronisation des chantiers...")
        success, message = transfer_chantiers_batisimply_to_postgres()
        print(message)
        messages.append(message)
        
        if success:
            success, message = transfer_chantiers_postgres_to_sqlserver()
            print(message)
            messages.append(message)
            if not success:
                overall_success = False
        else:
            overall_success = False
        
        # 2. Transfert des heures
        print("🔄 Synchronisation des heures...")
        success, message = transfer_heures_batisimply_to_postgres()
        print(message)
        messages.append(message)
        
        if success:
            # Mettre à jour les codes projet des heures
            print("🔄 Mise à jour des codes projet...")
            success_update, message_update = update_code_projet_chantiers()
            print(message_update)
            messages.append(message_update)
            
            success, message = transfer_heures_postgres_to_sqlserver()
            print(message)
            messages.append(message)
            if not success:
                overall_success = False
        else:
            overall_success = False
        
        # 3. Transfert des devis
        print("🔄 Synchronisation des devis...")
        success, message = transfer_devis_batisimply_to_postgres()
        print(message)
        messages.append(message)
        
        if success:
            success, message = transfer_devis_postgres_to_sqlserver()
            print(message)
            messages.append(message)
            if not success:
                overall_success = False
        else:
            overall_success = False
        
        print("=== FIN DE LA SYNCHRONISATION BATISIMPLY → SQL SERVER ===")
        
        if overall_success:
            return True, "✅ Synchronisation BatiSimply → SQL Server terminée avec succès"
        else:
            return False, "⚠️ Synchronisation BatiSimply → SQL Server terminée avec des erreurs"
            
    except Exception as e:
        error_msg = f"❌ Erreur lors de la synchronisation BatiSimply → SQL Server : {str(e)}"
        print(error_msg)
        return False, error_msg
