#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour corriger la configuration et utiliser DATA_DEMO au lieu d'ESPE-PROD
"""

import json
import os

def fix_database_config():
    """Corrige la configuration pour utiliser DATA_DEMO"""
    print("🔧 Correction de la configuration de base de données")
    print("=" * 60)
    
    credentials_file = "app/services/credentials.json"
    
    # Configuration correcte pour DATA_DEMO
    correct_config = {
        "software": "codial",
        "hfsql": {
            "host": "127.0.0.1",
            "dsn": "HFSQL_LOCAL",
            "user": "admin",
            "password": "",
            "database": "DATA_DEMO",  # Base correcte
            "port": "4900"
        }
    }
    
    try:
        # Sauvegarder la configuration
        os.makedirs(os.path.dirname(credentials_file), exist_ok=True)
        with open(credentials_file, "w", encoding="utf-8") as f:
            json.dump(correct_config, f, indent=2, ensure_ascii=False)
        
        print("✅ Configuration corrigée")
        print(f"   Base de données: {correct_config['hfsql']['database']}")
        print(f"   DSN: {correct_config['hfsql']['dsn']}")
        print(f"   Host: {correct_config['hfsql']['host']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la correction: {e}")
        return False

def test_data_demo_connection():
    """Teste la connexion à DATA_DEMO"""
    print("\n🔌 Test de connexion à DATA_DEMO...")
    
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
    
    from services.connex import connect_to_hfsql, load_credentials
    
    creds = load_credentials()
    if not creds or "hfsql" not in creds:
        print("❌ Configuration non trouvée")
        return False
    
    hfsql_config = creds["hfsql"]
    host_value = f"DSN={hfsql_config['dsn']}" if hfsql_config.get("dsn") else hfsql_config.get("host", "localhost")
    
    print(f"   DSN: {hfsql_config.get('dsn')}")
    print(f"   Base: {hfsql_config.get('database')}")
    
    conn = connect_to_hfsql(
        host_value,
        hfsql_config.get("user", "admin"),
        hfsql_config.get("password", ""),
        hfsql_config.get("database", "HFSQL"),
        hfsql_config.get("port", "4900")
    )
    
    if conn:
        print("✅ Connexion à DATA_DEMO réussie")
        
        try:
            cursor = conn.cursor()
            
            # Tester la table REPARAT
            cursor.execute("SELECT COUNT(*) FROM REPARAT")
            result = cursor.fetchone()
            reparat_count = result[0] if result else 0
            print(f"   📊 REPARAT: {reparat_count} enregistrements")
            
            # Tester la table CLIENT
            cursor.execute("SELECT COUNT(*) FROM CLIENT")
            result = cursor.fetchone()
            client_count = result[0] if result else 0
            print(f"   📊 CLIENT: {client_count} enregistrements")
            
            if reparat_count > 0:
                print("   🎯 Données trouvées dans REPARAT !")
                cursor.execute("SELECT TOP 3 R1CLEUNIK, NUMEROR, CODE, NOM FROM REPARAT")
                sample_data = cursor.fetchall()
                if sample_data:
                    columns = [description[0] for description in cursor.description]
                    from tabulate import tabulate
                    table = tabulate(sample_data, headers=columns, tablefmt="grid", stralign="left")
                    print(f"   📄 Aperçu des données REPARAT:")
                    print(table)
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"   ❌ Erreur lors du test: {e}")
            if conn:
                conn.close()
            return False
        
        return True
    else:
        print("❌ Échec de la connexion à DATA_DEMO")
        return False

def main():
    """Fonction principale"""
    print("🚀 Correction de la configuration de base de données")
    print("=" * 60)
    
    # Étape 1: Corriger la configuration
    if fix_database_config():
        print("\n✅ Configuration corrigée avec succès!")
        
        # Étape 2: Tester la connexion
        if test_data_demo_connection():
            print("\n🎉 Configuration et test réussis!")
            print("\n📋 Maintenant vous pouvez:")
            print("1. Aller sur http://localhost:8000/configuration")
            print("2. Cliquer sur 'Test requête REPARAT'")
            print("3. Voir les données de la table REPARAT de DATA_DEMO")
        else:
            print("\n❌ Problème avec la connexion à DATA_DEMO")
    else:
        print("\n❌ Échec de la correction de la configuration")

if __name__ == "__main__":
    main()
