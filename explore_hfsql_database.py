#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour explorer la base de données HFSQL
Liste les tables et affiche la structure de REPARAT
"""

import sys
import os
from tabulate import tabulate

# Ajouter le répertoire app au path pour importer les modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.connex import connect_to_hfsql

def explore_hfsql_database():
    """Explore la base de données HFSQL"""
    print("=" * 80)
    print("EXPLORATION DE LA BASE DE DONNÉES HFSQL")
    print("=" * 80)
    print()
    
    # Connexion HFSQL via DSN
    print("Connexion à HFSQL via DSN 'HFSQL_LOCAL'...")
    conn = connect_to_hfsql("DSN=HFSQL_LOCAL")
    
    if not conn:
        print("❌ Échec de la connexion HFSQL")
        return False
    
    print("✅ Connexion HFSQL réussie")
    print()
    
    try:
        cursor = conn.cursor()
        
        # 1. Lister les tables disponibles
        print("📋 TABLES DISPONIBLES DANS LA BASE")
        print("-" * 50)
        
        try:
            # Requête pour lister les tables (syntaxe HFSQL)
            cursor.execute("SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'TABLE'")
            tables = cursor.fetchall()
            
            if tables:
                table_headers = [desc[0] for desc in cursor.description]
                table_data = []
                for table in tables:
                    table_data.append([table[0] if len(table) > 0 else "N/A"])
                
                print(tabulate(table_data, headers=["Nom de la table"], tablefmt="grid"))
            else:
                print("Aucune table trouvée via INFORMATION_SCHEMA")
                
        except Exception as e:
            print(f"Erreur lors de la liste des tables: {e}")
            print("Tentative alternative...")
            
            # Méthode alternative pour lister les tables
            try:
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                if tables:
                    table_data = [[table[0]] for table in tables]
                    print(tabulate(table_data, headers=["Nom de la table"], tablefmt="grid"))
                else:
                    print("Aucune table trouvée")
            except Exception as e2:
                print(f"Erreur méthode alternative: {e2}")
        
        print()
        
        # 2. Vérifier si la table REPARAT existe
        print("🔍 VÉRIFICATION DE LA TABLE REPARAT")
        print("-" * 40)
        
        try:
            # Essayer de compter les enregistrements
            cursor.execute("SELECT COUNT(*) FROM REPARAT")
            count_result = cursor.fetchone()
            count = count_result[0] if count_result else 0
            print(f"✅ Table REPARAT trouvée - {count} enregistrement(s)")
            
            if count > 0:
                # Afficher la structure de la table
                print("\n📊 STRUCTURE DE LA TABLE REPARAT")
                print("-" * 40)
                
                try:
                    cursor.execute("DESCRIBE REPARAT")
                    columns = cursor.fetchall()
                    
                    if columns:
                        column_data = []
                        for col in columns:
                            column_data.append([
                                col[0] if len(col) > 0 else "N/A",
                                col[1] if len(col) > 1 else "N/A",
                                col[2] if len(col) > 2 else "N/A",
                                col[3] if len(col) > 3 else "N/A"
                            ])
                        
                        print(tabulate(column_data, 
                                     headers=["Colonne", "Type", "Null", "Clé"], 
                                     tablefmt="grid"))
                    else:
                        print("Impossible de récupérer la structure")
                        
                except Exception as e:
                    print(f"Erreur lors de la récupération de la structure: {e}")
                
                # Afficher les premiers enregistrements
                print(f"\n📋 PREMIERS ENREGISTREMENTS DE REPARAT (limite 10)")
                print("-" * 50)
                
                cursor.execute("SELECT * FROM REPARAT LIMIT 10")
                results = cursor.fetchall()
                
                if results:
                    column_names = [desc[0] for desc in cursor.description]
                    print(tabulate(results, headers=column_names, tablefmt="grid"))
                else:
                    print("Aucun enregistrement à afficher")
            else:
                print("⚠️  La table REPARAT est vide")
                
        except Exception as e:
            print(f"❌ Erreur lors de l'accès à la table REPARAT: {e}")
            
            # Essayer de voir si la table existe avec une requête simple
            try:
                cursor.execute("SELECT 1 FROM REPARAT WHERE 1=0")
                print("✅ La table REPARAT existe mais est vide")
            except Exception as e2:
                print(f"❌ La table REPARAT n'existe pas ou n'est pas accessible: {e2}")
        
        print()
        
        # 3. Informations générales sur la base
        print("ℹ️  INFORMATIONS GÉNÉRALES")
        print("-" * 30)
        print(f"DSN utilisé: HFSQL_LOCAL")
        print(f"Statut de la connexion: Active")
        
        cursor.close()
        conn.close()
        
        print()
        print("✅ Exploration terminée avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        if conn:
            conn.close()
        return False

def main():
    """Fonction principale"""
    print("🔍 EXPLORATEUR DE BASE DE DONNÉES HFSQL")
    print("DSN: HFSQL_LOCAL")
    print()
    
    success = explore_hfsql_database()
    
    print()
    print("=" * 80)
    if success:
        print("🎉 EXPLORATION TERMINÉE AVEC SUCCÈS")
    else:
        print("❌ EXPLORATION ÉCHOUÉE")
    print("=" * 80)

if __name__ == "__main__":
    main()
