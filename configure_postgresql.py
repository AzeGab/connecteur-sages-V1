#!/usr/bin/env python3
# Script de configuration PostgreSQL manuel

import json
import os
from pathlib import Path

def create_postgresql_config():
    """Crée la configuration PostgreSQL manuellement."""
    
    print("🔧 Configuration PostgreSQL pour le système de licences")
    print("=" * 60)
    
    # Demander les informations de connexion
    print("Veuillez entrer les informations de connexion PostgreSQL :")
    host = input("Host (localhost): ").strip() or "localhost"
    port = input("Port (5432): ").strip() or "5432"
    user = input("Utilisateur (postgres): ").strip() or "postgres"
    password = input("Mot de passe: ").strip()
    database = input("Base de données (connecteur_licenses): ").strip() or "connecteur_licenses"
    
    if not password:
        print("❌ Le mot de passe est obligatoire")
        return False
    
    # Créer la configuration
    config = {
        "postgresql": {
            "host": host,
            "user": user,
            "password": password,
            "database": database,
            "port": port
        }
    }
    
    # Chemin du fichier
    credentials_file = Path("app/services/credentials.json")
    
    # Créer le répertoire si nécessaire
    credentials_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Sauvegarder la configuration
    try:
        with open(credentials_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"✅ Configuration sauvegardée dans {credentials_file}")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        return False

def test_connection():
    """Teste la connexion PostgreSQL."""
    try:
        from app.services.connex import connect_to_postgres, load_credentials
        
        creds = load_credentials()
        if not creds or 'postgresql' not in creds:
            print("❌ Configuration PostgreSQL manquante")
            return False
        
        pg_creds = creds['postgresql']
        print(f"🔍 Test de connexion à {pg_creds['host']}:{pg_creds['port']}...")
        
        conn = connect_to_postgres(
            pg_creds['host'],
            pg_creds['user'],
            pg_creds['password'],
            pg_creds['database'],
            pg_creds.get('port', '5432')
        )
        
        if conn:
            print("✅ Connexion PostgreSQL réussie !")
            conn.close()
            return True
        else:
            print("❌ Échec de connexion PostgreSQL")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def setup_database():
    """Configure la base de données."""
    try:
        from app.services.licences import create_licenses_table
        from app.services.connex import connect_to_postgres, load_credentials
        
        creds = load_credentials()
        if not creds or 'postgresql' not in creds:
            print("❌ Configuration PostgreSQL manquante")
            return False
        
        pg_creds = creds['postgresql']
        conn = connect_to_postgres(
            pg_creds['host'],
            pg_creds['user'],
            pg_creds['password'],
            pg_creds['database'],
            pg_creds.get('port', '5432')
        )
        
        if not conn:
            print("❌ Impossible de se connecter à PostgreSQL")
            return False
        
        # Créer la table licenses
        success = create_licenses_table(conn)
        conn.close()
        
        if success:
            print("✅ Table 'licenses' créée avec succès")
            return True
        else:
            print("❌ Échec de création de la table")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la configuration: {e}")
        return False

def create_sample_license():
    """Crée une licence d'exemple."""
    try:
        from app.services.licences import add_license
        from app.services.connex import connect_to_postgres, load_credentials
        
        creds = load_credentials()
        if not creds or 'postgresql' not in creds:
            print("❌ Configuration PostgreSQL manquante")
            return False
        
        pg_creds = creds['postgresql']
        conn = connect_to_postgres(
            pg_creds['host'],
            pg_creds['user'],
            pg_creds['password'],
            pg_creds['database'],
            pg_creds.get('port', '5432')
        )
        
        if not conn:
            print("❌ Impossible de se connecter à PostgreSQL")
            return False
        
        # Créer une licence d'exemple
        license_key = add_license(
            conn=conn,
            client_name="Client Test",
            client_email="test@example.com",
            company_name="Entreprise Test",
            duration_days=30,
            max_usage=100,
            notes="Licence d'exemple pour les tests"
        )
        
        conn.close()
        
        if license_key:
            print(f"✅ Licence d'exemple créée: {license_key}")
            return True
        else:
            print("❌ Échec de création de la licence")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la création: {e}")
        return False

def main():
    """Fonction principale."""
    print("🔧 Configuration PostgreSQL pour le système de licences")
    print("=" * 60)
    
    # Étape 1: Créer la configuration
    if not create_postgresql_config():
        return
    
    print("\n" + "=" * 60)
    
    # Étape 2: Tester la connexion
    if not test_connection():
        print("\n💡 Vérifiez que:")
        print("   - PostgreSQL est installé et démarré")
        print("   - Les identifiants sont corrects")
        print("   - La base de données existe")
        print("   - L'utilisateur a les droits nécessaires")
        return
    
    # Étape 3: Configurer la base de données
    if not setup_database():
        return
    
    # Étape 4: Créer une licence d'exemple
    create_sample = input("\nCréer une licence d'exemple ? (o/n): ").strip().lower()
    if create_sample in ['o', 'oui', 'y', 'yes']:
        create_sample_license()
    
    print("\n🎉 Configuration PostgreSQL terminée !")
    print("Vous pouvez maintenant démarrer l'application avec: python -m uvicorn app.main:app --reload")

if __name__ == "__main__":
    main() 