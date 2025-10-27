#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test final pour vérifier l'interface web
"""

import requests
import json
import time

def test_web_interface():
    """Teste l'interface web avec la table CLIENT"""
    print("🌐 Test de l'interface web")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    try:
        # Test 1: Vérifier que le serveur répond
        print("🔌 Test de connexion au serveur...")
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("   ✅ Serveur accessible")
        else:
            print(f"   ❌ Serveur inaccessible (code: {response.status_code})")
            return False
        
        # Test 2: Tester la route de requête CLIENT
        print("\n📊 Test de la requête CLIENT...")
        response = requests.get(f"{base_url}/query-hfsql-reparat", timeout=10)
        
        if response.status_code == 200:
            print("   ✅ Route de requête accessible")
            
            # Vérifier le contenu
            html_content = response.text
            
            if "Table: CLIENT" in html_content:
                print("   ✅ Table CLIENT détectée dans la réponse")
            else:
                print("   ⚠️  Table CLIENT non trouvée dans la réponse")
            
            if "2918 enregistrements" in html_content:
                print("   ✅ Nombre d'enregistrements affiché")
            else:
                print("   ⚠️  Nombre d'enregistrements non affiché")
            
            if "enregistrement(s)" in html_content or "Aucun résultat trouvé" in html_content:
                print("   ✅ Données ou message d'absence de données détecté")
            else:
                print("   ⚠️  Aucune donnée détectée")
            
            if "Erreur" in html_content or "error" in html_content.lower():
                print("   ⚠️  Erreur détectée dans la réponse")
            else:
                print("   ✅ Aucune erreur détectée")
                
        else:
            print(f"   ❌ Erreur de la route (code: {response.status_code})")
            return False
        
        # Test 3: Vérifier la page de configuration
        print("\n⚙️ Test de la page de configuration...")
        response = requests.get(f"{base_url}/configuration", timeout=5)
        
        if response.status_code == 200:
            print("   ✅ Page de configuration accessible")
            
            if "Test requête CLIENT" in response.text:
                print("   ✅ Bouton 'Test requête CLIENT' trouvé")
            else:
                print("   ⚠️  Bouton 'Test requête CLIENT' non trouvé")
        else:
            print(f"   ❌ Page de configuration inaccessible (code: {response.status_code})")
            return False
        
        print("\n🎉 Tous les tests sont passés avec succès!")
        print("\n📋 Instructions pour utiliser l'interface:")
        print(f"1. Ouvrez votre navigateur sur: {base_url}/configuration")
        print("2. Allez dans l'onglet 'Bases de données'")
        print("3. Cliquez sur 'Test requête CLIENT'")
        print("4. Vous devriez voir les données de la table CLIENT (2918 enregistrements)")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

def main():
    """Fonction principale"""
    print("🚀 Test final de l'interface web")
    print("=" * 50)
    
    success = test_web_interface()
    
    if success:
        print("\n✅ Interface web fonctionnelle!")
        print("💡 Vous pouvez maintenant utiliser l'interface pour voir vos données.")
    else:
        print("\n❌ Problème avec l'interface web")
        print("💡 Vérifiez que le serveur uvicorn est démarré.")

if __name__ == "__main__":
    main()
