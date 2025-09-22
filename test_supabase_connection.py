#!/usr/bin/env python3
"""
Script de test pour vérifier la connexion à Supabase et la validation des licences
"""

import os
import sys
import requests
from dotenv import load_dotenv
import json

# Charger les variables d'environnement
load_dotenv()

# Configuration Supabase
SUPABASE_URL = "https://rxqveiaawggfyeukpvyz.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ4cXZlaWFhd2dnZnlldWtwdnl6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA2NjQzMjAsImV4cCI6MjA2NjI0MDMyMH0.vYrxDe41M_a8XDcbHwmaiVfy8rKMsyNroiHvNHq5FAM")

def test_supabase_connection():
    """Test de connexion à Supabase"""
    print("🔍 Test de connexion à Supabase...")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # Test de connexion simple
        response = requests.get(f"{SUPABASE_URL}/rest/v1/", headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ Connexion à Supabase réussie !")
            return True
        else:
            print(f"❌ Erreur de connexion: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def test_licenses_table():
    """Test d'accès à la table licenses"""
    print("\n🔍 Test d'accès à la table licenses...")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # Test d'accès à la table licenses
        response = requests.get(f"{SUPABASE_URL}/rest/v1/licenses", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Accès à la table licenses réussi !")
            print(f"📊 Nombre de licences trouvées: {len(data)}")
            
            if data:
                print("📋 Structure de la première licence:")
                for key, value in data[0].items():
                    print(f"   {key}: {value}")
            
            return True
        else:
            print(f"❌ Erreur d'accès à la table: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur d'accès à la table: {e}")
        return False

def test_license_validation(license_key):
    """Test de validation d'une clé de licence"""
    print(f"\n🔍 Test de validation de la clé: {license_key}")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # Test de validation d'une clé spécifique
        url = f"{SUPABASE_URL}/rest/v1/licenses?license_key=eq.{license_key}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data and len(data) > 0:
                license_info = data[0]
                print(f"✅ Licence trouvée !")
                print(f"📋 Informations de la licence:")
                for key, value in license_info.items():
                    print(f"   {key}: {value}")
                return True
            else:
                print(f"❌ Licence non trouvée")
                return False
        else:
            print(f"❌ Erreur de validation: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur de validation: {e}")
        return False

def get_local_license_key():
    """Récupère la clé de licence locale enregistrée dans credentials.json"""
    try:
        with open("app/services/credentials.json", "r") as f:
            creds = json.load(f)
            license_info = creds.get("license")
            if license_info:
                return license_info.get("key")
    except Exception:
        pass
    return None

def main():
    """Fonction principale de test"""
    print("🚀 Test de la configuration Supabase pour les licences")
    print("=" * 60)
    
    # Test 1: Connexion à Supabase
    if not test_supabase_connection():
        print("\n❌ Impossible de se connecter à Supabase. Vérifiez votre configuration.")
        sys.exit(1)
    
    # Test 2: Accès à la table licenses
    if not test_licenses_table():
        print("\n❌ Impossible d'accéder à la table licenses. Vérifiez les permissions.")
        sys.exit(1)
    
    # Test 3: Validation d'une clé locale si présente
    local_key = get_local_license_key()
    if local_key:
        print(f"\n🔑 Clé de licence locale trouvée dans credentials.json : {local_key}")
        test_license_validation(local_key)
    else:
        # Sinon, demander à l'utilisateur
        test_key = input("\n🔑 Entrez une clé de licence à tester (ou appuyez sur Entrée pour passer): ").strip()
        if test_key:
            test_license_validation(test_key)
    
    print("\n✅ Tests terminés !")
    print("\n📝 Prochaines étapes:")
    print("1. Vérifiez que la table 'licenses' existe dans votre projet Supabase")
    print("2. Assurez-vous que la table contient les colonnes: license_key, client_name, expiry_date, features")
    print("3. Testez l'application avec une vraie clé de licence")

if __name__ == "__main__":
    main() 