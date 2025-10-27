#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script final pour tester la table REPARAT avec contournement des erreurs de version
"""

import sys
import os
from tabulate import tabulate

# Ajouter le répertoire app au path pour importer les modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.connex import connect_to_hfsql, load_credentials

def test_reparat_final():
    """Teste la table REPARAT avec différentes approches"""
    print("🔍 Test final de la table REPARAT")
    print("=" * 50)
    
    # Charger la configuration
    creds = load_credentials()
    if not creds or creds.get("software") != "codial" or "hfsql" not in creds:
        print("❌ Configuration HFSQL non trouvée")
        return False
    
    hfsql_config = creds["hfsql"]
    host_value = f"DSN={hfsql_config['dsn']}" if hfsql_config.get("dsn") else hfsql_config.get("host", "localhost")
    
    print(f"🔌 Connexion à HFSQL...")
    print(f"   DSN: {hfsql_config.get('dsn')}")
    print(f"   Base: {hfsql_config.get('database')}")
    
    conn = connect_to_hfsql(
        host_value,
        hfsql_config.get("user", "admin"),
        hfsql_config.get("password", ""),
        hfsql_config.get("database", "HFSQL"),
        hfsql_config.get("port", "4900")
    )
    
    if not conn:
        print("❌ Échec de la connexion")
        return False
    
    print("✅ Connexion réussie")
    
    try:
        cursor = conn.cursor()
        
        # Test 1: Compter les enregistrements
        print("\n📊 Test 1: Compter les enregistrements")
        try:
            cursor.execute("SELECT COUNT(*) as total FROM REPARAT")
            result = cursor.fetchone()
            count = result[0] if result else 0
            print(f"   ✅ Nombre d'enregistrements: {count}")
        except Exception as e:
            print(f"   ❌ Erreur comptage: {e}")
            return False
        
        # Test 2: Récupérer la structure
        print("\n📋 Test 2: Structure de la table")
        try:
            cursor.execute("SELECT TOP 1 * FROM REPARAT")
            columns = [description[0] for description in cursor.description]
            print(f"   ✅ Colonnes trouvées: {len(columns)}")
            print(f"   📝 Premières colonnes: {', '.join(columns[:10])}")
        except Exception as e:
            print(f"   ❌ Erreur structure: {e}")
            return False
        
        # Test 3: Récupérer des données avec différentes approches
        print("\n📄 Test 3: Récupération des données")
        
        # Approche 1: Requête simple avec colonnes spécifiques
        try:
            print("   Approche 1: Colonnes spécifiques")
            cursor.execute("SELECT TOP 3 R1CLEUNIK, NUMEROR, CODE, NOM FROM REPARAT")
            results = cursor.fetchall()
            
            if results:
                columns = [description[0] for description in cursor.description]
                print(f"   ✅ {len(results)} enregistrement(s) récupéré(s)")
                
                table = tabulate(results, headers=columns, tablefmt="grid", stralign="left")
                print(table)
                return True
            else:
                print("   ⚠️  Aucun résultat")
        except Exception as e:
            print(f"   ❌ Erreur approche 1: {e}")
        
        # Approche 2: Requête avec CAST pour éviter les erreurs de conversion
        try:
            print("\n   Approche 2: Avec CAST")
            cursor.execute("SELECT TOP 3 CAST(R1CLEUNIK AS VARCHAR(50)), CAST(NUMEROR AS VARCHAR(50)), CODE, NOM FROM REPARAT")
            results = cursor.fetchall()
            
            if results:
                columns = [description[0] for description in cursor.description]
                print(f"   ✅ {len(results)} enregistrement(s) récupéré(s)")
                
                table = tabulate(results, headers=columns, tablefmt="grid", stralign="left")
                print(table)
                return True
            else:
                print("   ⚠️  Aucun résultat")
        except Exception as e:
            print(f"   ❌ Erreur approche 2: {e}")
        
        # Approche 3: Requête avec ISNULL pour gérer les valeurs NULL
        try:
            print("\n   Approche 3: Avec ISNULL")
            cursor.execute("SELECT TOP 3 ISNULL(CAST(R1CLEUNIK AS VARCHAR(50)), ''), ISNULL(CAST(NUMEROR AS VARCHAR(50)), ''), ISNULL(CODE, ''), ISNULL(NOM, '') FROM REPARAT")
            results = cursor.fetchall()
            
            if results:
                columns = [description[0] for description in cursor.description]
                print(f"   ✅ {len(results)} enregistrement(s) récupéré(s)")
                
                table = tabulate(results, headers=columns, tablefmt="grid", stralign="left")
                print(table)
                return True
            else:
                print("   ⚠️  Aucun résultat")
        except Exception as e:
            print(f"   ❌ Erreur approche 3: {e}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Test terminé!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        if conn:
            conn.close()
        return False

def main():
    """Fonction principale"""
    print("🚀 Test final de la table REPARAT")
    print("=" * 50)
    
    success = test_reparat_final()
    
    if success:
        print("\n✅ Les données de REPARAT sont accessibles!")
        print("💡 Vous pouvez maintenant utiliser l'interface web pour voir les résultats.")
    else:
        print("\n❌ Problème d'accès aux données REPARAT")
        print("💡 Vérifiez la configuration HFSQL ou contactez l'administrateur.")

if __name__ == "__main__":
    main()
