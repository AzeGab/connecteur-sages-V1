#!/usr/bin/env python3
"""
Test rapide de l'installation Supabase
Ce script vérifie rapidement que tout fonctionne avec Supabase
"""

import os
import sys
from pathlib import Path

# Charger les variables d'environnement depuis le fichier .env
from dotenv import load_dotenv
load_dotenv()

# Ajouter le répertoire app au path
sys.path.append(str(Path(__file__).parent / "app"))

def test_environment():
    """
    Teste les variables d'environnement.
    """
    print("🔧 Test des variables d'environnement...")
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url:
        print("❌ SUPABASE_URL manquant")
        return False
    
    if not supabase_key:
        print("❌ SUPABASE_KEY manquant")
        return False
    
    print(f"✅ SUPABASE_URL : {supabase_url}")
    print(f"✅ SUPABASE_KEY : {supabase_key[:10]}...")
    return True

def test_imports():
    """
    Teste les imports des modules.
    """
    print("\n📦 Test des imports...")
    
    try:
        from app.services.supabase_licences import get_supabase_client
        print("✅ Module supabase_licences importé")
    except ImportError as e:
        print(f"❌ Erreur import supabase_licences : {e}")
        return False
    
    try:
        from app.middleware.license_middleware import add_license_middleware
        print("✅ Module license_middleware importé")
    except ImportError as e:
        print(f"❌ Erreur import license_middleware : {e}")
        return False
    
    try:
        from app.routes.license_routes import router
        print("✅ Module license_routes importé")
    except ImportError as e:
        print(f"❌ Erreur import license_routes : {e}")
        return False
    
    return True

def test_supabase_connection():
    """
    Teste la connexion à Supabase.
    """
    print("\n🔗 Test de connexion Supabase...")
    
    try:
        from app.services.supabase_licences import get_supabase_client
        supabase = get_supabase_client()
        
        if supabase:
            print("✅ Connexion Supabase réussie")
            return True
        else:
            print("❌ Échec de la connexion Supabase")
            return False
            
    except Exception as e:
        print(f"❌ Erreur connexion Supabase : {e}")
        return False

def test_table_exists():
    """
    Teste si la table licenses existe.
    """
    print("\n📋 Test de la table licenses...")
    
    try:
        from app.services.supabase_licences import get_supabase_client
        supabase = get_supabase_client()
        
        if not supabase:
            print("❌ Impossible de se connecter à Supabase")
            return False
        
        # Tenter de récupérer les licences
        result = supabase.table('licenses').select('*').limit(1).execute()
        
        if result is not None:
            print("✅ Table licenses accessible")
            return True
        else:
            print("❌ Table licenses inaccessible")
            return False
            
    except Exception as e:
        print(f"❌ Erreur accès table : {e}")
        print("💡 Vérifiez que la table 'licenses' existe dans Supabase")
        return False

def test_license_creation():
    """
    Teste la création d'une licence de test.
    """
    print("\n🔑 Test de création de licence...")
    
    try:
        from app.services.supabase_licences import add_license, deactivate_license
        
        # Créer une licence de test
        license_key = add_license(
            client_name="Test Rapide",
            client_email="test@quick.com",
            company_name="Test Company",
            duration_days=1,  # Expire demain
            max_usage=1,
            notes="Licence de test rapide - à supprimer"
        )
        
        if license_key:
            print(f"✅ Licence de test créée : {license_key}")
            
            # Désactiver immédiatement pour le nettoyage
            deactivate_license(license_key)
            print("✅ Licence de test désactivée")
            
            return True
        else:
            print("❌ Échec création licence de test")
            return False
            
    except Exception as e:
        print(f"❌ Erreur création licence : {e}")
        return False

def test_fastapi_app():
    """
    Teste que l'application FastAPI peut démarrer.
    """
    print("\n🚀 Test de l'application FastAPI...")
    
    try:
        from app.main import app
        print("✅ Application FastAPI créée")
        
        # Vérifier que les routes sont enregistrées
        routes = [route.path for route in app.routes]
        license_routes = [r for r in routes if 'licenses' in r]
        
        if license_routes:
            print(f"✅ Routes de licences trouvées : {len(license_routes)}")
            return True
        else:
            print("❌ Aucune route de licence trouvée")
            return False
            
    except Exception as e:
        print(f"❌ Erreur application FastAPI : {e}")
        return False

def main():
    """
    Fonction principale de test.
    """
    print("🧪 Test rapide de l'installation Supabase")
    print("=" * 50)
    
    tests = [
        ("Variables d'environnement", test_environment),
        ("Imports des modules", test_imports),
        ("Connexion Supabase", test_supabase_connection),
        ("Table licenses", test_table_exists),
        ("Création de licence", test_license_creation),
        ("Application FastAPI", test_fastapi_app)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur lors du test '{test_name}' : {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 Résumé des tests :")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Score : {passed}/{total} tests réussis")
    
    if passed == total:
        print("\n🎉 Tous les tests sont passés !")
        print("✅ Votre installation Supabase est opérationnelle")
        print("\n🚀 Vous pouvez maintenant :")
        print("  - Lancer l'application : python -m uvicorn app.main:app --reload")
        print("  - Accéder à l'interface : http://localhost:8000/licenses/")
        print("  - Tester l'API : http://localhost:8000/docs")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) ont échoué")
        print("🔧 Vérifiez la configuration et réessayez")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 