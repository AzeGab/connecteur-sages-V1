# app/services/codial/hfsql_to_batisimply.py
# Module de gestion du flux HFSQL -> PostgreSQL -> BatiSimply
# Ce fichier contient les fonctions pour transférer les données depuis Codial (HFSQL) vers BatiSimply

import psycopg2
import requests
import json
from datetime import date, datetime
from app.services.connex import connect_to_hfsql, connect_to_postgres, load_credentials, recup_batisimply_token

# ============================================================================
# TRANSFERT DES CHANTIERS HFSQL -> POSTGRESQL -> BATISIMPLY
# ============================================================================

def transfer_chantiers_hfsql_to_postgres():
    """
    Transfère les chantiers depuis HFSQL (Codial) vers PostgreSQL.
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

        # Requête pour récupérer les chantiers depuis HFSQL (Codial)
        query_hfsql = """
        SELECT cod_projet.INT_TERMINE, cod_projet.NOM, cod_projet.DATE_DEBUT, cod_projet.DATE_FIN, 
               cod_projet.DESCRIPTION, cod_projet.REFERENCE, cod_projet.ADRESSE1_CHANTIER, 
               cod_projet.COP_CHANTIER, cod_projet.VILLE_CHANTIER, cod_projet.CODE_PAYS_CHANTIER, 
               cod_projet.CODEREP, client.NOM, meca.PRENOM, meca.NOM
        FROM cod_projet
        JOIN client ON client.CODE = cod_projet.CODE_TIERS
        JOIN meca ON meca.CODEREP = cod_projet.CODEREP
        WHERE cod_projet.INT_TERMINE = 0
        """
        
        hfsql_cursor.execute(query_hfsql)
        chantiers = hfsql_cursor.fetchall()

        # Insertion dans PostgreSQL avec gestion des conflits
        for chantier in chantiers:
            int_termine, nom, date_debut, date_fin, description, reference, adresse1_chantier, \
            cop_chantier, ville_chantier, code_pays_chantier, coderep, client_nom, meca_prenom, meca_nom = chantier
            
            # Utiliser la référence comme code unique
            code = reference if reference else f"PROJ_{coderep}"
            
            query_postgres = """
            INSERT INTO codial_chantiers (code, nom, date_debut, date_fin, description, reference, 
                                        adresse_chantier, cp_chantier, ville_chantier, code_pays_chantier, 
                                        coderep, client_nom, meca_prenom, meca_nom, statut, sync)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE)
            ON CONFLICT (code) DO UPDATE SET
                nom = EXCLUDED.nom,
                date_debut = EXCLUDED.date_debut,
                date_fin = EXCLUDED.date_fin,
                description = EXCLUDED.description,
                reference = EXCLUDED.reference,
                adresse_chantier = EXCLUDED.adresse_chantier,
                cp_chantier = EXCLUDED.cp_chantier,
                ville_chantier = EXCLUDED.ville_chantier,
                code_pays_chantier = EXCLUDED.code_pays_chantier,
                coderep = EXCLUDED.coderep,
                client_nom = EXCLUDED.client_nom,
                meca_prenom = EXCLUDED.meca_prenom,
                meca_nom = EXCLUDED.meca_nom,
                statut = EXCLUDED.statut,
                sync = FALSE
            """
            
            # Déterminer le statut basé sur INT_TERMINE
            statut = "Terminé" if int_termine == 1 else "En cours"
            
            postgres_cursor.execute(query_postgres, (
                code, nom, date_debut, date_fin, description, reference, 
                adresse1_chantier, cop_chantier, ville_chantier, code_pays_chantier,
                coderep, client_nom, meca_prenom, meca_nom, statut
            ))

        postgres_conn.commit()
        
        # Fermeture des connexions
        hfsql_cursor.close()
        postgres_cursor.close()
        hfsql_conn.close()
        postgres_conn.close()

        return True, f"[OK] {len(chantiers)} chantier(s) transféré(s) depuis HFSQL vers PostgreSQL"

    except Exception as e:
        return False, f"[ERREUR] Erreur lors du transfert HFSQL -> PostgreSQL : {str(e)}"

def transfer_chantiers_postgres_to_batisimply():
    """
    Transfère les chantiers depuis PostgreSQL vers BatiSimply.
    """
    try:
        # Vérification des identifiants
        creds = load_credentials()
        if not creds or "postgres" not in creds:
            return False, "[ERREUR] Informations de connexion manquantes"

        # Récupération du token BatiSimply
        token = recup_batisimply_token()
        if not token:
            return False, "[ERREUR] Impossible de récupérer le token BatiSimply"

        # Connexion PostgreSQL
        postgres_conn = connect_to_postgres()
        if not postgres_conn:
            return False, "[ERREUR] Connexion PostgreSQL échouée"

        postgres_cursor = postgres_conn.cursor()

        # Récupération des chantiers non synchronisés
        query = "SELECT * FROM codial_chantiers WHERE sync = FALSE"
        postgres_cursor.execute(query)
        chantiers = postgres_cursor.fetchall()

        # Envoi vers BatiSimply
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        for chantier in chantiers:
            # Récupération des données du chantier
            id, code, nom, date_debut, date_fin, description, reference, adresse_chantier, \
            cp_chantier, ville_chantier, code_pays_chantier, coderep, client_nom, \
            meca_prenom, meca_nom, statut, sync = chantier
            
            # Préparation des données pour BatiSimply
            data = {
                "name": nom,
                "startDate": date_debut.isoformat() if date_debut else None,
                "endDate": date_fin.isoformat() if date_fin else None,
                "status": statut,
                "description": description,
                "reference": reference,
                "address": adresse_chantier,
                "postalCode": cp_chantier,
                "city": ville_chantier,
                "countryCode": code_pays_chantier,
                "clientName": client_nom,
                "managerFirstName": meca_prenom,
                "managerLastName": meca_nom
            }

            # Envoi vers l'API BatiSimply
            response = requests.post(
                'https://api.staging.batisimply.fr/api/project',
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code in [200, 201]:
                # Marquer comme synchronisé
                update_query = "UPDATE codial_chantiers SET sync = TRUE WHERE code = %s"
                postgres_cursor.execute(update_query, (code,))
            else:
                print(f"[ATTENTION] Erreur lors de l'envoi du chantier {code}: {response.status_code}")

        postgres_conn.commit()
        postgres_cursor.close()
        postgres_conn.close()

        return True, f"[OK] {len(chantiers)} chantier(s) envoyé(s) vers BatiSimply"

    except Exception as e:
        return False, f"[ERREUR] Erreur lors du transfert PostgreSQL -> BatiSimply : {str(e)}"

# ============================================================================
# TRANSFERT DES HEURES HFSQL -> POSTGRESQL -> BATISIMPLY
# ============================================================================

def transfer_heures_hfsql_to_postgres():
    """
    Transfère les heures depuis HFSQL (Codial) vers PostgreSQL.
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

        # Requête pour récupérer les heures depuis HFSQL
        query_hfsql = """
        SELECT CodeChantier, CodeSalarie, Date, Heures, Commentaire
        FROM SuiviHeures
        WHERE Date >= DATEADD(day, -30, GETDATE())
        """
        
        hfsql_cursor.execute(query_hfsql)
        heures = hfsql_cursor.fetchall()

        # Insertion dans PostgreSQL avec gestion des conflits
        for heure in heures:
            code_chantier, code_salarie, date_heure, heures, commentaire = heure
            
            query_postgres = """
            INSERT INTO codial_heures (code_chantier, code_salarie, date_heure, heures, commentaire, sync)
            VALUES (%s, %s, %s, %s, %s, FALSE)
            ON CONFLICT (code_chantier, code_salarie, date_heure) DO UPDATE SET
                heures = EXCLUDED.heures,
                commentaire = EXCLUDED.commentaire,
                sync = FALSE
            """
            
            postgres_cursor.execute(query_postgres, (code_chantier, code_salarie, date_heure, heures, commentaire))

        postgres_conn.commit()
        
        # Fermeture des connexions
        hfsql_cursor.close()
        postgres_cursor.close()
        hfsql_conn.close()
        postgres_conn.close()

        return True, f"[OK] {len(heures)} heure(s) transférée(s) depuis HFSQL vers PostgreSQL"

    except Exception as e:
        return False, f"[ERREUR] Erreur lors du transfert HFSQL -> PostgreSQL : {str(e)}"

def transfer_heures_postgres_to_batisimply():
    """
    Transfère les heures depuis PostgreSQL vers BatiSimply.
    """
    try:
        # Vérification des identifiants
        creds = load_credentials()
        if not creds or "postgres" not in creds:
            return False, "[ERREUR] Informations de connexion manquantes"

        # Récupération du token BatiSimply
        token = recup_batisimply_token()
        if not token:
            return False, "[ERREUR] Impossible de récupérer le token BatiSimply"

        # Connexion PostgreSQL
        postgres_conn = connect_to_postgres()
        if not postgres_conn:
            return False, "[ERREUR] Connexion PostgreSQL échouée"

        postgres_cursor = postgres_conn.cursor()

        # Récupération des heures non synchronisées
        query = "SELECT * FROM codial_heures WHERE sync = FALSE"
        postgres_cursor.execute(query)
        heures = postgres_cursor.fetchall()

        # Envoi vers BatiSimply
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        for heure in heures:
            code_chantier, code_salarie, date_heure, heures, commentaire, sync = heure
            
            # Préparation des données pour BatiSimply
            data = {
                "projectId": code_chantier,
                "userId": code_salarie,
                "date": date_heure.isoformat(),
                "hours": float(heures),
                "comment": commentaire
            }

            # Envoi vers l'API BatiSimply
            response = requests.post(
                'https://api.staging.batisimply.fr/api/timeSlotManagement',
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code in [200, 201]:
                # Marquer comme synchronisé
                update_query = "UPDATE codial_heures SET sync = TRUE WHERE code_chantier = %s AND code_salarie = %s AND date_heure = %s"
                postgres_cursor.execute(update_query, (code_chantier, code_salarie, date_heure))
            else:
                print(f"[ATTENTION] Erreur lors de l'envoi de l'heure {code_chantier}-{code_salarie}: {response.status_code}")

        postgres_conn.commit()
        postgres_cursor.close()
        postgres_conn.close()

        return True, f"[OK] {len(heures)} heure(s) envoyée(s) vers BatiSimply"

    except Exception as e:
        return False, f"[ERREUR] Erreur lors du transfert PostgreSQL -> BatiSimply : {str(e)}"

# ============================================================================
# FONCTIONS DE SYNCHRONISATION COMPLÈTE
# ============================================================================

def sync_hfsql_to_batisimply():
    """
    Synchronisation complète HFSQL -> PostgreSQL -> BatiSimply.
    """
    print("=== DÉBUT DE LA SYNCHRONISATION HFSQL -> BATISIMPLY ===")
    messages = []
    overall_success = True
    
    try:
        # 1. Transfert des chantiers
        print("[SYNC] Synchronisation des chantiers...")
        success, message = transfer_chantiers_hfsql_to_postgres()
        print(message)
        messages.append(message)
        
        if success:
            success, message = transfer_chantiers_postgres_to_batisimply()
            print(message)
            messages.append(message)
            if not success:
                overall_success = False
        else:
            overall_success = False
        
        # 2. Transfert des heures
        print("[SYNC] Synchronisation des heures...")
        success, message = transfer_heures_hfsql_to_postgres()
        print(message)
        messages.append(message)
        
        if success:
            success, message = transfer_heures_postgres_to_batisimply()
            print(message)
            messages.append(message)
            if not success:
                overall_success = False
        else:
            overall_success = False
        
        print("=== FIN DE LA SYNCHRONISATION HFSQL -> BATISIMPLY ===")
        
        if overall_success:
            return True, "[OK] Synchronisation HFSQL -> BatiSimply terminée avec succès"
        else:
            return False, "[ATTENTION] Synchronisation HFSQL -> BatiSimply terminée avec des erreurs"
            
    except Exception as e:
        error_msg = f"[ERREUR] Erreur lors de la synchronisation HFSQL -> BatiSimply : {str(e)}"
        print(error_msg)
        return False, error_msg
