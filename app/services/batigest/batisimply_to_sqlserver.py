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

        chantiers = response.json()

        # Insertion dans PostgreSQL avec gestion des conflits
        for chantier in chantiers:
            id_projet = chantier.get('id')
            nom = chantier.get('name')
            date_debut = chantier.get('startDate')
            date_fin = chantier.get('endDate')
            statut = chantier.get('status')
            code_client = chantier.get('clientCode')
            
            query_postgres = """
            INSERT INTO batigest_chantiers (id_projet, nom, date_debut, date_fin, statut, code_client, sync)
            VALUES (%s, %s, %s, %s, %s, %s, FALSE)
            ON CONFLICT (id_projet) DO UPDATE SET
                nom = EXCLUDED.nom,
                date_debut = EXCLUDED.date_debut,
                date_fin = EXCLUDED.date_fin,
                statut = EXCLUDED.statut,
                code_client = EXCLUDED.code_client,
                sync = FALSE
            """
            
            postgres_cursor.execute(query_postgres, (id_projet, nom, date_debut, date_fin, statut, code_client))

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

        # Récupération des chantiers non synchronisés
        query = "SELECT * FROM batigest_chantiers WHERE sync = FALSE"
        postgres_cursor.execute(query)
        chantiers = postgres_cursor.fetchall()

        # Insertion dans SQL Server
        for chantier in chantiers:
            id_projet, nom, date_debut, date_fin, statut, code_client, sync = chantier
            
            # Vérifier si le chantier existe déjà dans SQL Server
            check_query = "SELECT COUNT(*) FROM dbo.ChantierDef WHERE Code = %s"
            sqlserver_cursor.execute(check_query, (id_projet,))
            exists = sqlserver_cursor.fetchone()[0] > 0
            
            if exists:
                # Mise à jour
                update_query = """
                UPDATE dbo.ChantierDef 
                SET Libelle = %s, DateDebut = %s, DateFin = %s, Etat = %s, CodeClient = %s
                WHERE Code = %s
                """
                sqlserver_cursor.execute(update_query, (nom, date_debut, date_fin, statut, code_client, id_projet))
            else:
                # Insertion
                insert_query = """
                INSERT INTO dbo.ChantierDef (Code, Libelle, DateDebut, DateFin, Etat, CodeClient)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                sqlserver_cursor.execute(insert_query, (id_projet, nom, date_debut, date_fin, statut, code_client))
            
            # Marquer comme synchronisé dans PostgreSQL
            update_postgres = "UPDATE batigest_chantiers SET sync = TRUE WHERE id_projet = %s"
            postgres_cursor.execute(update_postgres, (id_projet,))

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

        # Récupération des heures depuis BatiSimply (dernières 30 jours)
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        # Calcul de la date de début (30 jours en arrière)
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        response = requests.get(
            f'https://api.staging.batisimply.fr/api/timeSlotManagement/allUsers?startDate={start_date}',
            headers=headers,
            timeout=30
        )

        if response.status_code != 200:
            return False, f"❌ Erreur API BatiSimply : {response.status_code}"

        heures = response.json()

        # Insertion dans PostgreSQL avec gestion des conflits
        for heure in heures:
            id_heure = heure.get('id')
            id_projet = heure.get('projectId')
            id_utilisateur = heure.get('userId')
            date_debut = heure.get('startDate')
            date_fin = heure.get('endDate')
            heures_travaillees = heure.get('hours')
            commentaire = heure.get('comment')
            
            query_postgres = """
            INSERT INTO batigest_heures (id_heure, id_projet, id_utilisateur, date_debut, date_fin, heures, commentaire, sync)
            VALUES (%s, %s, %s, %s, %s, %s, %s, FALSE)
            ON CONFLICT (id_heure) DO UPDATE SET
                id_projet = EXCLUDED.id_projet,
                id_utilisateur = EXCLUDED.id_utilisateur,
                date_debut = EXCLUDED.date_debut,
                date_fin = EXCLUDED.date_fin,
                heures = EXCLUDED.heures,
                commentaire = EXCLUDED.commentaire,
                sync = FALSE
            """
            
            postgres_cursor.execute(query_postgres, (id_heure, id_projet, id_utilisateur, date_debut, date_fin, heures_travaillees, commentaire))

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

        # Récupération des heures non synchronisées
        query = "SELECT * FROM batigest_heures WHERE sync = FALSE"
        postgres_cursor.execute(query)
        heures = postgres_cursor.fetchall()

        # Insertion dans SQL Server
        for heure in heures:
            id_heure, id_projet, id_utilisateur, date_debut, date_fin, heures_travaillees, commentaire, sync = heure
            
            # Vérifier si l'heure existe déjà dans SQL Server
            check_query = "SELECT COUNT(*) FROM dbo.SuiviMO WHERE CodeChantier = %s AND CodeSalarie = %s AND Date = %s"
            sqlserver_cursor.execute(check_query, (id_projet, id_utilisateur, date_debut.date()))
            exists = sqlserver_cursor.fetchone()[0] > 0
            
            if exists:
                # Mise à jour
                update_query = """
                UPDATE dbo.SuiviMO 
                SET Heures = %s, Commentaire = %s
                WHERE CodeChantier = %s AND CodeSalarie = %s AND Date = %s
                """
                sqlserver_cursor.execute(update_query, (heures_travaillees, commentaire, id_projet, id_utilisateur, date_debut.date()))
            else:
                # Insertion
                insert_query = """
                INSERT INTO dbo.SuiviMO (CodeChantier, CodeSalarie, Date, Heures, Commentaire)
                VALUES (%s, %s, %s, %s, %s)
                """
                sqlserver_cursor.execute(insert_query, (id_projet, id_utilisateur, date_debut.date(), heures_travaillees, commentaire))
            
            # Marquer comme synchronisé dans PostgreSQL
            update_postgres = "UPDATE batigest_heures SET sync = TRUE WHERE id_heure = %s"
            postgres_cursor.execute(update_postgres, (id_heure,))

        sqlserver_conn.commit()
        postgres_conn.commit()
        
        # Fermeture des connexions
        sqlserver_cursor.close()
        postgres_cursor.close()
        sqlserver_conn.close()
        postgres_conn.close()

        return True, f"✅ {len(heures)} heure(s) transférée(s) vers SQL Server"

    except Exception as e:
        return False, f"❌ Erreur lors du transfert PostgreSQL -> SQL Server : {str(e)}"

# ============================================================================
# TRANSFERT DES DEVIS BATISIMPLY -> POSTGRESQL -> SQL SERVER
# ============================================================================

def transfer_devis_batisimply_to_postgres():
    """
    Transfère les devis depuis BatiSimply vers PostgreSQL.
    """
    try:
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

        response = requests.get(
            'https://api.staging.batisimply.fr/api/quote',
            headers=headers,
            timeout=30
        )

        if response.status_code != 200:
            return False, f"❌ Erreur API BatiSimply : {response.status_code}"

        devis = response.json()

        # Insertion dans PostgreSQL avec gestion des conflits
        for devi in devis:
            id_devis = devi.get('id')
            nom = devi.get('name')
            date_creation = devi.get('creationDate')
            montant = devi.get('amount')
            statut = devi.get('status')
            code_client = devi.get('clientCode')
            
            query_postgres = """
            INSERT INTO batigest_devis (id_devis, nom, date_creation, montant, statut, code_client, sync)
            VALUES (%s, %s, %s, %s, %s, %s, FALSE)
            ON CONFLICT (id_devis) DO UPDATE SET
                nom = EXCLUDED.nom,
                date_creation = EXCLUDED.date_creation,
                montant = EXCLUDED.montant,
                statut = EXCLUDED.statut,
                code_client = EXCLUDED.code_client,
                sync = FALSE
            """
            
            postgres_cursor.execute(query_postgres, (id_devis, nom, date_creation, montant, statut, code_client))

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
            id_devis, nom, date_creation, montant, statut, code_client, sync = devi
            
            # Vérifier si le devis existe déjà dans SQL Server
            check_query = "SELECT COUNT(*) FROM dbo.Devis WHERE Code = %s"
            sqlserver_cursor.execute(check_query, (id_devis,))
            exists = sqlserver_cursor.fetchone()[0] > 0
            
            if exists:
                # Mise à jour
                update_query = """
                UPDATE dbo.Devis 
                SET Nom = %s, DateCreation = %s, Montant = %s, Statut = %s, CodeClient = %s
                WHERE Code = %s
                """
                sqlserver_cursor.execute(update_query, (nom, date_creation, montant, statut, code_client, id_devis))
            else:
                # Insertion
                insert_query = """
                INSERT INTO dbo.Devis (Code, Nom, DateCreation, Montant, Statut, CodeClient)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                sqlserver_cursor.execute(insert_query, (id_devis, nom, date_creation, montant, statut, code_client))
            
            # Marquer comme synchronisé dans PostgreSQL
            update_postgres = "UPDATE batigest_devis SET sync = TRUE WHERE id_devis = %s"
            postgres_cursor.execute(update_postgres, (id_devis,))

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
