#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour vérifier toutes les bases de données HFSQL disponibles
"""

import sys
import os
from tabulate import tabulate

# Ajouter le répertoire app au path pour importer les modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.connex import connect_to_hfsql, load_credentials

def check_all_databases():
    """Vérifie toutes les bases de données HFSQL disponibles"""
    print("🔍 Vérification de toutes les bases de données HFSQL")
    print("=" * 60)
    
    # Charger la configuration
    creds = load_credentials()
    if not creds or creds.get("software") != "codial" or "hfsql" not in creds:
        print("❌ Configuration HFSQL non trouvée")
        return False
    
    hfsql_config = creds["hfsql"]
    host_value = f"DSN={hfsql_config['dsn']}" if hfsql_config.get("dsn") else hfsql_config.get("host", "localhost")
    
    print(f"🔌 Connexion à HFSQL...")
    print(f"   DSN: {hfsql_config.get('dsn')}")
    print(f"   Base actuelle: {hfsql_config.get('database')}")
    
    # Bases de données à tester (basées sur votre capture d'écran)
    databases_to_test = [
        "DATA_DEMO",
        "DATA_DEMO_FORM", 
        "DATAV18",
        "DEMO",
        "DEMO18",
        "ESPE-PROD",
        "JL EMBALLAGE"
    ]
    
    results = []
    
    for db_name in databases_to_test:
        print(f"\n📊 Test de la base: {db_name}")
        
        try:
            # Tenter de se connecter à cette base
            conn = connect_to_hfsql(
                host_value,
                hfsql_config.get("user", "admin"),
                hfsql_config.get("password", ""),
                db_name,
                hfsql_config.get("port", "4900")
            )
            
            if conn:
                print(f"   ✅ Connexion réussie à {db_name}")
                
                try:
                    cursor = conn.cursor()
                    
                    # Tester la table REPARAT
                    cursor.execute("SELECT COUNT(*) FROM REPARAT")
                    result = cursor.fetchone()
                    reparat_count = result[0] if result else 0
                    
                    # Tester la table CLIENT
                    cursor.execute("SELECT COUNT(*) FROM CLIENT")
                    result = cursor.fetchone()
                    client_count = result[0] if result else 0
                    
                    results.append({
                        "Base": db_name,
                        "REPARAT": reparat_count,
                        "CLIENT": client_count,
                        "Status": "✅ Connectée"
                    })
                    
                    print(f"   📋 REPARAT: {reparat_count} enregistrements")
                    print(f"   📋 CLIENT: {client_count} enregistrements")
                    
                    # Si REPARAT a des données, afficher un aperçu
                    if reparat_count > 0:
                        print(f"   🎯 Données trouvées dans REPARAT !")
                        try:
                            cursor.execute("SELECT TOP 3 R1CLEUNIK, NUMEROR, CODE, NOM FROM REPARAT")
                            sample_data = cursor.fetchall()
                            if sample_data:
                                columns = [description[0] for description in cursor.description]
                                table = tabulate(sample_data, headers=columns, tablefmt="grid", stralign="left")
                                print(f"   📄 Aperçu des données:")
                                print(table)
                        except Exception as e:
                            print(f"   ⚠️  Erreur aperçu: {e}")
                    
                    cursor.close()
                    conn.close()
                    
                except Exception as e:
                    print(f"   ❌ Erreur requête: {e}")
                    results.append({
                        "Base": db_name,
                        "REPARAT": "Erreur",
                        "CLIENT": "Erreur", 
                        "Status": "❌ Erreur requête"
                    })
            else:
                print(f"   ❌ Échec connexion à {db_name}")
                results.append({
                    "Base": db_name,
                    "REPARAT": "N/A",
                    "CLIENT": "N/A",
                    "Status": "❌ Non accessible"
                })
                
        except Exception as e:
            print(f"   ❌ Erreur générale: {e}")
            results.append({
                "Base": db_name,
                "REPARAT": "N/A",
                "CLIENT": "N/A",
                "Status": "❌ Erreur"
            })
    
    # Afficher le résumé
    print(f"\n📊 RÉSUMÉ DE TOUTES LES BASES")
    print("=" * 60)
    
    if results:
        table_data = []
        for result in results:
            table_data.append([
                result["Base"],
                result["REPARAT"],
                result["CLIENT"],
                result["Status"]
            ])
        
        table = tabulate(table_data, headers=["Base de données", "REPARAT", "CLIENT", "Status"], tablefmt="grid")
        print(table)
        
        # Trouver la base avec des données REPARAT
        reparat_bases = [r for r in results if isinstance(r["REPARAT"], int) and r["REPARAT"] > 0]
        if reparat_bases:
            print(f"\n🎯 Bases contenant des données REPARAT:")
            for base in reparat_bases:
                print(f"   ✅ {base['Base']}: {base['REPARAT']} enregistrements")
        else:
            print(f"\n⚠️  Aucune base ne contient de données dans REPARAT")
    
    return True

def main():
    """Fonction principale"""
    print("🚀 Vérification complète des bases HFSQL")
    print("=" * 60)
    
    success = check_all_databases()
    
    if success:
        print("\n✅ Vérification terminée!")
    else:
        print("\n❌ Problème lors de la vérification")

if __name__ == "__main__":
    main()
