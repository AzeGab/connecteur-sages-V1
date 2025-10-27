#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour exécuter une requête HFSQL et afficher les résultats
Requête: SELECT * FROM REPARAT
"""

import sys
import os
from tabulate import tabulate

# Ajouter le répertoire app au path pour importer les modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.connex import connect_to_hfsql

def execute_hfsql_query():
    """Exécute la requête SELECT * FROM REPARAT sur HFSQL"""
    print("=" * 80)
    print("REQUÊTE HFSQL : SELECT * FROM REPARAT")
    print("=" * 80)
    print()
    
    # Connexion HFSQL via DSN (qui fonctionne)
    print("Connexion à HFSQL via DSN 'HFSQL_LOCAL'...")
    conn = connect_to_hfsql("DSN=HFSQL_LOCAL")
    
    if not conn:
        print("❌ Échec de la connexion HFSQL")
        return False
    
    print("✅ Connexion HFSQL réussie")
    print()
    
    try:
        # Exécution de la requête
        print("Exécution de la requête: SELECT * FROM REPARAT")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM REPARAT")
        
        # Récupération des résultats
        results = cursor.fetchall()
        
        if not results:
            print("⚠️  Aucun résultat trouvé dans la table REPARAT")
            cursor.close()
            conn.close()
            return True
        
        # Récupération des noms de colonnes
        columns = [description[0] for description in cursor.description]
        
        print(f"✅ {len(results)} enregistrement(s) trouvé(s)")
        print()
        
        # Affichage des résultats dans un tableau
        print("📊 RÉSULTATS DE LA REQUÊTE")
        print("-" * 80)
        
        # Création du tableau avec tabulate
        table = tabulate(results, headers=columns, tablefmt="grid", stralign="left")
        print(table)
        
        # Statistiques
        print()
        print("📈 STATISTIQUES")
        print("-" * 40)
        print(f"Nombre de colonnes: {len(columns)}")
        print(f"Nombre d'enregistrements: {len(results)}")
        print(f"Colonnes: {', '.join(columns)}")
        
        cursor.close()
        conn.close()
        
        print()
        print("✅ Requête exécutée avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution de la requête: {e}")
        if conn:
            conn.close()
        return False

def main():
    """Fonction principale"""
    print("🔍 DIAGNOSTIC REQUÊTE HFSQL")
    print("Table: REPARAT")
    print("Requête: SELECT * FROM REPARAT")
    print()
    
    success = execute_hfsql_query()
    
    print()
    print("=" * 80)
    if success:
        print("🎉 DIAGNOSTIC TERMINÉ AVEC SUCCÈS")
    else:
        print("❌ DIAGNOSTIC ÉCHOUÉ")
    print("=" * 80)

if __name__ == "__main__":
    main()
