#!/usr/bin/env python3
"""
Script de test pour Supabase
Ce script teste toutes les fonctionnalités du système de licences avec Supabase
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire app au path
sys.path.append(str(Path(__file__).parent / "app"))

from app.services.supabase_licences import (
    get_supabase_client, add_license, get_license_info, validate_license,
    update_license_usage, deactivate_license, get_all_licenses,
    format_license_key, get_license_status_text, days_until_expiration
)

def test_supabase_connection():
    """
    Teste la connexion à Supabase.
    """
    print("🔗 Test de connexion à Supabase...")
    
    try:
        supabase = get_supabase_client()
        if supabase:
            print("✅ Connexion à Supabase réussie")
            return True
        else:
            print("❌ Échec de la connexion à Supabase")
            return False
    except Exception as e:
        print(f"❌ Erreur de connexion : {e}")
        return False

def test_license_creation():
    """
    Teste la création de licences.
    """
    print("\n🔑 Test de création de licences...")
    
    test_licenses = [
        {
            "client_name": "Jean Dupont",
            "client_email": "jean.dupont@example.com",
            "company_name": "Entreprise Dupont",
            "duration_days": 365,
            "max_usage": 1000,
            "notes": "Licence de test 1"
        },
        {
            "client_name": "Marie Martin",
            "client_email": "marie.martin@example.com",
            "company_name": "Société Martin",
            "duration_days": 180,
            "max_usage": 500,
            "notes": "Licence de test 2"
        }
    ]
    
    created_licenses = []
    
    for i, license_data in enumerate(test_licenses, 1):
        print(f"  Création licence {i}...")
        try:
            license_key = add_license(**license_data)
            if license_key:
                created_licenses.append(license_key)
                print(f"  ✅ Licence {i} créée : {license_key}")
            else:
                print(f"  ❌ Échec création licence {i}")
        except Exception as e:
            print(f"  ❌ Erreur création licence {i} : {e}")
    
    return created_licenses

def test_license_validation(license_keys):
    """
    Teste la validation des licences.
    """
    print("\n✅ Test de validation des licences...")
    
    for i, license_key in enumerate(license_keys, 1):
        print(f"  Validation licence {i}...")
        try:
            is_valid, message = validate_license(license_key)
            if is_valid:
                print(f"  ✅ Licence {i} valide : {message}")
            else:
                print(f"  ❌ Licence {i} invalide : {message}")
        except Exception as e:
            print(f"  ❌ Erreur validation licence {i} : {e}")

def test_license_info(license_keys):
    """
    Teste la récupération d'informations des licences.
    """
    print("\n📋 Test de récupération d'informations...")
    
    for i, license_key in enumerate(license_keys, 1):
        print(f"  Récupération info licence {i}...")
        try:
            license_info = get_license_info(license_key)
            if license_info:
                status = get_license_status_text(license_info)
                days_left = days_until_expiration(license_info)
                formatted_key = format_license_key(license_key)
                
                print(f"  ✅ Licence {i} :")
                print(f"     - Client : {license_info['client_name']}")
                print(f"     - Email : {license_info['client_email']}")
                print(f"     - Statut : {status}")
                print(f"     - Jours restants : {days_left}")
                print(f"     - Utilisations : {license_info['usage_count']}")
                print(f"     - Clé formatée : {formatted_key}")
            else:
                print(f"  ❌ Licence {i} non trouvée")
        except Exception as e:
            print(f"  ❌ Erreur récupération licence {i} : {e}")

def test_license_usage_update(license_keys):
    """
    Teste la mise à jour des statistiques d'utilisation.
    """
    print("\n📊 Test de mise à jour des statistiques...")
    
    for i, license_key in enumerate(license_keys, 1):
        print(f"  Mise à jour utilisation licence {i}...")
        try:
            # Récupérer les informations avant mise à jour
            before_info = get_license_info(license_key)
            before_count = before_info['usage_count'] if before_info else 0
            
            # Mettre à jour l'utilisation
            success = update_license_usage(license_key)
            
            if success:
                # Récupérer les informations après mise à jour
                after_info = get_license_info(license_key)
                after_count = after_info['usage_count'] if after_info else 0
                
                print(f"  ✅ Licence {i} : {before_count} → {after_count} utilisations")
            else:
                print(f"  ❌ Échec mise à jour licence {i}")
        except Exception as e:
            print(f"  ❌ Erreur mise à jour licence {i} : {e}")

def test_license_deactivation(license_keys):
    """
    Teste la désactivation des licences.
    """
    print("\n🚫 Test de désactivation des licences...")
    
    # Désactiver seulement la première licence pour le test
    if license_keys:
        license_key = license_keys[0]
        print(f"  Désactivation licence 1...")
        try:
            success = deactivate_license(license_key)
            if success:
                print(f"  ✅ Licence 1 désactivée")
                
                # Vérifier que la licence est bien désactivée
                license_info = get_license_info(license_key)
                if license_info and not license_info['is_active']:
                    print(f"  ✅ Vérification : licence bien désactivée")
                else:
                    print(f"  ⚠️  Vérification : licence toujours active")
            else:
                print(f"  ❌ Échec désactivation licence 1")
        except Exception as e:
            print(f"  ❌ Erreur désactivation licence 1 : {e}")

def test_list_all_licenses():
    """
    Teste la récupération de toutes les licences.
    """
    print("\n📋 Test de récupération de toutes les licences...")
    
    try:
        licenses = get_all_licenses()
        print(f"  ✅ {len(licenses)} licences trouvées")
        
        for i, license_info in enumerate(licenses, 1):
            status = get_license_status_text(license_info)
            print(f"  {i}. {license_info['client_name']} - {status}")
            
    except Exception as e:
        print(f"  ❌ Erreur récupération licences : {e}")

def run_all_tests():
    """
    Lance tous les tests.
    """
    print("🧪 Tests du système de licences Supabase")
    print("=" * 50)
    
    # Test de connexion
    if not test_supabase_connection():
        print("❌ Impossible de continuer sans connexion Supabase")
        return False
    
    # Test de création
    created_licenses = test_license_creation()
    if not created_licenses:
        print("❌ Impossible de continuer sans licences créées")
        return False
    
    # Tests avec les licences créées
    test_license_validation(created_licenses)
    test_license_info(created_licenses)
    test_license_usage_update(created_licenses)
    test_license_deactivation(created_licenses)
    test_list_all_licenses()
    
    print("\n" + "=" * 50)
    print("🎉 Tous les tests sont terminés !")
    print(f"📝 {len(created_licenses)} licences de test créées")
    
    return True

def cleanup_test_licenses():
    """
    Nettoie les licences de test (optionnel).
    """
    print("\n🧹 Nettoyage des licences de test...")
    
    try:
        licenses = get_all_licenses()
        test_licenses = [l for l in licenses if "test" in l.get('notes', '').lower()]
        
        for license_info in test_licenses:
            print(f"  Suppression : {license_info['client_name']}")
            # Note: Supabase ne permet pas la suppression directe via l'API publique
            # Les licences de test resteront dans la base
            # Vous pouvez les supprimer manuellement via l'interface Supabase
        
        print(f"  ⚠️  {len(test_licenses)} licences de test à supprimer manuellement")
        
    except Exception as e:
        print(f"  ❌ Erreur nettoyage : {e}")

if __name__ == "__main__":
    print("🔧 Script de test Supabase")
    print("=" * 30)
    
    # Menu principal
    while True:
        print("\nOptions disponibles :")
        print("1. Test de connexion")
        print("2. Tests complets")
        print("3. Nettoyer les licences de test")
        print("4. Quitter")
        
        choice = input("\nChoisissez une option (1-4) : ").strip()
        
        if choice == "1":
            test_supabase_connection()
        elif choice == "2":
            run_all_tests()
        elif choice == "3":
            cleanup_test_licenses()
        elif choice == "4":
            print("👋 Au revoir !")
            break
        else:
            print("❌ Option invalide") 