#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour trouver dans quelle base se trouvent les données REPARAT
"""

import sys
import os
from tabulate import tabulate

# Ajouter le répertoire app au path pour importer les modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.connex import connect_to_hfsql, load_credentials

def find_reparat_data():
    """Trouve dans quelle base se trouvent les données REPARAT"""
    print("🔍 Recherche des données REPARAT dans toutes les bases")
    print("=" * 60)
    
    # Charger la configuration
    creds = load_credentials()
    if not creds or creds.get("software") != "codial" or "hfsql" not in creds:
        print("❌ Configuration HFSQL non trouvée")
        return False
    
    hfsql_config = creds["hfsql"]
    host_value = f"DSN={hfsql_config['dsn']}" if hfsql_config.get("dsn") else hfsql_config.get("host", "localhost")
    
    # Bases de données à tester
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
                        print(f"   🎯 DONNÉES TROUVÉES DANS REPARAT !")
                        try:
                            cursor.execute("SELECT TOP 3 R1CLEUNIK, NUMEROR, CODE, NOM, ADRESSE1, VILLE FROM REPARAT")
                            sample_data = cursor.fetchall()
                            if sample_data:
                                columns = [description[0] for description in cursor.description]
                                table = tabulate(sample_data, headers=columns, tablefmt="grid", stralign="left")
                                print(f"   📄 Aperçu des données REPARAT:")
                                print(table)
                                
                                # Vérifier si on trouve des données similaires à votre capture
                                print(f"\n   🔍 Recherche de données spécifiques de votre capture:")
                                
                                # Chercher "ABED (SARL)"
                                cursor.execute("SELECT R1CLEUNIK, NUMEROR, CODE, NOM, ADRESSE1, VILLE FROM REPARAT WHERE NOM LIKE '%ABED%'")
                                abed_results = cursor.fetchall()
                                if abed_results:
                                    print(f"   ✅ Trouvé 'ABED': {abed_results[0]}")
                                
                                # Chercher "DANIERE FLORENCE"
                                cursor.execute("SELECT R1CLEUNIK, NUMEROR, CODE, NOM, ADRESSE1, VILLE FROM REPARAT WHERE NOM LIKE '%DANIERE%'")
                                daniere_results = cursor.fetchall()
                                if daniere_results:
                                    print(f"   ✅ Trouvé 'DANIERE': {daniere_results[0]}")
                                
                                # Chercher "DURAND ALAIN"
                                cursor.execute("SELECT R1CLEUNIK, NUMEROR, CODE, NOM, ADRESSE1, VILLE FROM REPARAT WHERE NOM LIKE '%DURAND%'")
                                durand_results = cursor.fetchall()
                                if durand_results:
                                    print(f"   ✅ Trouvé 'DURAND': {durand_results[0]}")
                                
                                print(f"\n   🎯 BASE TROUVÉE: {db_name} contient les données REPARAT!")
                                return db_name
                                
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
            return reparat_bases[0]['Base']
        else:
            print(f"\n⚠️  Aucune base ne contient de données dans REPARAT")
            return None
    
    return None

def main():
    """Fonction principale"""
    print("🚀 Recherche des données REPARAT")
    print("=" * 60)
    
    found_base = find_reparat_data()
    
    if found_base:
        print(f"\n🎉 Base trouvée: {found_base}")
        print("💡 Il faut maintenant configurer l'application pour utiliser cette base.")
    else:
        print("\n❌ Aucune base ne contient les données REPARAT")
        print("💡 Vérifiez que les données existent vraiment dans HFSQL.")

if __name__ == "__main__":
    main()
