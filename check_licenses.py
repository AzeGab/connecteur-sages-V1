#!/usr/bin/env python3
"""
Script de vérification des licences Supabase
"""

import os
import sys
from pathlib import Path

# Charger les variables d'environnement
from dotenv import load_dotenv
load_dotenv()

# Ajouter le répertoire app au path
sys.path.append(str(Path(__file__).parent / "app"))

def main():
    print("🔍 Vérification des licences Supabase")
    print("=" * 50)
    
    # Vérifier les variables d'environnement
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    print(f"SUPABASE_URL: {supabase_url}")
    print(f"SUPABASE_KEY: {supabase_key[:20]}..." if supabase_key else "Non défini")
    
    try:
        from app.services.supabase_licences import get_all_licenses, get_supabase_client
        
        # Tester la connexion
        supabase = get_supabase_client()
        if not supabase:
            print("❌ Impossible de se connecter à Supabase")
            return
        
        print("✅ Connexion Supabase réussie")
        
        # Récupérer toutes les licences
        licenses = get_all_licenses()
        print(f"\n📋 Licences trouvées: {len(licenses)}")
        
        for i, license_info in enumerate(licenses, 1):
            print(f"\n{i}. Licence:")
            print(f"   - Client: {license_info.get('client_name', 'N/A')}")
            print(f"   - Email: {license_info.get('client_email', 'N/A')}")
            print(f"   - Clé: {license_info.get('license_key', 'N/A')}")
            print(f"   - Actif: {license_info.get('is_active', 'N/A')}")
            print(f"   - Expire: {license_info.get('expires_at', 'N/A')}")
            print(f"   - Utilisations: {license_info.get('usage_count', 0)}")
            print(f"   - Max utilisations: {license_info.get('max_usage', -1)}")
        
        # Vérifier les routes de l'API
        print(f"\n🚀 Vérification des routes API...")
        from app.main import app
        routes = [route.path for route in app.routes if 'licenses' in route.path]
        print(f"Routes de licences trouvées: {len(routes)}")
        for route in routes:
            print(f"  - {route}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 