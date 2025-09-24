"""
Utilitaires pour les services Batigest.
"""

from app.services.connex import connect_to_postgres, load_credentials

def init_batigest_tables():
    """
    Initialise les tables PostgreSQL avec les colonnes exactes des images fournies.
    
    Cette fonction :
    1. Crée la table batigest_chantiers si elle n'existe pas
    2. Crée la table batigest_heures si elle n'existe pas
    3. Crée la table batigest_devis si elle n'existe pas
    4. Crée la table batigest_heures_map pour le mapping des heures
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

        # Création de la table batigest_chantiers (structure exacte de l'image)
        postgres_cursor.execute("""
            CREATE TABLE IF NOT EXISTS batigest_chantiers (
                id SERIAL PRIMARY KEY,
                code VARCHAR(50) UNIQUE,
                date_debut DATE,
                date_fin DATE,
                nom_client VARCHAR(100),
                description VARCHAR(200),
                adr_chantier TEXT,
                cp_chantier VARCHAR(10),
                ville_chantier VARCHAR(45),
                sync_date TIMESTAMP,
                sync BOOLEAN DEFAULT FALSE,
                total_mo REAL,
                last_modified_batisimply TIMESTAMP WITH TIME ZONE,
                last_modified_batigest TIMESTAMP WITH TIME ZONE
            )
        """)

        # Création de la table batigest_heures (structure exacte de l'image)
        postgres_cursor.execute("""
            CREATE TABLE IF NOT EXISTS batigest_heures (
                id SERIAL PRIMARY KEY,
                id_heure VARCHAR(50) UNIQUE,
                date_debut TIMESTAMP NOT NULL,
                date_fin TIMESTAMP NOT NULL,
                id_utilisateur UUID NOT NULL,
                id_projet INTEGER,
                status_management VARCHAR(50),
                total_heure NUMERIC(5,2),
                panier BOOLEAN,
                trajet BOOLEAN,
                code_projet VARCHAR(100),
                sync BOOLEAN DEFAULT FALSE
            )
        """)

        # Création de la table batigest_devis (structure exacte de l'image)
        postgres_cursor.execute("""
            CREATE TABLE IF NOT EXISTS batigest_devis (
                code VARCHAR(50) PRIMARY KEY,
                date DATE,
                nom VARCHAR(100),
                adr TEXT,
                cp VARCHAR(10),
                ville VARCHAR(100),
                sujet TEXT,
                dateconcretis DATE,
                tempsmo REAL,
                sync_date TIMESTAMP,
                sync BOOLEAN DEFAULT FALSE
            )
        """)

        # Création de la table batigest_heures_map (structure exacte de l'image)
        postgres_cursor.execute("""
            CREATE TABLE IF NOT EXISTS batigest_heures_map (
                id_heure VARCHAR PRIMARY KEY,
                code_chantier VARCHAR NOT NULL,
                code_salarie VARCHAR NOT NULL,
                date_sqlserver TIMESTAMP NOT NULL
            )
        """)

        # Validation des modifications
        postgres_conn.commit()
        postgres_cursor.close()
        postgres_conn.close()

        print("✅ Tables Batigest initialisées avec succès")
        return True

    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation de la table : {e}")
        return False

def check_batigest_connection():
    """
    Vérifie la connexion aux bases de données Batigest.
    """
    try:
        creds = load_credentials()
        if not creds:
            return False, "❌ Aucune configuration trouvée"

        # Vérification PostgreSQL
        if "postgres" not in creds:
            return False, "❌ Configuration PostgreSQL manquante"

        pg = creds["postgres"]
        postgres_conn = connect_to_postgres(
            pg["host"], pg["user"], pg["password"], pg["database"], pg.get("port", "5432")
        )
        
        if not postgres_conn:
            return False, "❌ Connexion PostgreSQL échouée"

        postgres_conn.close()
        return True, "✅ Connexion Batigest réussie"

    except Exception as e:
        return False, f"❌ Erreur de connexion Batigest : {str(e)}"