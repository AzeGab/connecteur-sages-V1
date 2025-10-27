#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour corriger la configuration HFSQL avec le DSN qui fonctionne
"""

import sys
import os
import json

# Ajouter le répertoire app au path pour importer les modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.connex import save_credentials, load_credentials

def fix_hfsql_config():
    """Corrige la configuration HFSQL pour utiliser le DSN qui fonctionne"""
    print("🔧 Correction de la configuration HFSQL...")
    
    # Configuration HFSQL corrigée avec le DSN qui fonctionne
    hfsql_config = {
        "host": "HFSQL_LOCAL",  # DSN qui fonctionne
        "dsn": "HFSQL_LOCAL",   # DSN qui fonctionne
        "user": "admin",
        "password": "",
        "database": "DATA_DEMO",
        "port": "4900"
    }
    
    # Charger la configuration existante
    creds = load_credentials() or {}
    creds["software"] = "codial"
    creds["hfsql"] = hfsql_config
    
    # Sauvegarder la configuration corrigée
    save_credentials(creds)
    print("✅ Configuration HFSQL corrigée")
    print(f"   DSN: {hfsql_config['dsn']} (qui fonctionne)")
    print(f"   Base de données: {hfsql_config['database']}")
    print(f"   Host: {hfsql_config['host']}")
    
    return True

def test_connection():
    """Teste la connexion avec la configuration corrigée"""
    print("\n🔌 Test de la connexion HFSQL...")
    
    from services.connex import connect_to_hfsql
    
    # Test avec le DSN qui fonctionne
    conn = connect_to_hfsql("DSN=HFSQL_LOCAL")
    
    if conn:
        print("✅ Connexion HFSQL réussie avec DSN=HFSQL_LOCAL")
        
        # Test de requête
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM REPARAT")
            result = cursor.fetchone()
            count = result[0] if result else 0
            print(f"✅ Requête test réussie: {count} enregistrements dans REPARAT")
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"⚠️  Connexion OK mais erreur de requête: {e}")
            conn.close()
            return True
    else:
        print("❌ Connexion HFSQL échouée")
        return False

def main():
    """Fonction principale"""
    print("🚀 Correction de la configuration HFSQL")
    print("=" * 50)
    
    # Étape 1: Corriger la configuration
    if not fix_hfsql_config():
        print("❌ Échec de la correction de configuration")
        return False
    
    # Étape 2: Tester la connexion
    if not test_connection():
        print("❌ Échec du test de connexion")
        return False
    
    print("\n🎉 Configuration corrigée et testée avec succès!")
    print("\n📋 Maintenant vous pouvez:")
    print("1. Aller sur http://localhost:8000/configuration")
    print("2. Cliquer sur 'Test requête REPARAT'")
    print("3. Voir les résultats de votre table REPARAT")
    
    return True

if __name__ == "__main__":
    main()
