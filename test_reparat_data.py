#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour tester la récupération des données de la table REPARAT
"""

import sys
import os
from tabulate import tabulate

# Ajouter le répertoire app au path pour importer les modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.connex import connect_to_hfsql, load_credentials

def test_reparat_data():
    """Teste la récupération des données de la table REPARAT"""
    print("🔍 Test des données de la table REPARAT")
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
        
        # Test 2: Récupérer les colonnes disponibles
        print("\n📋 Test 2: Structure de la table")
        try:
            cursor.execute("SELECT TOP 1 * FROM REPARAT")
            columns = [description[0] for description in cursor.description]
            print(f"   ✅ Colonnes trouvées: {len(columns)}")
            print(f"   📝 Colonnes: {', '.join(columns)}")
        except Exception as e:
            print(f"   ❌ Erreur structure: {e}")
            return False
        
        # Test 3: Récupérer quelques enregistrements
        print("\n📄 Test 3: Récupération des données")
        queries_to_try = [
            "SELECT TOP 5 R1CLEUNIK, NUMEROR, CODE, NOM FROM REPARAT",
            "SELECT TOP 3 R1CLEUNIK, NUMEROR, CODE, NOM, ADRESSE1, VILLE FROM REPARAT",
            "SELECT TOP 2 * FROM REPARAT"
        ]
        
        for i, query in enumerate(queries_to_try, 1):
            try:
                print(f"\n   Requête {i}: {query}")
                cursor.execute(query)
                results = cursor.fetchall()
                
                if results:
                    columns = [description[0] for description in cursor.description]
                    print(f"   ✅ {len(results)} enregistrement(s) récupéré(s)")
                    
                    # Afficher les résultats dans un tableau
                    print(f"\n   📊 Résultats:")
                    table = tabulate(results, headers=columns, tablefmt="grid", stralign="left")
                    print(table)
                    
                    # Si on a réussi, on s'arrête ici
                    break
                else:
                    print(f"   ⚠️  Aucun résultat")
                    
            except Exception as e:
                print(f"   ❌ Erreur requête {i}: {e}")
                continue
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Test terminé avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        if conn:
            conn.close()
        return False

def main():
    """Fonction principale"""
    print("🚀 Test des données REPARAT")
    print("=" * 50)
    
    success = test_reparat_data()
    
    if success:
        print("\n✅ Les données sont accessibles!")
        print("💡 Le problème vient probablement de l'interface web.")
        print("   Vérifiez que le serveur web fonctionne et testez la route /query-hfsql-reparat")
    else:
        print("\n❌ Problème d'accès aux données")
        print("💡 Vérifiez la configuration HFSQL")

if __name__ == "__main__":
    main()
