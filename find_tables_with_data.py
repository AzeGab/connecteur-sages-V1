#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour trouver toutes les tables contenant des données
"""

import sys
import os
from tabulate import tabulate

# Ajouter le répertoire app au path pour importer les modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.connex import connect_to_hfsql, load_credentials

def find_tables_with_data():
    """Trouve toutes les tables contenant des données"""
    print("🔍 Recherche de toutes les tables avec des données")
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
        
        # Liste des tables à tester (basées sur votre capture d'écran et noms courants)
        tables_to_test = [
            "REPARAT", "REPARATION", "REPARATIONS",
            "CLIENT", "CLIENTS", "CUSTOMER", "CUSTOMERS",
            "CONTACT", "CONTACTS", "PERSONNE", "PERSONNES",
            "DOSSIER", "DOSSIERS", "AFFAIRE", "AFFAIRES",
            "DEVIS", "DEVISES", "FACTURE", "FACTURES",
            "PRODUIT", "PRODUITS", "ARTICLE", "ARTICLES",
            "INTERVENTION", "INTERVENTIONS", "MAINTENANCE",
            "SERVICE", "SERVICES", "TICKET", "TICKETS",
            "ORDRE", "ORDERS", "COMMANDE", "COMMANDES"
        ]
        
        results = []
        
        for table_name in tables_to_test:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                result = cursor.fetchone()
                count = result[0] if result else 0
                
                if count > 0:
                    results.append({
                        "Table": table_name,
                        "Enregistrements": count,
                        "Status": "✅ Données trouvées"
                    })
                    print(f"   ✅ {table_name}: {count} enregistrements")
                    
                    # Si c'est une table qui pourrait contenir les données de votre capture
                    if any(keyword in table_name.upper() for keyword in ['REPARAT', 'INTERVENTION', 'SERVICE', 'TICKET']):
                        print(f"   🎯 Table candidate: {table_name}")
                        try:
                            cursor.execute(f"SELECT TOP 3 * FROM {table_name}")
                            sample_data = cursor.fetchall()
                            if sample_data:
                                columns = [description[0] for description in cursor.description]
                                print(f"   📄 Aperçu des colonnes: {', '.join(columns[:10])}")
                                
                                # Vérifier si les colonnes correspondent à votre capture
                                expected_columns = ['r1cleunik', 'numeror', 'code', 'nom', 'adresse1', 'ville']
                                found_columns = [col.lower() for col in columns]
                                matching_columns = [col for col in expected_columns if col in found_columns]
                                
                                if len(matching_columns) >= 3:
                                    print(f"   🎯 COLONNES CORRESPONDANTES: {matching_columns}")
                                    print(f"   📊 Aperçu des données:")
                                    table = tabulate(sample_data[:3], headers=columns[:8], tablefmt="grid", stralign="left")
                                    print(table)
                        except Exception as e:
                            print(f"   ⚠️  Erreur aperçu: {e}")
                
            except Exception as e:
                # Table n'existe pas ou erreur
                continue
        
        # Afficher le résumé
        print(f"\n📊 RÉSUMÉ DES TABLES AVEC DONNÉES")
        print("=" * 60)
        
        if results:
            table_data = []
            for result in results:
                table_data.append([
                    result["Table"],
                    result["Enregistrements"],
                    result["Status"]
                ])
            
            table = tabulate(table_data, headers=["Table", "Enregistrements", "Status"], tablefmt="grid")
            print(table)
        else:
            print("⚠️  Aucune table avec des données trouvée")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Recherche terminée!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        if conn:
            conn.close()
        return False

def main():
    """Fonction principale"""
    print("🚀 Recherche de toutes les tables avec des données")
    print("=" * 60)
    
    success = find_tables_with_data()
    
    if success:
        print("\n✅ Recherche terminée avec succès!")
    else:
        print("\n❌ Problème lors de la recherche")

if __name__ == "__main__":
    main()
