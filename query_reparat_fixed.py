#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script corrigé pour exécuter la requête HFSQL sur la base configurée
Requête: SELECT * FROM REPARAT avec gestion des erreurs
"""

import sys
import os
from tabulate import tabulate

# Ajouter le répertoire app au path pour importer les modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.connex import connect_to_hfsql, load_credentials

def execute_reparat_query():
    """Exécute la requête SELECT * FROM REPARAT avec gestion d'erreurs"""
    print("=" * 80)
    print("REQUÊTE HFSQL : SELECT * FROM REPARAT")
    print("Base de données: Configuration du formulaire")
    print("=" * 80)
    print()
    
    # Charger la configuration
    creds = load_credentials()
    if not creds or creds.get("software") != "codial" or "hfsql" not in creds:
        print("❌ Configuration HFSQL non trouvée")
        return False
    
    hfsql_config = creds["hfsql"]
    print("🔧 CONFIGURATION UTILISÉE")
    print("-" * 30)
    print(f"Logiciel: {creds.get('software')}")
    print(f"Host/DSN: {hfsql_config.get('host')}")
    print(f"Utilisateur: {hfsql_config.get('user')}")
    print(f"Base: {hfsql_config.get('database')}")
    print(f"Port: {hfsql_config.get('port')}")
    print()
    
    # Connexion
    host_value = f"DSN={hfsql_config['dsn']}" if hfsql_config.get("dsn") else hfsql_config.get("host", "localhost")
    
    print("🔌 Connexion à HFSQL...")
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
    print()
    
    try:
        cursor = conn.cursor()
        
        # Essayer différentes requêtes pour éviter les erreurs de conversion
        queries_to_try = [
            "SELECT * FROM REPARAT",
            "SELECT TOP 10 * FROM REPARAT",
            "SELECT COUNT(*) as total FROM REPARAT",
            "SELECT * FROM REPARAT WHERE 1=1"
        ]
        
        for i, query in enumerate(queries_to_try, 1):
            print(f"📊 Tentative {i}: {query}")
            try:
                cursor.execute(query)
                results = cursor.fetchall()
                
                if not results:
                    print(f"   ⚠️  Aucun résultat pour la requête {i}")
                    continue
                
                # Récupérer les colonnes
                columns = [description[0] for description in cursor.description]
                
                print(f"   ✅ {len(results)} enregistrement(s) trouvé(s)")
                print(f"   📋 Colonnes: {', '.join(columns)}")
                
                # Afficher les résultats
                print(f"\n📋 RÉSULTATS DE LA REQUÊTE {i}")
                print("-" * 50)
                
                # Limiter l'affichage pour éviter les tableaux trop longs
                display_results = results[:20] if len(results) > 20 else results
                
                table = tabulate(display_results, headers=columns, tablefmt="grid", stralign="left")
                print(table)
                
                if len(results) > 20:
                    print(f"\n... et {len(results) - 20} autres enregistrements")
                
                # Statistiques
                print(f"\n📈 STATISTIQUES")
                print("-" * 20)
                print(f"Total d'enregistrements: {len(results)}")
                print(f"Colonnes: {len(columns)}")
                print(f"Colonnes: {', '.join(columns)}")
                
                cursor.close()
                conn.close()
                
                print(f"\n✅ Requête {i} exécutée avec succès!")
                return True
                
            except Exception as e:
                print(f"   ❌ Erreur requête {i}: {str(e)[:100]}...")
                continue
        
        # Si aucune requête n'a fonctionné
        print("\n❌ Toutes les requêtes ont échoué")
        cursor.close()
        conn.close()
        return False
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        if conn:
            conn.close()
        return False

def main():
    """Fonction principale"""
    print("🔍 REQUÊTE HFSQL AVEC CONFIGURATION FORMULAIRE")
    print("Table: REPARAT")
    print("Base: Configuration sauvegardée")
    print()
    
    success = execute_reparat_query()
    
    print()
    print("=" * 80)
    if success:
        print("🎉 REQUÊTE EXÉCUTÉE AVEC SUCCÈS")
        print("✅ Données récupérées depuis votre base configurée")
    else:
        print("❌ ÉCHEC DE LA REQUÊTE")
        print("💡 Vérifiez que la table REPARAT existe et contient des données")
    print("=" * 80)

if __name__ == "__main__":
    main()
