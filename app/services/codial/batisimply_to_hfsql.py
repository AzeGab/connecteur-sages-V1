# app/services/codial/batisimply_to_hfsql.py
# Module de gestion du flux BatiSimply -> PostgreSQL -> HFSQL (Codial)
# Ce fichier contient les fonctions pour transférer les données depuis BatiSimply vers Codial (HFSQL)

import psycopg2
import requests
import json
from datetime import date, datetime, timedelta
from app.services.connex import connect_to_hfsql, connect_to_postgres, load_credentials, recup_batisimply_token

# ============================================================================
# TRANSFERT DES CHANTIERS BATISIMPLY -> POSTGRESQL -> HFSQL
# ============================================================================

def transfer_chantiers_batisimply_to_postgres():
    """
    Transfère les chantiers depuis BatiSimply vers PostgreSQL.
    """
    try:
        # Récupération du token BatiSimply
        token = recup_batisimply_token()
        if not token:
            return False, "[ERREUR] Impossible de récupérer le token BatiSimply"

        # Connexion PostgreSQL
        postgres_conn = connect_to_postgres()
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
            INSERT INTO codial_chantiers (id_projet, nom, date_debut, date_fin, statut, code_client, sync)
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

        return True, f"[OK] {len(chantiers)} chantier(s) transféré(s) depuis BatiSimply vers PostgreSQL"

    except Exception as e:
        return False, f"[ERREUR] Erreur lors du transfert BatiSimply -> PostgreSQL : {str(e)}"

def transfer_chantiers_postgres_to_hfsql():
    """
    Transfère les chantiers depuis PostgreSQL vers HFSQL (Codial).
    """
    try:
        # Vérification des identifiants
        creds = load_credentials()
        if not creds or "hfsql" not in creds or "postgres" not in creds:
            return False, "[ERREUR] Informations de connexion manquantes"

        # Établissement des connexions
        hfsql_conn = connect_to_hfsql(
            creds["hfsql"]["host"],
            creds["hfsql"].get("user", "admin"),
            creds["hfsql"].get("password", ""),
            creds["hfsql"].get("database", "HFSQL"),
            creds["hfsql"].get("port", "4900")
        )
        postgres_conn = connect_to_postgres(
            creds["postgres"]["host"],
            creds["postgres"]["user"],
            creds["postgres"]["password"],
            creds["postgres"]["database"],
            creds["postgres"].get("port", "5432")
        )
        
        if not hfsql_conn or not postgres_conn:
            return False, "[ERREUR] Connexion aux bases échouée"

        # Création des curseurs
        hfsql_cursor = hfsql_conn.cursor()
        postgres_cursor = postgres_conn.cursor()

        # Récupération des chantiers non synchronisés
        query = "SELECT * FROM codial_chantiers WHERE sync = FALSE"
        postgres_cursor.execute(query)
        chantiers = postgres_cursor.fetchall()

        # Insertion dans HFSQL
        for chantier in chantiers:
            id, id_projet, code, nom, date_debut, date_fin, description, reference, adresse_chantier, \
            cp_chantier, ville_chantier, code_pays_chantier, coderep, client_nom, \
            meca_prenom, meca_nom, statut, sync = chantier
            
            # Vérifier si le chantier existe déjà dans HFSQL
            check_query = "SELECT COUNT(*) FROM cod_projet WHERE REFERENCE = %s"
            hfsql_cursor.execute(check_query, (reference,))
            exists = hfsql_cursor.fetchone()[0] > 0
            
            # Déterminer INT_TERMINE basé sur le statut
            int_termine = 1 if statut == "Terminé" else 0
            
            if exists:
                # Mise à jour
                update_query = """
                UPDATE cod_projet 
                SET NOM = %s, DATE_DEBUT = %s, DATE_FIN = %s, DESCRIPTION = %s, 
                    ADRESSE1_CHANTIER = %s, COP_CHANTIER = %s, VILLE_CHANTIER = %s, 
                    CODE_PAYS_CHANTIER = %s, INT_TERMINE = %s
                WHERE REFERENCE = %s
                """
                hfsql_cursor.execute(update_query, (
                    nom, date_debut, date_fin, description, adresse_chantier, 
                    cp_chantier, ville_chantier, code_pays_chantier, int_termine, reference
                ))
            else:
                # Insertion (nécessite des valeurs par défaut pour les champs obligatoires)
                insert_query = """
                INSERT INTO cod_projet (REFERENCE, NOM, DATE_DEBUT, DATE_FIN, DESCRIPTION, 
                                      ADRESSE1_CHANTIER, COP_CHANTIER, VILLE_CHANTIER, 
                                      CODE_PAYS_CHANTIER, CODEREP, INT_TERMINE)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                hfsql_cursor.execute(insert_query, (
                    reference, nom, date_debut, date_fin, description, adresse_chantier, 
                    cp_chantier, ville_chantier, code_pays_chantier, coderep, int_termine
                ))
            
            # Marquer comme synchronisé dans PostgreSQL
            update_postgres = "UPDATE codial_chantiers SET sync = TRUE WHERE id = %s"
            postgres_cursor.execute(update_postgres, (id,))

        hfsql_conn.commit()
        postgres_conn.commit()
        
        # Fermeture des connexions
        hfsql_cursor.close()
        postgres_cursor.close()
        hfsql_conn.close()
        postgres_conn.close()

        return True, f"[OK] {len(chantiers)} chantier(s) transféré(s) vers HFSQL"

    except Exception as e:
        return False, f"[ERREUR] Erreur lors du transfert PostgreSQL -> HFSQL : {str(e)}"

# ============================================================================
# TRANSFERT DES HEURES BATISIMPLY -> POSTGRESQL -> HFSQL
# ============================================================================

def transfer_heures_batisimply_to_postgres():
    """
    Transfère les heures depuis BatiSimply vers PostgreSQL.
    """
    try:
        # Récupération du token BatiSimply
        token = recup_batisimply_token()
        if not token:
            return False, "[ERREUR] Impossible de récupérer le token BatiSimply"

        # Connexion PostgreSQL
        postgres_conn = connect_to_postgres()
        if not postgres_conn:
            return False, "[ERREUR] Connexion PostgreSQL échouée"

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
            return False, f"[ERREUR] Erreur API BatiSimply : {response.status_code}"

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
            INSERT INTO codial_heures (id_heure, id_projet, id_utilisateur, date_debut, date_fin, heures, commentaire, sync)
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

        return True, f"[OK] {len(heures)} heure(s) transférée(s) depuis BatiSimply vers PostgreSQL"

    except Exception as e:
        return False, f"[ERREUR] Erreur lors du transfert BatiSimply -> PostgreSQL : {str(e)}"

def transfer_heures_postgres_to_hfsql():
    """
    Transfère les heures depuis PostgreSQL vers HFSQL (Codial).
    """
    try:
        # Vérification des identifiants
        creds = load_credentials()
        if not creds or "hfsql" not in creds or "postgres" not in creds:
            return False, "[ERREUR] Informations de connexion manquantes"

        # Établissement des connexions
        hfsql_conn = connect_to_hfsql(
            creds["hfsql"]["host"],
            creds["hfsql"].get("user", "admin"),
            creds["hfsql"].get("password", ""),
            creds["hfsql"].get("database", "HFSQL"),
            creds["hfsql"].get("port", "4900")
        )
        postgres_conn = connect_to_postgres(
            creds["postgres"]["host"],
            creds["postgres"]["user"],
            creds["postgres"]["password"],
            creds["postgres"]["database"],
            creds["postgres"].get("port", "5432")
        )
        
        if not hfsql_conn or not postgres_conn:
            return False, "[ERREUR] Connexion aux bases échouée"

        # Création des curseurs
        hfsql_cursor = hfsql_conn.cursor()
        postgres_cursor = postgres_conn.cursor()

        # Récupération des heures non synchronisées
        query = "SELECT * FROM codial_heures WHERE sync = FALSE"
        postgres_cursor.execute(query)
        heures = postgres_cursor.fetchall()

        # Insertion dans HFSQL
        for heure in heures:
            id_heure, id_projet, id_utilisateur, date_debut, date_fin, heures_travaillees, commentaire, sync = heure
            
            # Vérifier si l'heure existe déjà dans HFSQL
            check_query = "SELECT COUNT(*) FROM SuiviHeures WHERE CodeChantier = %s AND CodeSalarie = %s AND Date = %s"
            hfsql_cursor.execute(check_query, (id_projet, id_utilisateur, date_debut.date()))
            exists = hfsql_cursor.fetchone()[0] > 0
            
            if exists:
                # Mise à jour
                update_query = """
                UPDATE SuiviHeures 
                SET Heures = %s, Commentaire = %s
                WHERE CodeChantier = %s AND CodeSalarie = %s AND Date = %s
                """
                hfsql_cursor.execute(update_query, (heures_travaillees, commentaire, id_projet, id_utilisateur, date_debut.date()))
            else:
                # Insertion
                insert_query = """
                INSERT INTO SuiviHeures (CodeChantier, CodeSalarie, Date, Heures, Commentaire)
                VALUES (%s, %s, %s, %s, %s)
                """
                hfsql_cursor.execute(insert_query, (id_projet, id_utilisateur, date_debut.date(), heures_travaillees, commentaire))
            
            # Marquer comme synchronisé dans PostgreSQL
            update_postgres = "UPDATE codial_heures SET sync = TRUE WHERE id_heure = %s"
            postgres_cursor.execute(update_postgres, (id_heure,))

        hfsql_conn.commit()
        postgres_conn.commit()
        
        # Fermeture des connexions
        hfsql_cursor.close()
        postgres_cursor.close()
        hfsql_conn.close()
        postgres_conn.close()

        return True, f"[OK] {len(heures)} heure(s) transférée(s) vers HFSQL"

    except Exception as e:
        return False, f"[ERREUR] Erreur lors du transfert PostgreSQL -> HFSQL : {str(e)}"

# ============================================================================
# FONCTIONS DE SYNCHRONISATION COMPLÈTE
# ============================================================================

def sync_batisimply_to_hfsql():
    """
    Synchronisation complète BatiSimply -> PostgreSQL -> HFSQL.
    """
    print("=== DÉBUT DE LA SYNCHRONISATION BATISIMPLY -> HFSQL ===")
    messages = []
    overall_success = True
    
    try:
        # 1. Transfert des chantiers
        print("[SYNC] Synchronisation des chantiers...")
        success, message = transfer_chantiers_batisimply_to_postgres()
        print(message)
        messages.append(message)
        
        if success:
            success, message = transfer_chantiers_postgres_to_hfsql()
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
            success, message = transfer_heures_postgres_to_hfsql()
            print(message)
            messages.append(message)
            if not success:
                overall_success = False
        else:
            overall_success = False
        
        print("=== FIN DE LA SYNCHRONISATION BATISIMPLY -> HFSQL ===")
        
        if overall_success:
            return True, "[OK] Synchronisation BatiSimply -> HFSQL terminée avec succès"
        else:
            return False, "[ATTENTION] Synchronisation BatiSimply -> HFSQL terminée avec des erreurs"
            
    except Exception as e:
        error_msg = f"[ERREUR] Erreur lors de la synchronisation BatiSimply -> HFSQL : {str(e)}"
        print(error_msg)
        return False, error_msg
