#!/usr/bin/env python3
"""
Script pour créer une licence de test active
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
    print("🔑 Création d'une licence de test active")
    print("=" * 50)
    
    try:
        from app.services.supabase_licences import add_license, get_all_licenses
        
        # Créer une licence de test active
        license_key = add_license(
            client_name="Client Test Actif",
            client_email="test.actif@example.com",
            company_name="Entreprise Test",
            duration_days=365,  # Valide 1 an
            max_usage=100,      # 100 utilisations max
            notes="Licence de test pour vérifier l'affichage dans le dashboard"
        )
        
        if license_key:
            print(f"✅ Licence créée avec succès!")
            print(f"   Clé: {license_key}")
            print(f"   Client: Client Test Actif")
            print(f"   Email: test.actif@example.com")
            print(f"   Durée: 365 jours")
            print(f"   Max utilisations: 100")
            
            # Vérifier toutes les licences
            print(f"\n📋 Toutes les licences:")
            licenses = get_all_licenses()
            for i, license_info in enumerate(licenses, 1):
                print(f"{i}. {license_info['client_name']} - Actif: {license_info['is_active']} - Clé: {license_info['license_key'][:10]}...")
                
        else:
            print("❌ Erreur lors de la création de la licence")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 