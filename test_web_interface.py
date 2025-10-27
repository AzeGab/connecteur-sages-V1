#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour l'interface web avec requête HFSQL
"""

import requests
import time

def test_web_interface():
    """Teste l'interface web avec la requête HFSQL"""
    base_url = "http://localhost:8000"
    
    print("🔍 Test de l'interface web avec requête HFSQL")
    print("=" * 50)
    
    # Test 1: Vérifier que le serveur répond
    print("1. Test de santé du serveur...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Serveur opérationnel")
        else:
            print(f"   ❌ Serveur répond avec le code: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Serveur inaccessible: {e}")
        return False
    
    # Test 2: Accéder à la page de configuration
    print("\n2. Test de la page de configuration...")
    try:
        response = requests.get(f"{base_url}/configuration", timeout=5)
        if response.status_code == 200:
            print("   ✅ Page de configuration accessible")
            if "Test requête REPARAT" in response.text:
                print("   ✅ Bouton de test de requête trouvé")
            else:
                print("   ⚠️  Bouton de test de requête non trouvé")
        else:
            print(f"   ❌ Page de configuration inaccessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Erreur d'accès à la configuration: {e}")
        return False
    
    # Test 3: Tester la route de requête HFSQL
    print("\n3. Test de la route de requête HFSQL...")
    try:
        response = requests.get(f"{base_url}/query-hfsql-reparat", timeout=10)
        if response.status_code == 200:
            print("   ✅ Route de requête HFSQL accessible")
            
            # Vérifier le contenu de la réponse
            if "Résultats de la requête HFSQL" in response.text:
                print("   ✅ Cadre de résultats trouvé")
            else:
                print("   ⚠️  Cadre de résultats non trouvé")
                
            if "Configuration HFSQL non trouvée" in response.text:
                print("   ℹ️  Configuration HFSQL non configurée (normal si pas encore configuré)")
            elif "table" in response.text.lower():
                print("   ✅ Données de table détectées")
            else:
                print("   ℹ️  Aucune donnée de table détectée")
                
        else:
            print(f"   ❌ Route de requête inaccessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Erreur lors du test de requête: {e}")
        return False
    
    print("\n🎉 Tous les tests sont passés avec succès!")
    print("\n💡 Instructions pour utiliser l'interface:")
    print("1. Ouvrez http://localhost:8000/configuration dans votre navigateur")
    print("2. Assurez-vous que le logiciel est configuré sur 'Codial'")
    print("3. Configurez la connexion HFSQL")
    print("4. Cliquez sur 'Test requête REPARAT' pour voir les résultats")
    
    return True

if __name__ == "__main__":
    test_web_interface()
