# app/services/batigest/utils.py
# Module d'utilitaires Batigest
# Ce fichier contient les fonctions utilitaires pour Batigest
# (initialisation des tables, vérifications, etc.)

from app.services.connex import connect_to_postgres, load_credentials

# ============================================================================
# INITIALISATION DE LA BASE DE DONNÉES
# ============================================================================

def init_postgres_table():
    """
    Initialise la table PostgreSQL avec les colonnes nécessaires pour le suivi des modifications.
    
    Cette fonction :
    1. Vérifie si les colonnes de dates de modification existent
    2. Les ajoute si elles n'existent pas
    3. Met à jour les dates existantes si nécessaire
    """
    try:
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

        postgres_cursor = postgres_conn.cursor()

        # Vérification de l'existence des colonnes
        postgres_cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'batigest_chantiers'
        """)
        existing_columns = [row[0] for row in postgres_cursor.fetchall()]

        # Ajout des colonnes si elles n'existent pas
        if 'sync' not in existing_columns:
            postgres_cursor.execute("""
                ALTER TABLE batigest_chantiers 
                ADD COLUMN sync BOOLEAN
            """)
            print("✅ Colonne sync ajoutée")

        # Validation des modifications
        postgres_conn.commit()
        postgres_cursor.close()
        postgres_conn.close()

        return True

    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation de la table : {e}")
        return False
