#!/usr/bin/env python3
# Script de test PostgreSQL simple

import psycopg2
import sys

def test_postgresql_connection():
    """Test simple de connexion PostgreSQL."""
    
    print("🔍 Test de connexion PostgreSQL")
    print("=" * 40)
    
    # Paramètres de test
    host = "localhost"
    port = "5432"
    user = "postgres"
    password = "admin"  # Changez selon votre configuration
    database = "licences"  # Changez selon votre configuration
    
    print(f"Tentative de connexion à {host}:{port}")
    print(f"Utilisateur: {user}")
    print(f"Base de données: {database}")
    
    try:
        # Test de connexion
        conn = psycopg2.connect(
            host=host,
            dbname=database,
            user=user,
            password=password,
            port=port
        )
        
        print("✅ Connexion PostgreSQL réussie !")
        
        # Test de requête simple
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Version PostgreSQL: {version[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Erreur de connexion: {e}")
        print("\n💡 Solutions possibles:")
        print("1. Vérifiez que PostgreSQL est démarré")
        print("2. Vérifiez le mot de passe")
        print("3. Vérifiez que la base de données existe")
        return False
        
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

def create_database_if_not_exists():
    """Crée la base de données si elle n'existe pas."""
    
    print("\n🔧 Création de la base de données si nécessaire")
    print("=" * 50)
    
    try:
        # Connexion à la base postgres par défaut
        conn = psycopg2.connect(
            host="localhost",
            dbname="postgres",
            user="postgres",
            password="admin",  # Changez selon votre configuration
            port="5432"
        )
        
        # Désactiver l'autocommit pour permettre CREATE DATABASE
        conn.autocommit = True
        
        cursor = conn.cursor()
        
        # Vérifier si la base existe
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'licences';")
        exists = cursor.fetchone()
        
        if not exists:
            print("📝 Création de la base de données 'licences'...")
            cursor.execute("CREATE DATABASE licences;")
            print("✅ Base de données 'licences' créée")
        else:
            print("✅ Base de données 'licences' existe déjà")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de la base: {e}")
        return False

def main():
    """Fonction principale."""
    
    # Étape 1: Créer la base si nécessaire
    if not create_database_if_not_exists():
        print("❌ Impossible de créer la base de données")
        return
    
    # Étape 2: Tester la connexion
    if test_postgresql_connection():
        print("\n🎉 PostgreSQL est correctement configuré !")
        print("Vous pouvez maintenant exécuter: python configure_postgresql.py")
    else:
        print("\n❌ Problème avec PostgreSQL")
        print("Vérifiez l'installation et la configuration")

if __name__ == "__main__":
    main() 