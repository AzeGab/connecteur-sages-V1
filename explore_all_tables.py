#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour explorer toutes les tables de la base HFSQL
"""

import sys
import os
from tabulate import tabulate

# Ajouter le répertoire app au path pour importer les modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.connex import connect_to_hfsql, load_credentials

def explore_all_tables():
    """Explore toutes les tables de la base HFSQL"""
    print("🔍 Exploration de toutes les tables HFSQL")
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
        
        # Test 1: Lister toutes les tables
        print("\n📋 Test 1: Recherche de tables")
        table_queries = [
            "SELECT * FROM INFORMATION_SCHEMA.TABLES",
            "SHOW TABLES",
            "SELECT name FROM sys.tables",
            "SELECT table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE'"
        ]
        
        tables_found = []
        for i, query in enumerate(table_queries, 1):
            try:
                print(f"   Requête {i}: {query}")
                cursor.execute(query)
                results = cursor.fetchall()
                
                if results:
                    print(f"   ✅ {len(results)} table(s) trouvée(s)")
                    tables_found.extend([row[0] for row in results])
                    break
                else:
                    print(f"   ⚠️  Aucun résultat")
                    
            except Exception as e:
                print(f"   ❌ Erreur requête {i}: {e}")
                continue
        
        if not tables_found:
            print("   ℹ️  Aucune table trouvée via les requêtes standard")
            print("   🔍 Test de tables connues...")
            
            # Tester des noms de tables courants
            common_tables = [
                "REPARAT", "REPARATION", "REPARATIONS", 
                "CLIENT", "CLIENTS", "CUSTOMER", "CUSTOMERS",
                "CONTACT", "CONTACTS", "PERSONNE", "PERSONNES",
                "DOSSIER", "DOSSIERS", "AFFAIRE", "AFFAIRES",
                "DEVIS", "DEVISES", "FACTURE", "FACTURES",
                "PRODUIT", "PRODUITS", "ARTICLE", "ARTICLES"
            ]
            
            for table_name in common_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    result = cursor.fetchone()
                    count = result[0] if result else 0
                    if count > 0:
                        print(f"   ✅ Table {table_name}: {count} enregistrements")
                        tables_found.append(table_name)
                    else:
                        print(f"   ⚠️  Table {table_name}: vide")
                except Exception as e:
                    print(f"   ❌ Table {table_name}: {e}")
        
        # Test 2: Analyser les tables trouvées
        if tables_found:
            print(f"\n📊 Test 2: Analyse des tables trouvées")
            for table_name in tables_found[:5]:  # Limiter à 5 tables
                try:
                    print(f"\n   Table: {table_name}")
                    
                    # Compter les enregistrements
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    result = cursor.fetchone()
                    count = result[0] if result else 0
                    print(f"   📊 Enregistrements: {count}")
                    
                    if count > 0:
                        # Récupérer la structure
                        cursor.execute(f"SELECT TOP 1 * FROM {table_name}")
                        columns = [description[0] for description in cursor.description]
                        print(f"   📝 Colonnes: {len(columns)}")
                        
                        # Afficher quelques colonnes clés
                        key_columns = [col for col in columns if any(keyword in col.lower() for keyword in ['nom', 'name', 'code', 'id', 'cleunik', 'numero'])]
                        if key_columns:
                            print(f"   🔑 Colonnes clés: {', '.join(key_columns[:5])}")
                        
                        # Récupérer quelques enregistrements
                        if count <= 100:
                            cursor.execute(f"SELECT TOP 3 * FROM {table_name}")
                            results = cursor.fetchall()
                            
                            if results:
                                print(f"   📄 Aperçu des données:")
                                # Afficher seulement les premières colonnes
                                display_columns = columns[:6]  # Limiter à 6 colonnes
                                display_results = [row[:6] for row in results]
                                table = tabulate(display_results, headers=display_columns, tablefmt="grid", stralign="left")
                                print(table)
                        
                except Exception as e:
                    print(f"   ❌ Erreur analyse {table_name}: {e}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Exploration terminée!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        if conn:
            conn.close()
        return False

def main():
    """Fonction principale"""
    print("🚀 Exploration complète de la base HFSQL")
    print("=" * 50)
    
    success = explore_all_tables()
    
    if success:
        print("\n✅ Exploration terminée avec succès!")
    else:
        print("\n❌ Problème lors de l'exploration")

if __name__ == "__main__":
    main()
