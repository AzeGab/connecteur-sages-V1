#!/usr/bin/env python3
# Script de test simple pour vérifier que l'application fonctionne

import requests
import time

def test_application():
    """Teste que l'application fonctionne correctement."""
    print("🧪 Test de l'application Connecteur Sages...")
    
    # Attendre que l'application démarre
    print("⏳ Attente du démarrage de l'application...")
    time.sleep(3)
    
    try:
        # Test de la page d'accueil
        print("📄 Test de la page d'accueil...")
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Page d'accueil accessible")
        else:
            print(f"❌ Page d'accueil: {response.status_code}")
            return False
        
        # Test de la page des licences
        print("🔑 Test de la page des licences...")
        response = requests.get("http://localhost:8000/licenses/", timeout=5)
        if response.status_code == 200:
            print("✅ Page des licences accessible")
        else:
            print(f"❌ Page des licences: {response.status_code}")
            return False
        
        # Test de la page de création de licence
        print("➕ Test de la page de création de licence...")
        response = requests.get("http://localhost:8000/licenses/create", timeout=5)
        if response.status_code == 200:
            print("✅ Page de création de licence accessible")
        else:
            print(f"❌ Page de création de licence: {response.status_code}")
            return False
        
        print("\n🎉 Tous les tests sont passés avec succès !")
        print("\n📱 Vous pouvez maintenant accéder à l'application :")
        print("   - Accueil: http://localhost:8000/")
        print("   - Licences: http://localhost:8000/licenses/")
        print("   - Créer une licence: http://localhost:8000/licenses/create")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter à l'application")
        print("💡 Assurez-vous que l'application est démarrée avec:")
        print("   python -m uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

if __name__ == "__main__":
    test_application() 