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
            return False, "[ERREUR] Informations de connexion PostgreSQL manquantes"

        # Récupération du token BatiSimply
        token = recup_batisimply_token()
        if not token:
            return False, "[ERREUR] Impossible de récupérer le token BatiSimply"

        # Connexion PostgreSQL
        postgres_conn = connect_to_postgres(
            creds["postgres"]["host"],
            creds["postgres"]["user"],
            creds["postgres"]["password"],
            creds["postgres"]["database"],
            creds["postgres"].get("port", "5432")
        )
        if not postgres_conn:
            return False, "[ERREUR] Connexion PostgreSQL échouée"

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
            return False, f"[ERREUR] Erreur API BatiSimply : {response.status_code}"

        try:
            chantiers = response.json()
        except json.JSONDecodeError as e:
            return False, f"[ERREUR] Erreur de parsing JSON de l'API BatiSimply : {str(e)}. Réponse: {response.text[:200]}"

        # Vérifier que chantiers est une liste ou un dictionnaire
        if isinstance(chantiers, dict):
            # Si c'est un dictionnaire, vérifier s'il contient une liste de chantiers
            if 'elements' in chantiers:
                chantiers = chantiers['elements']
            elif 'content' in chantiers:
                chantiers = chantiers['content']
            elif 'data' in chantiers:
                chantiers = chantiers['data']
            elif 'items' in chantiers:
                chantiers = chantiers['items']
            else:
                # Si c'est un dictionnaire simple, le traiter comme un seul chantier
                chantiers = [chantiers]
        elif not isinstance(chantiers, list):
            return False, f"[ERREUR] Format de réponse inattendu de l'API BatiSimply. Attendu: liste ou dict, reçu: {type(chantiers)}"

        # Insertion dans PostgreSQL avec gestion des conflits
        inserted_count = 0
        for chantier in chantiers:
            # Vérifier que chantier est un dictionnaire
            if not isinstance(chantier, dict):
                print(f"[ATTENTION] Chantier ignoré (format inattendu): {type(chantier)} - {chantier}")
                continue
            # Normaliser et valider les champs obligatoires
            raw_id = chantier.get('id')
            raw_project_code = (
                chantier.get('projectCode') or chantier.get('project_code') or chantier.get('code')
            )
            code = None
            if raw_project_code is not None:
                code = str(raw_project_code).strip()
            elif raw_id is not None:
                # Fallback: utiliser l'id zéro-rempli pour préserver un code compatible Batigest
                try:
                    code = str(int(raw_id)).zfill(8)
                except Exception:
                    code = str(raw_id).strip()
            else:
                code = ""
            raw_name = chantier.get('name')
            nom_client = str(raw_name).strip() if raw_name is not None else ""

            if not code or not nom_client:
                print(f"[ATTENTION] Chantier ignoré (code/nom manquant) : id='{raw_id}' name='{raw_name}'")
                continue
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
            inserted_count += 1

        postgres_conn.commit()
        postgres_cursor.close()
        postgres_conn.close()

        return True, f"[OK] {inserted_count} chantier(s) transféré(s) depuis BatiSimply vers PostgreSQL"

    except Exception as e:
        return False, f"[ERREUR] Erreur lors du transfert BatiSimply -> PostgreSQL : {str(e)}"

def transfer_chantiers_postgres_to_sqlserver():
    """
    Transfère les chantiers depuis PostgreSQL vers SQL Server (Batigest).
    """
    try:
        # Vérification des identifiants
        creds = load_credentials()
        if not creds or "sqlserver" not in creds or "postgres" not in creds:
            return False, "[ERREUR] Informations de connexion manquantes"

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
            return False, "[ERREUR] Connexion aux bases échouée"

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
            print("[INFO] Structure de la table ChantierDef :")
            for col in columns_info:
                print(f"  - {col[0]}: {col[1]} (max: {col[2]})")
        except Exception as e:
            print(f"[ATTENTION] Impossible de récupérer la structure de la table: {e}")

        # Récupération des chantiers non synchronisés et valides
        query = (
            """
            SELECT *
            FROM batigest_chantiers
            WHERE NOT sync
              AND code IS NOT NULL AND code <> ''
              AND nom_client IS NOT NULL AND nom_client <> ''
            """
        )
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
            print(f"[DEBUG] Debug chantier: code='{code_truncated}' (len={len(code_truncated)}), nom_client='{nom_client_truncated}' (len={len(nom_client_truncated)}), etat='{description_truncated}' (len={len(description_truncated)})")
            print(f"   Données originales: code='{code}', nom_client='{nom_client}', description='{description}'")
            
            # Ignorer les chantiers avec des données vides
            if not code_truncated or not nom_client_truncated:
                print(f"[ATTENTION] Chantier ignoré (données vides): code='{code_truncated}', nom='{nom_client_truncated}'")
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
                print(f"[ATTENTION] Erreur lors de l'insertion/mise à jour du chantier {code_truncated}: {e}")
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

        return True, f"[OK] {len(chantiers)} chantier(s) transféré(s) vers SQL Server"

    except Exception as e:
        return False, f"[ERREUR] Erreur lors du transfert PostgreSQL -> SQL Server : {str(e)}"

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
            return False, "[ERREUR] Informations de connexion PostgreSQL manquantes"

        # Récupération du token BatiSimply
        token = recup_batisimply_token()
        if not token:
            return False, "[ERREUR] Impossible de récupérer le token BatiSimply"

        # Connexion PostgreSQL
        postgres_conn = connect_to_postgres(
            creds["postgres"]["host"],
            creds["postgres"]["user"],
            creds["postgres"]["password"],
            creds["postgres"]["database"],
            creds["postgres"].get("port", "5432")
        )
        if not postgres_conn:
            return False, "[ERREUR] Connexion PostgreSQL échouée"

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
        print(f"[CALENDRIER] Fenêtre d'import des heures: {start_date_str} -> {end_date_str}")

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
            return False, f"[ERREUR] Erreur API BatiSimply : {response.status_code}. Réponse: {response.text[:200]}"

        try:
            heures = response.json()
        except json.JSONDecodeError as e:
            return False, f"[ERREUR] Erreur de parsing JSON de l'API BatiSimply : {str(e)}. Réponse: {response.text[:200]}"

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
            return False, f"[ERREUR] Format de réponse inattendu de l'API BatiSimply. Attendu: liste ou dict, reçu: {type(heures)}"

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
                print(f"[ATTENTION] Heure ignorée (format inattendu): {type(h)} - {h}")
                continue
                
            heure_id = h.get("id")
            start_iso = h.get("startDate")
            end_iso = h.get("endDate")
            
            project_obj = h.get("project", {}) or {}
            # Essayer de récupérer directement le code chantier fourni par l'API (projectCode)
            project_code = (
                project_obj.get("projectCode")
                or project_obj.get("code")
                or project_obj.get("project_code")
            )
            if isinstance(project_code, int):
                project_code = str(project_code)
            if isinstance(project_code, str):
                project_code = project_code.strip()

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
            id_projet = project_obj.get("id")
            status = h.get("managementStatus")
            total_heure = h.get("totalTimeMinutes")
            panier = h.get("hasPackedLunch", False)
            trajet = h.get("hasHomeToWorkJourney", False)

            # Fallback 1: si aucun project_code mais id_projet fourni, tenter de récupérer le projet pour obtenir le code exact
            if (not project_code) and (id_projet is not None):
                try:
                    resp_proj = requests.get(
                        f"https://api.staging.batisimply.fr/api/project/{id_projet}",
                        headers=headers,
                        timeout=12,
                    )
                    if resp_proj.status_code == 200:
                        try:
                            pjson = resp_proj.json() or {}
                        except Exception:
                            pjson = {}
                        project_code = (
                            str(pjson.get("projectCode") or pjson.get("code") or pjson.get("project_code") or "").strip()
                        ) or None
                except requests.RequestException:
                    project_code = None

            # Fallback 2: à défaut, utiliser l'id zéro-rempli pour rester compatible avec Batigest
            if (not project_code) and (id_projet is not None):
                try:
                    project_code = str(int(id_projet)).zfill(8)
                except Exception:
                    project_code = None

            # Upsert: met à jour si l'heure existe déjà et remet sync=false si modification
            postgres_cursor.execute("""
                INSERT INTO batigest_heures(
                    id_heure, date_debut, date_fin, id_utilisateur,
                    id_projet, status_management,
                    total_heure, panier, trajet, code_projet, sync
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id_heure) DO UPDATE SET
                    date_debut = EXCLUDED.date_debut,
                    date_fin = EXCLUDED.date_fin,
                    id_utilisateur = EXCLUDED.id_utilisateur,
                    id_projet = EXCLUDED.id_projet,
                    status_management = EXCLUDED.status_management,
                    total_heure = EXCLUDED.total_heure,
                    panier = EXCLUDED.panier,
                    trajet = EXCLUDED.trajet,
                    code_projet = COALESCE(EXCLUDED.code_projet, batigest_heures.code_projet),
                    sync = CASE WHEN (
                        batigest_heures.date_debut IS DISTINCT FROM EXCLUDED.date_debut OR
                        batigest_heures.date_fin IS DISTINCT FROM EXCLUDED.date_fin OR
                        batigest_heures.id_utilisateur IS DISTINCT FROM EXCLUDED.id_utilisateur OR
                        batigest_heures.id_projet IS DISTINCT FROM EXCLUDED.id_projet OR
                        batigest_heures.status_management IS DISTINCT FROM EXCLUDED.status_management OR
                        batigest_heures.total_heure IS DISTINCT FROM EXCLUDED.total_heure OR
                        batigest_heures.panier IS DISTINCT FROM EXCLUDED.panier OR
                        batigest_heures.trajet IS DISTINCT FROM EXCLUDED.trajet OR
                        (EXCLUDED.code_projet IS NOT NULL AND batigest_heures.code_projet IS DISTINCT FROM EXCLUDED.code_projet)
                    ) THEN FALSE ELSE batigest_heures.sync END
            """, (
                heure_id, date_debut, date_fin, user_id,
                id_projet, status,
                total_heure, panier, trajet, project_code, False
            ))

        postgres_conn.commit()
        postgres_cursor.close()
        postgres_conn.close()

        return True, f"[OK] {len(heures)} heure(s) transférée(s) depuis BatiSimply vers PostgreSQL"

    except Exception as e:
        return False, f"[ERREUR] Erreur lors du transfert BatiSimply -> PostgreSQL : {str(e)}"

def transfer_heures_postgres_to_sqlserver():
    """
    Transfère les heures depuis PostgreSQL vers SQL Server (Batigest).
    """
    try:
        # Vérification des identifiants
        creds = load_credentials()
        if not creds or "sqlserver" not in creds or "postgres" not in creds:
            return False, "[ERREUR] Informations de connexion manquantes"

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
            return False, "[ERREUR] Connexion aux bases échouée"

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
            SELECT id_heure, date_debut, id_utilisateur, code_projet, total_heure, panier, trajet, id_projet
            FROM batigest_heures
            WHERE status_management = 'VALIDATED' AND NOT sync AND code_projet IS NOT NULL
        """)
        heures = postgres_cursor.fetchall()
        print(f"[INFO] {len(heures)} heure(s) à traiter...")

        transferred_ids = []

        for h in heures:
            id_heure, date_debut, id_utilisateur, code_projet, total_heure, panier, trajet, id_projet = h

            # Recherche de l'utilisateur avec plus de détails
            print(f"\n[DEBUG] Recherche de l'utilisateur {id_utilisateur} dans Salarie...")
            sqlserver_cursor.execute("""
                SELECT TOP 5 * 
                FROM Salarie 
                WHERE codebs = ?
            """, (id_utilisateur,))
            
            # Affichage des résultats de la recherche
            results = sqlserver_cursor.fetchall()
            if results:
                print("[OK] Utilisateurs trouvés :")
                for row in results:
                    print(f"  - {row}")
            else:
                print(f"[ATTENTION] Aucun utilisateur trouvé avec l'ID {id_utilisateur}")
                continue

            code_salarie = results[0][0]  # On prend le Code du premier résultat
            if not code_projet:
                print(f"[IGNORE] id_heure {id_heure} ignorée: code_projet manquant")
                continue
            # Normaliser le code chantier pour respecter Batigest (8 caractères)
            code_chantier = str(code_projet)
            if not code_chantier.isdigit() or len(code_chantier) != 8:
                try:
                    # fallback: utiliser id_projet si numérique
                    if id_projet is not None:
                        code_chantier = str(int(id_projet)).zfill(8)
                except Exception:
                    pass
            # total_heure vient de BatiSimply (minutes). Conversion en heures décimales pour NbH0.
            nb_h0 = (float(total_heure) / 60.0) if total_heure is not None else 0.0
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
                    print("[SYNC] Clé modifiée pour id_heure", id_heure,
                          f": ({old_code_chantier}, {old_code_salarie}, {old_date}) -> ({code_chantier}, {code_salarie}, {date_debut})")

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

            # Pas de mapping existant (nouvelle heure) -> upsert sur la nouvelle clé
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

        return True, f"[OK] {len(transferred_ids)} heure(s) transférée(s) vers SQL Server"

    except Exception as e:
        return False, f"[ERREUR] Erreur lors du transfert PostgreSQL -> SQL Server : {str(e)}"

def update_code_projet_chantiers():
    """
    Met à jour les codes projet des heures en utilisant la correspondance avec les chantiers.
    """
    try:
        creds = load_credentials()
        if not creds or "postgres" not in creds:
            return False, "[ERREUR] Informations de connexion PostgreSQL manquantes"

        postgres_conn = connect_to_postgres(
            creds["postgres"]["host"],
            creds["postgres"]["user"],
            creds["postgres"]["password"],
            creds["postgres"]["database"],
            creds["postgres"].get("port", "5432")
        )
        if not postgres_conn:
            return False, "[ERREUR] Connexion PostgreSQL échouée"

        postgres_cursor = postgres_conn.cursor()

        # Mettre à jour les codes projet des heures avec plusieurs stratégies de correspondance:
        # - id_projet::text = code (cas BatiSimply -> Postgres)
        # - id_projet = code::bigint quand code est numérique
        # - LPAD(id_projet::text, 8, '0') = code (cas codes Batigest '00000001')
        postgres_cursor.execute("""
            UPDATE batigest_heures AS h
            SET code_projet = c.code
            FROM batigest_chantiers AS c
            WHERE h.code_projet IS NULL
              AND (
                    h.id_projet::text = c.code
                 OR (c.code ~ '^[0-9]+$' AND h.id_projet = c.code::bigint)
                 OR LPAD(h.id_projet::text, 8, '0') = c.code
              )
        """)

        updated_count = postgres_cursor.rowcount

        # Deuxième passe: compléter/corriger via l'API pour:
        #  - code_projet manquant
        #  - code_projet égal à LPAD(id_projet, 8, '0') (fallback générique à corriger par le vrai projectCode)
        postgres_cursor.execute(
            """
            SELECT DISTINCT id_projet, code_projet
            FROM batigest_heures
            WHERE id_projet IS NOT NULL
              AND (
                    code_projet IS NULL
                 OR code_projet = LPAD(id_projet::text, 8, '0')
              )
            """
        )
        missing_rows = postgres_cursor.fetchall()
        missing_ids = [(row[0], row[1]) for row in missing_rows]

        if missing_ids:
            token = recup_batisimply_token()
            if token:
                headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                try:
                    # Récupérer la liste des projets accessibles (contient projectCode)
                    list_resp = requests.get(
                        "https://api.staging.batisimply.fr/api/project",
                        headers=headers,
                        timeout=15,
                    )
                    projects = []
                    if list_resp.status_code == 200:
                        try:
                            pj = list_resp.json()
                            if isinstance(pj, dict):
                                # support elements/content/items/data formats
                                for key in ("elements", "content", "items", "data"):
                                    if key in pj and isinstance(pj[key], list):
                                        projects = pj[key]
                                        break
                                if not projects and all(k in pj for k in ("id", "projectCode")):
                                    projects = [pj]
                            elif isinstance(pj, list):
                                projects = pj
                        except Exception:
                            projects = []

                    # Construire un mapping id -> projectCode/code
                    id_to_code = {}
                    for p in projects or []:
                        try:
                            pid_val = p.get("id")
                            pcode = (
                                str(p.get("projectCode") or p.get("code") or p.get("project_code") or "").strip()
                            )
                            if pid_val is not None and pcode:
                                id_to_code[int(pid_val)] = pcode
                        except Exception:
                            continue

                    for pid, current_code in missing_ids:
                        pcode = id_to_code.get(int(pid))
                        if pcode and pcode != (current_code or ""):
                            postgres_cursor.execute(
                                "UPDATE batigest_heures SET code_projet = %s WHERE id_projet = %s AND code_projet IS NULL",
                                (pcode, pid),
                            )
                            updated_count += postgres_cursor.rowcount
                            postgres_cursor.execute(
                                "UPDATE batigest_heures SET code_projet = %s WHERE id_projet = %s AND code_projet = LPAD(id_projet::text, 8, '0')",
                                (pcode, pid),
                            )
                            updated_count += postgres_cursor.rowcount
                except requests.RequestException:
                    pass

        postgres_conn.commit()
        postgres_cursor.close()
        postgres_conn.close()

        return True, f"[OK] {updated_count} heure(s) mise(s) à jour avec le code projet"

    except Exception as e:
        return False, f"[ERREUR] Erreur lors de la mise à jour des codes projet : {str(e)}"

# ============================================================================
# TRANSFERT DES DEVIS BATISIMPLY -> POSTGRESQL -> SQL SERVER
# ============================================================================

def transfer_devis_batisimply_to_postgres():
    """
    Transfère les devis depuis BatiSimply vers PostgreSQL.
    """
    try:
        # Garde-fou global: ne rien faire en mode chantier
        _creds_mode = (load_credentials() or {}).get("mode", "chantier").strip().lower()
        if _creds_mode != "devis":
            return True, "[INFO] Mode 'chantier' actif: transfert des devis depuis BatiSimply ignoré"
        # Vérification des identifiants
        creds = load_credentials()
        if not creds or "postgres" not in creds:
            return False, "[ERREUR] Informations de connexion PostgreSQL manquantes"

        # Récupération du token BatiSimply
        token = recup_batisimply_token()
        if not token:
            return False, "[ERREUR] Impossible de récupérer le token BatiSimply"

        # Connexion PostgreSQL
        postgres_conn = connect_to_postgres(
            creds["postgres"]["host"],
            creds["postgres"]["user"],
            creds["postgres"]["password"],
            creds["postgres"]["database"],
            creds["postgres"].get("port", "5432")
        )
        if not postgres_conn:
            return False, "[ERREUR] Connexion PostgreSQL échouée"

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
                print(f"[ATTENTION] Erreur avec l'endpoint {endpoint}: {e}")
                continue
        
        if not response:
            return True, "[INFO] Aucun endpoint valide trouvé pour les devis - fonctionnalité non disponible"

        if response.status_code != 200:
            return False, f"[ERREUR] Erreur API BatiSimply : {response.status_code}. Réponse: {response.text[:200]}"

        # Vérifier si la réponse est du HTML (erreur 404 ou redirection)
        if response.headers.get('content-type', '').startswith('text/html'):
            return True, "[INFO] L'API des devis retourne du HTML - fonctionnalité non disponible via cette API"

        try:
            devis = response.json()
        except json.JSONDecodeError as e:
            return False, f"[ERREUR] Erreur de parsing JSON de l'API BatiSimply : {str(e)}. Réponse: {response.text[:200]}"

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
            return False, f"[ERREUR] Format de réponse inattendu de l'API BatiSimply. Attendu: liste ou dict, reçu: {type(devis)}"

        # Insertion dans PostgreSQL avec gestion des conflits
        for devi in devis:
            # Vérifier que devi est un dictionnaire
            if not isinstance(devi, dict):
                print(f"[ATTENTION] Devis ignoré (format inattendu): {type(devi)} - {devi}")
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

        return True, f"[OK] {len(devis)} devi(s) transféré(s) depuis BatiSimply vers PostgreSQL"

    except Exception as e:
        return False, f"[ERREUR] Erreur lors du transfert BatiSimply -> PostgreSQL : {str(e)}"

def transfer_devis_postgres_to_sqlserver():
    """
    Transfère les devis depuis PostgreSQL vers SQL Server (Batigest).
    """
    try:
        # Vérification des identifiants
        creds = load_credentials()
        if not creds or "sqlserver" not in creds or "postgres" not in creds:
            return False, "[ERREUR] Informations de connexion manquantes"

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
            return False, "[ERREUR] Connexion aux bases échouée"

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

        return True, f"[OK] {len(devis)} devi(s) transféré(s) vers SQL Server"

    except Exception as e:
        return False, f"[ERREUR] Erreur lors du transfert PostgreSQL -> SQL Server : {str(e)}"

# ============================================================================
# FONCTIONS DE SYNCHRONISATION COMPLÈTE
# ============================================================================

def sync_batisimply_to_sqlserver():
    """
    Synchronisation complète BatiSimply -> PostgreSQL -> SQL Server.
    """
    print("=== DÉBUT DE LA SYNCHRONISATION BATISIMPLY -> SQL SERVER ===")
    messages = []
    overall_success = True
    
    try:
        # Respect du mode (chantier|devis) depuis credentials.json
        creds = load_credentials() or {}
        mode = (creds.get("mode") or "chantier").strip().lower()
        print(f"[INFO] Mode courant: {mode}")
        # 1. Transfert des chantiers
        print("[SYNC] Synchronisation des chantiers...")
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
        print("[SYNC] Synchronisation des heures...")
        success, message = transfer_heures_batisimply_to_postgres()
        print(message)
        messages.append(message)
        
        if success:
            # Mettre à jour les codes projet des heures
            print("[SYNC] Mise à jour des codes projet...")
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
        
        # 3. Transfert des devis (uniquement en mode 'devis')
        if mode == "devis":
            print("[SYNC] Synchronisation des devis...")
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
        else:
            print("[INFO] Mode 'chantier' actif: envoi des devis désactivé.")
        
        print("=== FIN DE LA SYNCHRONISATION BATISIMPLY -> SQL SERVER ===")
        
        if overall_success:
            return True, "[OK] Synchronisation BatiSimply -> SQL Server terminée avec succès"
        else:
            return False, "[ATTENTION] Synchronisation BatiSimply -> SQL Server terminée avec des erreurs"
            
    except Exception as e:
        error_msg = f"[ERREUR] Erreur lors de la synchronisation BatiSimply -> SQL Server : {str(e)}"
        print(error_msg)
        return False, error_msg
