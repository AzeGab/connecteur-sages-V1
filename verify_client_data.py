#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour vérifier si les données de la capture correspondent à la table CLIENT
"""

import sys
import os
from tabulate import tabulate

# Ajouter le répertoire app au path pour importer les modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.connex import connect_to_hfsql, load_credentials

def verify_client_data():
    """Vérifie si les données de la capture correspondent à la table CLIENT"""
    print("🔍 Vérification des données de la table CLIENT")
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
        
        # Vérifier la structure de la table CLIENT
        print("\n📋 Structure de la table CLIENT")
        cursor.execute("SELECT TOP 1 * FROM CLIENT")
        columns = [description[0] for description in cursor.description]
        print(f"   📝 Nombre de colonnes: {len(columns)}")
        print(f"   📝 Premières colonnes: {', '.join(columns[:15])}")
        
        # Vérifier si les colonnes correspondent à votre capture
        expected_columns = ['r1cleunik', 'numeror', 'code', 'genre', 'nom', 'adresse1', 'adresse2', 'cop', 'ville', 'marque', 'type']
        found_columns = [col.lower() for col in columns]
        matching_columns = [col for col in expected_columns if col in found_columns]
        
        print(f"\n🎯 Colonnes correspondantes à votre capture:")
        print(f"   ✅ Trouvées: {matching_columns}")
        print(f"   ❌ Manquantes: {[col for col in expected_columns if col not in found_columns]}")
        
        if len(matching_columns) >= 8:  # Au moins 8 colonnes correspondent
            print(f"\n🎉 La table CLIENT semble correspondre à vos données!")
            
            # Récupérer quelques enregistrements pour vérification
            print(f"\n📊 Aperçu des données CLIENT:")
            try:
                cursor.execute("SELECT TOP 5 R1CLEUNIK, NUMEROR, CODE, NOM, ADRESSE1, VILLE FROM CLIENT")
                results = cursor.fetchall()
                
                if results:
                    columns_display = [description[0] for description in cursor.description]
                    table = tabulate(results, headers=columns_display, tablefmt="grid", stralign="left")
                    print(table)
                    
                    # Vérifier si on trouve des données similaires à votre capture
                    print(f"\n🔍 Recherche de données spécifiques de votre capture:")
                    
                    # Chercher "ABED (SARL)"
                    cursor.execute("SELECT R1CLEUNIK, NUMEROR, CODE, NOM, ADRESSE1, VILLE FROM CLIENT WHERE NOM LIKE '%ABED%'")
                    abed_results = cursor.fetchall()
                    if abed_results:
                        print(f"   ✅ Trouvé 'ABED': {abed_results[0]}")
                    
                    # Chercher "DANIERE FLORENCE"
                    cursor.execute("SELECT R1CLEUNIK, NUMEROR, CODE, NOM, ADRESSE1, VILLE FROM CLIENT WHERE NOM LIKE '%DANIERE%'")
                    daniere_results = cursor.fetchall()
                    if daniere_results:
                        print(f"   ✅ Trouvé 'DANIERE': {daniere_results[0]}")
                    
                    # Chercher "DURAND ALAIN"
                    cursor.execute("SELECT R1CLEUNIK, NUMEROR, CODE, NOM, ADRESSE1, VILLE FROM CLIENT WHERE NOM LIKE '%DURAND%'")
                    durand_results = cursor.fetchall()
                    if durand_results:
                        print(f"   ✅ Trouvé 'DURAND': {durand_results[0]}")
                    
                    print(f"\n🎯 CONCLUSION: Les données de votre capture sont dans la table CLIENT, pas REPARAT!")
                    print(f"   💡 Il faut modifier la requête pour utiliser SELECT * FROM CLIENT")
                    
                else:
                    print("   ⚠️  Aucun résultat trouvé")
                    
            except Exception as e:
                print(f"   ❌ Erreur lors de la récupération des données: {e}")
        else:
            print(f"\n⚠️  La table CLIENT ne correspond pas exactement à vos données")
            print(f"   📝 Colonnes attendues: {expected_columns}")
            print(f"   📝 Colonnes trouvées: {found_columns}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Vérification terminée!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        if conn:
            conn.close()
        return False

def main():
    """Fonction principale"""
    print("🚀 Vérification des données CLIENT")
    print("=" * 60)
    
    success = verify_client_data()
    
    if success:
        print("\n✅ Vérification terminée avec succès!")
    else:
        print("\n❌ Problème lors de la vérification")

if __name__ == "__main__":
    main()
