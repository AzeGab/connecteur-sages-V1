#!/usr/bin/env python3
# Script de configuration du système de licences
# Ce script aide à configurer la base de données PostgreSQL

import json
import os
import sys
from pathlib import Path

def create_credentials_file():
    """Crée le fichier de configuration des identifiants."""
    credentials_file = Path("app/services/credentials.json")
    
    if credentials_file.exists():
        print("✅ Le fichier credentials.json existe déjà")
        return True
    
    print("🔧 Configuration de la base de données PostgreSQL")
    print("=" * 50)
    
    # Demander les informations de connexion
    host = input("Host PostgreSQL (localhost): ").strip() or "localhost"
    port = input("Port PostgreSQL (5432): ").strip() or "5432"
    user = input("Utilisateur PostgreSQL: ").strip()
    password = input("Mot de passe PostgreSQL: ").strip()
    database = input("Nom de la base de données: ").strip()
    
    if not user or not password or not database:
        print("❌ Toutes les informations sont requises")
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
    
    # Créer le répertoire si nécessaire
    credentials_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Sauvegarder la configuration
    try:
        with open(credentials_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print("✅ Fichier credentials.json créé avec succès")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la création du fichier: {e}")
        return False

def test_database_connection():
    """Teste la connexion à la base de données."""
    try:
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
        
        if conn:
            print("✅ Connexion à PostgreSQL réussie")
            conn.close()
            return True
        else:
            print("❌ Échec de connexion à PostgreSQL")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test de connexion: {e}")
        return False

def setup_database():
    """Configure la base de données pour les licences."""
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
            print("✅ Table licenses créée avec succès")
            return True
        else:
            print("❌ Échec de création de la table licenses")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la configuration de la base: {e}")
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
            print("❌ Échec de création de la licence d'exemple")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la création de la licence: {e}")
        return False

def main():
    """Fonction principale de configuration."""
    print("🔧 Configuration du système de licences")
    print("=" * 50)
    
    # Étape 1: Créer le fichier de configuration
    if not create_credentials_file():
        return
    
    # Étape 2: Tester la connexion
    if not test_database_connection():
        print("\n💡 Vérifiez que:")
        print("   - PostgreSQL est démarré")
        print("   - Les identifiants sont corrects")
        print("   - La base de données existe")
        return
    
    # Étape 3: Configurer la base de données
    if not setup_database():
        return
    
    # Étape 4: Créer une licence d'exemple
    create_sample = input("\nCréer une licence d'exemple ? (o/n): ").strip().lower()
    if create_sample in ['o', 'oui', 'y', 'yes']:
        create_sample_license()
    
    print("\n🎉 Configuration terminée !")
    print("\n📋 Prochaines étapes:")
    print("   1. Démarrez l'application: python -m uvicorn app.main:app --reload")
    print("   2. Accédez à l'interface: http://localhost:8000/licenses/")
    print("   3. Testez le système: python test_licenses.py")

if __name__ == "__main__":
    main() 