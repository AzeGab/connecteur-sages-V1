#!/usr/bin/env python3
"""
Script de migration de PostgreSQL vers Supabase
Ce script transfère les données de licences de PostgreSQL local vers Supabase
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire app au path
sys.path.append(str(Path(__file__).parent / "app"))

from app.services.connex import connect_to_postgres, load_credentials
from app.services.supabase_licences import get_supabase_client, add_license

def get_postgresql_licenses():
    """
    Récupère toutes les licences de PostgreSQL local.
    """
    print("📊 Récupération des licences PostgreSQL...")
    
    try:
        # Charger les identifiants PostgreSQL
        creds = load_credentials()
        if not creds or 'postgresql' not in creds:
            print("❌ Configuration PostgreSQL manquante")
            return []
        
        pg_creds = creds['postgresql']
        
        # Se connecter à PostgreSQL
        conn = connect_to_postgres(
            pg_creds['host'],
            pg_creds['user'],
            pg_creds['password'],
            pg_creds['database'],
            pg_creds.get('port', '5432')
        )
        
        if not conn:
            print("❌ Impossible de se connecter à PostgreSQL")
            return []
        
        # Récupérer toutes les licences
        cursor = conn.cursor()
        cursor.execute("""
            SELECT license_key, client_name, client_email, company_name,
                   created_at, expires_at, is_active, last_used, 
                   usage_count, max_usage, notes
            FROM licenses
            ORDER BY created_at
        """)
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        licenses = []
        for result in results:
            licenses.append({
                'license_key': result[0],
                'client_name': result[1],
                'client_email': result[2],
                'company_name': result[3],
                'created_at': result[4],
                'expires_at': result[5],
                'is_active': result[6],
                'last_used': result[7],
                'usage_count': result[8],
                'max_usage': result[9],
                'notes': result[10]
            })
        
        print(f"✅ {len(licenses)} licences récupérées de PostgreSQL")
        return licenses
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération PostgreSQL : {e}")
        return []

def migrate_license_to_supabase(license_data):
    """
    Migre une licence vers Supabase.
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        # Préparer les données pour Supabase
        supabase_data = {
            'license_key': license_data['license_key'],
            'client_name': license_data['client_name'],
            'client_email': license_data['client_email'],
            'company_name': license_data['company_name'],
            'created_at': license_data['created_at'].isoformat() if license_data['created_at'] else None,
            'expires_at': license_data['expires_at'].isoformat() if license_data['expires_at'] else None,
            'is_active': license_data['is_active'],
            'last_used': license_data['last_used'].isoformat() if license_data['last_used'] else None,
            'usage_count': license_data['usage_count'],
            'max_usage': license_data['max_usage'],
            'notes': license_data['notes']
        }
        
        # Insérer dans Supabase
        result = supabase.table('licenses').insert(supabase_data).execute()
        
        return len(result.data) > 0
        
    except Exception as e:
        print(f"  ❌ Erreur migration licence {license_data['license_key']} : {e}")
        return False

def migrate_all_licenses():
    """
    Migre toutes les licences de PostgreSQL vers Supabase.
    """
    print("🔄 Migration PostgreSQL → Supabase")
    print("=" * 50)
    
    # Récupérer les licences PostgreSQL
    pg_licenses = get_postgresql_licenses()
    
    if not pg_licenses:
        print("❌ Aucune licence à migrer")
        return False
    
    # Vérifier la connexion Supabase
    print("\n🔗 Test de connexion Supabase...")
    supabase = get_supabase_client()
    if not supabase:
        print("❌ Impossible de se connecter à Supabase")
        return False
    print("✅ Connexion Supabase OK")
    
    # Migrer chaque licence
    print(f"\n📦 Migration de {len(pg_licenses)} licences...")
    
    success_count = 0
    error_count = 0
    
    for i, license_data in enumerate(pg_licenses, 1):
        print(f"  [{i}/{len(pg_licenses)}] Migration : {license_data['client_name']}")
        
        if migrate_license_to_supabase(license_data):
            success_count += 1
            print(f"    ✅ Migrée")
        else:
            error_count += 1
            print(f"    ❌ Échec")
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 Résumé de la migration :")
    print(f"  Total : {len(pg_licenses)} licences")
    print(f"  Succès : {success_count} licences")
    print(f"  Échecs : {error_count} licences")
    
    if success_count > 0:
        print("\n✅ Migration terminée avec succès !")
        return True
    else:
        print("\n❌ Aucune licence migrée")
        return False

def verify_migration():
    """
    Vérifie que la migration s'est bien passée.
    """
    print("\n🔍 Vérification de la migration...")
    
    try:
        # Récupérer les licences Supabase
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        result = supabase.table('licenses').select('*').execute()
        supabase_licenses = result.data
        
        # Récupérer les licences PostgreSQL
        pg_licenses = get_postgresql_licenses()
        
        print(f"  PostgreSQL : {len(pg_licenses)} licences")
        print(f"  Supabase : {len(supabase_licenses)} licences")
        
        if len(supabase_licenses) >= len(pg_licenses):
            print("  ✅ Migration vérifiée")
            return True
        else:
            print("  ❌ Données manquantes dans Supabase")
            return False
            
    except Exception as e:
        print(f"  ❌ Erreur vérification : {e}")
        return False

def create_backup():
    """
    Crée une sauvegarde des données PostgreSQL.
    """
    print("💾 Création d'une sauvegarde...")
    
    try:
        # Récupérer les licences PostgreSQL
        pg_licenses = get_postgresql_licenses()
        
        if not pg_licenses:
            print("❌ Aucune donnée à sauvegarder")
            return False
        
        # Créer le fichier de sauvegarde
        backup_file = f"backup_licenses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(pg_licenses, f, indent=2, default=str)
        
        print(f"✅ Sauvegarde créée : {backup_file}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur sauvegarde : {e}")
        return False

def main():
    """
    Fonction principale de migration.
    """
    print("🔄 Script de migration PostgreSQL → Supabase")
    print("=" * 60)
    
    # Vérifier les variables d'environnement
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        print("❌ Variables d'environnement Supabase manquantes")
        print("Veuillez définir SUPABASE_URL et SUPABASE_KEY")
        return False
    
    # Menu principal
    while True:
        print("\nOptions disponibles :")
        print("1. Créer une sauvegarde PostgreSQL")
        print("2. Migrer toutes les licences")
        print("3. Vérifier la migration")
        print("4. Migration complète (sauvegarde + migration + vérification)")
        print("5. Quitter")
        
        choice = input("\nChoisissez une option (1-5) : ").strip()
        
        if choice == "1":
            create_backup()
        elif choice == "2":
            migrate_all_licenses()
        elif choice == "3":
            verify_migration()
        elif choice == "4":
            print("\n🔄 Migration complète...")
            if create_backup():
                if migrate_all_licenses():
                    verify_migration()
        elif choice == "5":
            print("👋 Au revoir !")
            break
        else:
            print("❌ Option invalide")

if __name__ == "__main__":
    main() 