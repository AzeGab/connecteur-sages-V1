# app/services/batigest/heures.py
# Module de gestion du transfert des heures Batigest
# Ce fichier contient les fonctions nécessaires pour transférer les heures
# entre BatiSimply, PostgreSQL et SQL Server

import psycopg2
from app.services.connex import connect_to_postgres, connect_to_sqlserver, load_credentials, recup_batisimply_token
import requests
import json
from datetime import datetime, timedelta
import pytz

# ============================================================================
# TRANSFERT BATISIMPLY VERS POSTGRESQL
# ============================================================================

def transfer_heures_to_postgres():
    """
    Transfère les heures depuis BatiSimply vers PostgreSQL.
    
    Cette fonction :
    1. Récupère le token d'authentification
    2. Récupère les heures depuis BatiSimply via l'API
    3. Les insère dans PostgreSQL avec gestion des doublons
    4. Gère la conversion de timezone et la normalisation des dates
    
    Returns:
        bool: True si le transfert a réussi, False sinon
    """
    try:
        # Récupération du token
        token = recup_batisimply_token()
        if not token:
            print("❌ Impossible de continuer sans token Batisimply")
            return False

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

        # Configuration de l'API BatiSimply
        API_URL = "https://api.staging.batisimply.fr/api/timeSlotManagement/allUsers"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Configuration de la fenêtre de temps (par défaut 180 jours)
        timezone_name = creds.get("timezone", "Europe/Paris")
        days_back = creds.get("heures_days_back", 180)
        
        # Calcul des dates de début et fin
        local_tz = pytz.timezone(timezone_name)
        now = datetime.now(local_tz)
        start_date = now - timedelta(days=days_back)
        
        # Conversion en UTC pour l'API
        start_utc = start_date.astimezone(pytz.UTC)
        end_utc = now.astimezone(pytz.UTC)
        
        print(f"📅 Récupération des heures des {days_back} derniers jours")
        print(f"📅 Période : {start_date.strftime('%Y-%m-%d')} à {now.strftime('%Y-%m-%d')} ({timezone_name})")

        # Récupération des heures depuis BatiSimply
        response = requests.get(API_URL, headers=headers)
        if response.status_code != 200:
            print(f"❌ Erreur API BatiSimply : {response.status_code}")
            return False

        heures_data = response.json()
        heures_count = 0
        heures_updated = 0

        postgres_cursor = postgres_conn.cursor()

        # Traitement de chaque heure
        for heure in heures_data:
            try:
                # Conversion des dates UTC vers le timezone local
                date_debut_utc = datetime.fromisoformat(heure['dateStart'].replace('Z', '+00:00'))
                date_fin_utc = datetime.fromisoformat(heure['dateEnd'].replace('Z', '+00:00'))
                
                # Conversion vers le timezone local
                date_debut_local = date_debut_utc.astimezone(local_tz)
                date_fin_local = date_fin_utc.astimezone(local_tz)
                
                # Normalisation à la minute (suppression des secondes)
                date_debut_normalized = date_debut_local.replace(second=0, microsecond=0)
                date_fin_normalized = date_fin_local.replace(second=0, microsecond=0)
                
                # Vérification si l'heure est dans la fenêtre de temps
                if date_debut_normalized < start_date or date_debut_normalized > now:
                    continue

                # Calcul du total d'heures
                duree = date_fin_normalized - date_debut_normalized
                total_heures = duree.total_seconds() / 3600

                # Insertion avec UPSERT (ON CONFLICT DO UPDATE)
                postgres_cursor.execute("""
                    INSERT INTO batigest_heures 
                    (id_heure, date_debut, date_fin, id_utilisateur, id_projet, 
                     status_management, total_heure, panier, trajet, code_projet, sync)
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
                    code_projet = EXCLUDED.code_projet,
                    sync = FALSE
                """, (
                    heure['id'],
                    date_debut_normalized,
                    date_fin_normalized,
                    heure['userId'],
                    heure['projectId'],
                    heure.get('statusManagement', ''),
                    total_heures,
                    heure.get('basket', False),
                    heure.get('travel', False),
                    None,  # code_projet sera mis à jour plus tard
                    False
                ))
                
                heures_count += 1
                
                # Vérifier si c'était une mise à jour
                if postgres_cursor.rowcount == 0:
                    heures_updated += 1

            except Exception as e:
                print(f"❌ Erreur lors du traitement de l'heure {heure.get('id')} : {e}")
                continue

        # Validation des modifications
        postgres_conn.commit()
        postgres_cursor.close()
        postgres_conn.close()

        print(f"✅ {heures_count} heure(s) traitées ({heures_updated} mises à jour)")
        return True

    except Exception as e:
        print(f"❌ Erreur lors du transfert vers PostgreSQL : {e}")
        return False

# ============================================================================
# TRANSFERT POSTGRESQL VERS SQL SERVER
# ============================================================================

def transfer_heures_to_sqlserver():
    """
    Transfère les heures depuis PostgreSQL vers SQL Server.
    
    Cette fonction :
    1. Récupère les heures non synchronisées depuis PostgreSQL
    2. Vérifie les correspondances avec les salariés dans SQL Server
    3. Insère ou met à jour les heures dans SQL Server
    4. Met à jour le statut de synchronisation
    
    Returns:
        int: Nombre d'heures transférées avec succès
    """
    try:
        # Connexions aux bases de données
        creds = load_credentials()
        if not creds or "postgres" not in creds or "sqlserver" not in creds:
            print("❌ Informations de connexion manquantes")
            return 0

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

        if not postgres_conn or not sqlserver_conn:
            print("❌ Connexion aux bases échouée")
            return 0

        postgres_cursor = postgres_conn.cursor()
        sqlserver_cursor = sqlserver_conn.cursor()

        # Récupération des heures non synchronisées avec code_projet
        postgres_cursor.execute("""
            SELECT id_heure, date_debut, date_fin, id_utilisateur, id_projet, 
                   status_management, total_heure, panier, trajet, code_projet
            FROM batigest_heures 
            WHERE sync = FALSE AND code_projet IS NOT NULL
        """)

        heures = postgres_cursor.fetchall()
        print(f"📦 {len(heures)} heure(s) à traiter...")

        # Vérification de la structure de la table Salarie
        sqlserver_cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'Salarie'
        """)
        salarie_columns = sqlserver_cursor.fetchall()
        print("📋 Structure de la table Salarie :")
        for col in salarie_columns:
            print(f"  - {col[0]}: {col[1]}")

        heures_transferees = 0

        # Traitement de chaque heure
        for heure in heures:
            try:
                id_heure, date_debut, date_fin, id_utilisateur, id_projet, status_management, total_heure, panier, trajet, code_projet = heure

                # Recherche du salarié correspondant
                sqlserver_cursor.execute("""
                    SELECT Code FROM Salarie WHERE codebs = ?
                """, (str(id_utilisateur),))

                salarie_result = sqlserver_cursor.fetchone()
                if not salarie_result:
                    print(f"⚠️ Aucun utilisateur trouvé avec l'ID {id_utilisateur}")
                    continue

                code_salarie = salarie_result[0]
                date_heure = date_debut.date()

                # Vérification si l'enregistrement existe déjà
                sqlserver_cursor.execute("""
                    SELECT CodeChantier, CodeSalarie, Date, Heures, Commentaire
                    FROM SuiviMO 
                    WHERE CodeChantier = ? AND CodeSalarie = ? AND Date = ?
                """, (code_projet, code_salarie, date_heure))

                existing_record = sqlserver_cursor.fetchone()

                if existing_record:
                    # Mise à jour si les valeurs diffèrent
                    existing_heures, existing_commentaire = existing_record[3], existing_record[4]
                    if existing_heures != total_heure or existing_commentaire != status_management:
                        sqlserver_cursor.execute("""
                            UPDATE SuiviMO 
                            SET Heures = ?, Commentaire = ?
                            WHERE CodeChantier = ? AND CodeSalarie = ? AND Date = ?
                        """, (total_heure, status_management, code_projet, code_salarie, date_heure))
                        print(f"🔄 Mise à jour heure {id_heure} : {code_projet}/{code_salarie}/{date_heure}")
                    else:
                        print(f"⏭️ Heure {id_heure} inchangée : {code_projet}/{code_salarie}/{date_heure}")
                else:
                    # Insertion d'un nouvel enregistrement
                    sqlserver_cursor.execute("""
                        INSERT INTO SuiviMO 
                        (CodeChantier, CodeSalarie, Date, Heures, Commentaire)
                        VALUES (?, ?, ?, ?, ?)
                    """, (code_projet, code_salarie, date_heure, total_heure, status_management))
                    print(f"➕ Nouvelle heure {id_heure} : {code_projet}/{code_salarie}/{date_heure}")

                # Mise à jour du statut de synchronisation
                postgres_cursor.execute("""
                    UPDATE batigest_heures SET sync = TRUE WHERE id_heure = ?
                """, (id_heure,))

                heures_transferees += 1

            except Exception as e:
                print(f"❌ Erreur lors du traitement de l'heure {id_heure} : {e}")
                continue

        # Validation des modifications
        postgres_conn.commit()
        sqlserver_conn.commit()

        # Fermeture des connexions
        postgres_cursor.close()
        sqlserver_cursor.close()
        postgres_conn.close()
        sqlserver_conn.close()

        print(f"✅ {heures_transferees} heure(s) transférée(s) avec succès")
        return heures_transferees

    except Exception as e:
        print(f"❌ Erreur lors du transfert vers SQL Server : {e}")
        return 0
