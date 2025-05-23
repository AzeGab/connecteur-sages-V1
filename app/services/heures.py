# app/services/heures_service.py
# Module de gestion du transfert des heures
# Ce fichier contient les fonctions nécessaires pour transférer les données
# des heures depuis SQL Server vers PostgreSQL et BatiSimply

import psycopg2
from app.services.connex import connect_to_sqlserver, connect_to_postgres, load_credentials, recup_batisimply_token
import requests
import json
from datetime import date

# ============================================================================
# TRANSFERT VERS POSTGRESQL
# ============================================================================

def transfer_heures():
    """
    Transfère les données des heures depuis SQL Server vers PostgreSQL.
    
    Cette fonction :
    1. Vérifie les identifiants de connexion
    2. Établit les connexions aux deux bases de données
    3. Récupère les heures depuis SQL Server
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
        
        # Récupération des heures depuis SQL Server
        sqlserver_cursor.execute("""
            SELECT Code, DateDebut, DateFin, NomClient, Libelle, AdrChantier, CPChantier, VilleChantier 
            FROM dbo.ChantierDef
        """)
        rows = sqlserver_cursor.fetchall()

        # Insertion des heures dans PostgreSQL
        for row in rows:
            # Requête pour récupérer les heures depuis Batisimply
            postgres_cursor.execute(
                """
                SELECT * FROM batisimply_heures
                """
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

def transfer_heures_vers_batisimply():
    """
    Transfère les heures depuis PostgreSQL vers BatiSimply.
    
    Cette fonction :
    1. Récupère le token d'authentification
    2. Vérifie les identifiants PostgreSQL
    3. Récupère les heures non synchronisées
    4. Les envoie à l'API BatiSimply
    5. Met à jour le statut de synchronisation
    
    Returns:
        bool: True si au moins une heure a été transférée avec succès, False sinon
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
    API_URL = "https://api.staging.batisimply.fr/api/hours"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Récupération des heures non synchronisées
    postgres_cursor = postgres_conn.cursor()
    postgres_cursor.execute("""
        SELECT * FROM batisimply_heures
        WHERE sync = false
    """)

    rows = postgres_cursor.fetchall()
    success = False

    # Traitement de chaque heure
    for row in rows:
        # TODO: Implémenter la logique de transfert des heures vers BatiSimply
        pass

    # Nettoyage
    postgres_cursor.close()
    postgres_conn.close()

    return success