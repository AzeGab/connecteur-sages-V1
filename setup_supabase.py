#!/usr/bin/env python3
"""
Script de configuration Supabase pour le système de licences
Ce script aide à configurer Supabase pour le système de licences
"""

import os
import sys
import json
from pathlib import Path

# Ajouter le répertoire app au path
sys.path.append(str(Path(__file__).parent / "app"))

from app.services.supabase_licences import setup_supabase_config, get_supabase_client, add_license

def main():
    """
    Fonction principale du script de configuration.
    """
    print("🚀 Configuration Supabase pour le système de licences")
    print("=" * 60)
    
    # Vérifier les variables d'environnement
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Variables d'environnement manquantes")
        print("\nVeuillez définir les variables suivantes :")
        print("  - SUPABASE_URL=https://your-project.supabase.co")
        print("  - SUPABASE_KEY=your-anon-key")
        print("\nVous pouvez les définir dans un fichier .env ou comme variables système.")
        return False
    
    print(f"✅ URL Supabase : {supabase_url}")
    print(f"✅ Clé Supabase : {supabase_key[:10]}...")
    
    # Tester la connexion Supabase
    print("\n🔗 Test de connexion à Supabase...")
    supabase = get_supabase_client()
    
    if not supabase:
        print("❌ Impossible de se connecter à Supabase")
        print("Vérifiez vos variables d'environnement et votre connexion internet.")
        return False
    
    print("✅ Connexion à Supabase réussie")
    
    # Afficher les instructions de configuration
    print("\n📋 Instructions de configuration :")
    setup_supabase_config()
    
    # Demander si l'utilisateur veut créer une licence de test
    print("\n" + "=" * 60)
    create_test = input("\nVoulez-vous créer une licence de test ? (o/n) : ").lower().strip()
    
    if create_test in ['o', 'oui', 'y', 'yes']:
        print("\n🔑 Création d'une licence de test...")
        
        try:
            license_key = add_license(
                client_name="Client Test",
                client_email="test@example.com",
                company_name="Entreprise Test",
                duration_days=30,
                max_usage=100,
                notes="Licence de test créée automatiquement"
            )
            
            if license_key:
                print(f"✅ Licence de test créée avec succès !")
                print(f"🔑 Clé de licence : {license_key}")
                print(f"📧 Email : test@example.com")
                print(f"⏰ Durée : 30 jours")
                print(f"🔢 Utilisations max : 100")
            else:
                print("❌ Erreur lors de la création de la licence de test")
                print("Vérifiez que la table 'licenses' a été créée dans Supabase.")
                
        except Exception as e:
            print(f"❌ Erreur lors de la création de la licence : {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Configuration terminée !")
    print("\nProchaines étapes :")
    print("1. Vérifiez que la table 'licenses' existe dans votre projet Supabase")
    print("2. Testez l'application avec : python -m uvicorn app.main:app --reload")
    print("3. Accédez à l'interface de gestion : http://localhost:8000/licenses/")
    
    return True

def create_env_file():
    """
    Crée un fichier .env avec les variables Supabase.
    """
    env_content = """# Configuration Supabase
# Remplacez ces valeurs par vos vraies clés Supabase

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Autres variables d'environnement
SECRET_KEY=connecteur-sages-v1-secret-key-2024
"""
    
    env_file = Path(".env")
    if env_file.exists():
        print("⚠️  Le fichier .env existe déjà")
        overwrite = input("Voulez-vous l'écraser ? (o/n) : ").lower().strip()
        if overwrite not in ['o', 'oui', 'y', 'yes']:
            return False
    
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print(f"✅ Fichier .env créé : {env_file.absolute()}")
        print("📝 Veuillez modifier ce fichier avec vos vraies clés Supabase")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la création du fichier .env : {e}")
        return False

def install_dependencies():
    """
    Installe les dépendances nécessaires pour Supabase.
    """
    print("📦 Installation des dépendances Supabase...")
    
    try:
        import subprocess
        import sys
        
        # Liste des packages à installer
        packages = [
            "supabase",
            "python-dotenv"
        ]
        
        for package in packages:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        
        print("✅ Dépendances installées avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'installation des dépendances : {e}")
        return False

if __name__ == "__main__":
    print("🔧 Script de configuration Supabase")
    print("=" * 40)
    
    # Menu principal
    while True:
        print("\nOptions disponibles :")
        print("1. Installer les dépendances")
        print("2. Créer un fichier .env")
        print("3. Configurer Supabase")
        print("4. Configuration complète")
        print("5. Quitter")
        
        choice = input("\nChoisissez une option (1-5) : ").strip()
        
        if choice == "1":
            install_dependencies()
        elif choice == "2":
            create_env_file()
        elif choice == "3":
            main()
        elif choice == "4":
            print("\n🔄 Configuration complète...")
            if install_dependencies():
                create_env_file()
                main()
        elif choice == "5":
            print("👋 Au revoir !")
            break
        else:
            print("❌ Option invalide") 