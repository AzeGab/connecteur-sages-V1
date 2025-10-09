# app/services/codial/utils.py
# Module d'utilitaires Codial
# Ce fichier contient les fonctions utilitaires pour Codial
# (initialisation des tables, vérifications, etc.)

from app.services.connex import connect_to_postgres, load_credentials

# ============================================================================
# INITIALISATION DE LA BASE DE DONNÉES CODIAL
# ============================================================================

def init_codial_tables():
    """
    Initialise les tables PostgreSQL pour Codial avec les colonnes nécessaires.
    
    Cette fonction :
    1. Crée la table codial_chantiers si elle n'existe pas
    2. Crée la table codial_heures si elle n'existe pas
    3. Crée la table codial_heures_map pour le mapping des heures
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
                id_projet INTEGER UNIQUE,
                code VARCHAR(50) UNIQUE,
                nom VARCHAR(255),
                date_debut DATE,
                date_fin DATE,
                description TEXT,
                reference VARCHAR(100),
                adresse_chantier VARCHAR(255),
                cp_chantier VARCHAR(10),
                ville_chantier VARCHAR(100),
                code_pays_chantier VARCHAR(10),
                coderep VARCHAR(50),
                client_nom VARCHAR(255),
                meca_prenom VARCHAR(100),
                meca_nom VARCHAR(100),
                statut VARCHAR(50),
                sync BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Création de la table codial_heures si elle n'existe pas
        postgres_cursor.execute("""
            CREATE TABLE IF NOT EXISTS codial_heures (
                id SERIAL PRIMARY KEY,
                id_heure VARCHAR(255) UNIQUE,
                id_projet INTEGER,
                id_utilisateur VARCHAR(255),
                code_chantier VARCHAR(50),
                code_salarie VARCHAR(50),
                date_heure DATE,
                date_debut TIMESTAMP,
                date_fin TIMESTAMP,
                heures DECIMAL(5,2),
                commentaire TEXT,
                sync BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Création de la table codial_heures_map pour le mapping des heures
        postgres_cursor.execute("""
            CREATE TABLE IF NOT EXISTS codial_heures_map (
                id_heure VARCHAR(255) PRIMARY KEY,
                code_chantier VARCHAR(50) NOT NULL,
                code_salarie VARCHAR(50) NOT NULL,
                date_hfsql TIMESTAMP NOT NULL
            )
        """)

        # Validation des modifications
        postgres_conn.commit()
        postgres_cursor.close()
        postgres_conn.close()

        print("✅ Tables Codial initialisées avec succès")
        return True

    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation de la table Codial : {e}")
        return False

def check_codial_connection():
    """
    Vérifie la connexion à la base de données HFSQL (Codial).
    """
    try:
        from app.services.connex import connect_to_hfsql
        
        hfsql_conn = connect_to_hfsql()
        if hfsql_conn:
            hfsql_conn.close()
            return True, "✅ Connexion HFSQL (Codial) réussie"
        else:
            return False, "❌ Connexion HFSQL (Codial) échouée"
            
    except Exception as e:
        return False, f"❌ Erreur de connexion HFSQL (Codial) : {str(e)}"
