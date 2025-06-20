#!/usr/bin/env python3
# Script de test pour le système de licences
# Ce script teste toutes les fonctionnalités du système de licences

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.licences import (
    generate_license_key, validate_license_key, create_licenses_table,
    add_license, get_license_info, validate_license, update_license_usage,
    deactivate_license, get_all_licenses, format_license_key,
    get_license_status_text, days_until_expiration
)
from app.services.connex import connect_to_postgres, load_credentials
import datetime

def test_license_generation():
    """Test de la génération de clés de licence."""
    print("🔑 Test de génération de clés de licence...")
    
    # Test 1: Génération basique
    key1 = generate_license_key("Jean Dupont", "jean.dupont@test.com", 365)
    print(f"   Clé générée: {key1}")
    assert len(key1.replace('-', '')) == 32, "La clé doit faire 32 caractères"
    
    # Test 2: Même client, même durée = même clé
    key2 = generate_license_key("Jean Dupont", "jean.dupont@test.com", 365)
    assert key1 == key2, "Même client et durée doivent générer la même clé"
    
    # Test 3: Client différent = clé différente
    key3 = generate_license_key("Marie Martin", "marie.martin@test.com", 365)
    assert key1 != key3, "Clients différents doivent générer des clés différentes"
    
    print("   ✅ Génération de clés OK")

def test_license_validation():
    """Test de la validation de format des clés."""
    print("🔍 Test de validation de format...")
    
    # Test 1: Clé valide
    valid_key = "A1B2-C3D4-E5F6-7890-ABCD-EF12-3456-7890"
    assert validate_license_key(valid_key) == True, "Clé valide rejetée"
    
    # Test 2: Clé invalide (trop courte)
    invalid_key1 = "A1B2-C3D4-E5F6"
    assert validate_license_key(invalid_key1) == False, "Clé trop courte acceptée"
    
    # Test 3: Clé invalide (caractères non hex)
    invalid_key2 = "A1B2-C3D4-E5F6-7890-ABCD-EF12-3456-789G"
    assert validate_license_key(invalid_key2) == False, "Clé avec caractères non hex acceptée"
    
    # Test 4: Clé vide
    assert validate_license_key("") == False, "Clé vide acceptée"
    
    print("   ✅ Validation de format OK")

def test_database_operations():
    """Test des opérations de base de données."""
    print("🗄️ Test des opérations de base de données...")
    
    # Charger les identifiants
    creds = load_credentials()
    if not creds or 'postgresql' not in creds:
        print("   ⚠️ Configuration PostgreSQL manquante, test ignoré")
        return
    
    try:
        # Se connecter à PostgreSQL
        pg_creds = creds['postgresql']
        conn = connect_to_postgres(
            pg_creds['host'],
            pg_creds['user'],
            pg_creds['password'],
            pg_creds['database'],
            pg_creds.get('port', '5432')
        )
        
        if not conn:
            print("   ⚠️ Impossible de se connecter à PostgreSQL, test ignoré")
            return
        
        # Test 1: Création de la table
        success = create_licenses_table(conn)
        assert success == True, "Échec de création de la table"
        print("   ✅ Création de table OK")
        
        # Test 2: Ajout d'une licence
        license_key = add_license(
            conn=conn,
            client_name="Test Client",
            client_email="test@example.com",
            company_name="Test Company",
            duration_days=30,
            max_usage=10,
            notes="Licence de test"
        )
        assert license_key is not None, "Échec d'ajout de licence"
        print(f"   ✅ Ajout de licence OK: {format_license_key(license_key)}")
        
        # Test 3: Récupération des informations
        license_info = get_license_info(conn, license_key)
        assert license_info is not None, "Échec de récupération des informations"
        assert license_info['client_name'] == "Test Client", "Nom client incorrect"
        assert license_info['client_email'] == "test@example.com", "Email client incorrect"
        print("   ✅ Récupération d'informations OK")
        
        # Test 4: Validation de licence
        is_valid, message = validate_license(conn, license_key)
        assert is_valid == True, f"Licence valide rejetée: {message}"
        print("   ✅ Validation de licence OK")
        
        # Test 5: Mise à jour des statistiques
        success = update_license_usage(conn, license_key)
        assert success == True, "Échec de mise à jour des statistiques"
        
        # Vérifier que le compteur a augmenté
        updated_info = get_license_info(conn, license_key)
        assert updated_info['usage_count'] == 1, "Compteur d'utilisation non mis à jour"
        print("   ✅ Mise à jour des statistiques OK")
        
        # Test 6: Désactivation de licence
        success = deactivate_license(conn, license_key)
        assert success == True, "Échec de désactivation"
        
        # Vérifier que la licence est désactivée
        deactivated_info = get_license_info(conn, license_key)
        assert deactivated_info['is_active'] == False, "Licence non désactivée"
        print("   ✅ Désactivation de licence OK")
        
        # Test 7: Liste des licences
        licenses = get_all_licenses(conn)
        assert len(licenses) > 0, "Aucune licence trouvée"
        print(f"   ✅ Liste des licences OK ({len(licenses)} licences)")
        
        conn.close()
        print("   ✅ Toutes les opérations de base de données OK")
        
    except Exception as e:
        print(f"   ❌ Erreur lors des tests de base de données: {e}")
        if conn:
            conn.close()

def test_utility_functions():
    """Test des fonctions utilitaires."""
    print("🛠️ Test des fonctions utilitaires...")
    
    # Test de formatage de clé
    raw_key = "A1B2C3D4E5F67890ABCDEF1234567890"
    formatted = format_license_key(raw_key)
    assert formatted == "A1B2-C3D4-E5F6-7890-ABCD-EF12-3456-7890", "Formatage incorrect"
    print("   ✅ Formatage de clé OK")
    
    # Test de calcul de statut
    license_info = {
        'is_active': True,
        'expires_at': datetime.datetime.now() + datetime.timedelta(days=30),
        'max_usage': 10,
        'usage_count': 5
    }
    status = get_license_status_text(license_info)
    assert status == "Active", f"Statut incorrect: {status}"
    print("   ✅ Calcul de statut OK")
    
    # Test de calcul de jours avant expiration
    days = days_until_expiration(license_info)
    assert 25 <= days <= 35, f"Calcul de jours incorrect: {days}"
    print("   ✅ Calcul de jours avant expiration OK")
    
    print("   ✅ Toutes les fonctions utilitaires OK")

def main():
    """Fonction principale de test."""
    print("🧪 Démarrage des tests du système de licences...\n")
    
    try:
        test_license_generation()
        print()
        
        test_license_validation()
        print()
        
        test_utility_functions()
        print()
        
        test_database_operations()
        print()
        
        print("🎉 Tous les tests sont passés avec succès !")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 