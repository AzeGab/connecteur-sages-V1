#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour configurer automatiquement HFSQL et tester la requête
"""

import sys
import os
import json
import requests

# Ajouter le répertoire app au path pour importer les modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.connex import save_credentials, load_credentials

def setup_hfsql_config():
    """Configure automatiquement la connexion HFSQL"""
    print("🔧 Configuration automatique de HFSQL...")
    
    # Configuration HFSQL pour DATA_DEMO
    hfsql_config = {
        "host": "127.0.0.1",
        "dsn": "codial",  # DSN qui fonctionne
        "user": "admin",
        "password": "",
        "database": "DATA_DEMO",  # Base de données correcte
        "port": "4900"
    }
    
    # Charger la configuration existante ou créer une nouvelle
    creds = load_credentials() or {}
    creds["software"] = "codial"
    creds["hfsql"] = hfsql_config
    
    # Sauvegarder la configuration
    save_credentials(creds)
    print("✅ Configuration HFSQL sauvegardée")
    print(f"   Base de données: {hfsql_config['database']}")
    print(f"   DSN: {hfsql_config['dsn']}")
    print(f"   Host: {hfsql_config['host']}")
    
    return True

def test_query_via_web():
    """Teste la requête via l'interface web"""
    print("\n🌐 Test de la requête via l'interface web...")
    
    try:
        response = requests.get("http://localhost:8000/query-hfsql-reparat", timeout=15)
        
        if response.status_code == 200:
            print("✅ Route de requête accessible")
            
            # Analyser le contenu de la réponse
            content = response.text
            
            if "Résultats de la requête HFSQL" in content:
                print("✅ Cadre de résultats trouvé")
                
                if "Configuration HFSQL non trouvée" in content:
                    print("❌ Configuration HFSQL non trouvée dans la réponse")
                    return False
                elif "table" in content.lower() and "reparat" in content.lower():
                    print("✅ Données de la table REPARAT détectées")
                    return True
                elif "erreur" in content.lower():
                    print("⚠️  Erreur détectée dans la réponse")
                    return False
                else:
                    print("ℹ️  Aucune donnée spécifique détectée")
                    return True
            else:
                print("❌ Cadre de résultats non trouvé")
                return False
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test web: {e}")
        return False

def main():
    """Fonction principale"""
    print("🚀 Configuration et test de l'interface HFSQL")
    print("=" * 50)
    
    # Étape 1: Configurer HFSQL
    if not setup_hfsql_config():
        print("❌ Échec de la configuration")
        return False
    
    # Étape 2: Tester via l'interface web
    if not test_query_via_web():
        print("❌ Échec du test web")
        return False
    
    print("\n🎉 Configuration et test réussis!")
    print("\n📋 Instructions pour utiliser l'interface:")
    print("1. Ouvrez http://localhost:8000/configuration")
    print("2. Allez dans l'onglet 'Bases de données'")
    print("3. Cliquez sur 'Test requête REPARAT'")
    print("4. Vous devriez voir les résultats de la table REPARAT")
    
    return True

if __name__ == "__main__":
    main()
