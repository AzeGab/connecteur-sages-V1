# app/services/codial/utils.py
# Module d'utilitaires Codial
# Ce fichier contient les fonctions utilitaires pour Codial
# (initialisation des tables, vérifications, etc.)

from app.services.connex import connect_to_postgres, load_credentials

# ============================================================================
# INITIALISATION DE LA BASE DE DONNÉES CODIAL
# ============================================================================

def init_codial_postgres_table():
    """
    Initialise la table PostgreSQL pour Codial avec les colonnes nécessaires.
    
    Cette fonction :
    1. Crée la table codial_chantiers si elle n'existe pas
    2. Ajoute les colonnes de suivi des modifications si nécessaire
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

        # Création de la table codial_chantiers si elle n'existe pas
        postgres_cursor.execute("""
            CREATE TABLE IF NOT EXISTS codial_chantiers (
                id SERIAL PRIMARY KEY,
                code VARCHAR(50) UNIQUE NOT NULL,
                date_debut DATE,
                date_fin DATE,
                nom_client VARCHAR(255),
                description TEXT,
                adr_chantier VARCHAR(255),
                cp_chantier VARCHAR(10),
                ville_chantier VARCHAR(100),
                total_mo DECIMAL(10,2),
                sync BOOLEAN DEFAULT FALSE,
                sync_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Vérification de l'existence des colonnes de suivi
        postgres_cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'codial_chantiers'
        """)
        existing_columns = [row[0] for row in postgres_cursor.fetchall()]

        # Ajout des colonnes si elles n'existent pas
        if 'sync' not in existing_columns:
            postgres_cursor.execute("""
                ALTER TABLE codial_chantiers 
                ADD COLUMN sync BOOLEAN DEFAULT FALSE
            """)
            print("✅ Colonne sync ajoutée à codial_chantiers")

        if 'sync_date' not in existing_columns:
            postgres_cursor.execute("""
                ALTER TABLE codial_chantiers 
                ADD COLUMN sync_date TIMESTAMP
            """)
            print("✅ Colonne sync_date ajoutée à codial_chantiers")

        # Validation des modifications
        postgres_conn.commit()
        postgres_cursor.close()
        postgres_conn.close()

        print("✅ Table codial_chantiers initialisée avec succès")
        return True

    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation de la table Codial : {e}")
        return False
