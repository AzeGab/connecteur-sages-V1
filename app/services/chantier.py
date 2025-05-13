# app/services/chantier_service.py
# Module de gestion du transfert des chantiers
# Ce fichier contient les fonctions nécessaires pour transférer les données
# des chantiers depuis SQL Server vers PostgreSQL

import psycopg2
from app.services.connex import connect_to_sqlserver, connect_to_postgres, load_credentials

def transfer_chantiers():
    """
    Transfère les données des chantiers depuis SQL Server vers PostgreSQL.
    
    Cette fonction :
    1. Vérifie les identifiants de connexion
    2. Établit les connexions aux deux bases de données
    3. Récupère les chantiers depuis SQL Server
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

        # Récupération des chantiers depuis SQL Server
        sqlserver_cursor.execute("""
            SELECT Code, DateDebut, DateFin, NomClient, Libelle, AdrChantier, CPChantier, VilleChantier 
            FROM dbo.ChantierDef
        """)
        rows = sqlserver_cursor.fetchall()

        # Insertion des chantiers dans PostgreSQL
        for row in rows:
            code, date_debut, date_fin, nom_client, description, adr_chantier, cp_chantier, ville_chantier = row
            # Utilisation de ON CONFLICT pour éviter les doublons
            postgres_cursor.execute(
                """
                INSERT INTO batigest_chantiers 
                (code, date_debut, date_fin, nom_client, description, adr_chantier, cp_chantier, ville_chantier)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (code) DO NOTHING
                """,
                (code, date_debut, date_fin, nom_client, description, adr_chantier, cp_chantier, ville_chantier)
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
