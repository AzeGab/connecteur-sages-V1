#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour exécuter une requête HFSQL en utilisant la configuration du formulaire
Requête: SELECT * FROM REPARAT
"""

import sys
import os
from tabulate import tabulate

# Ajouter le répertoire app au path pour importer les modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.connex import connect_to_hfsql, load_credentials

def execute_query_with_form_config():
    """Exécute la requête en utilisant la configuration du formulaire"""
    print("=" * 80)
    print("REQUÊTE HFSQL AVEC CONFIGURATION DU FORMULAIRE")
    print("=" * 80)
    print()
    
    # Charger la configuration sauvegardée
    print("📋 Chargement de la configuration du formulaire...")
    creds = load_credentials()
    
    if not creds:
        print("❌ Aucune configuration trouvée dans credentials.json")
        print("Veuillez d'abord configurer la connexion via le formulaire web")
        return False
    
    print("✅ Configuration chargée")
    print()
    
    # Afficher la configuration
    print("🔧 CONFIGURATION UTILISÉE")
    print("-" * 40)
    
    software = creds.get("software", "batigest")
    print(f"Logiciel: {software}")
    
    if software == "codial" and "hfsql" in creds:
        hfsql_config = creds["hfsql"]
        print(f"Type de connexion: HFSQL")
        print(f"Host/DSN: {hfsql_config.get('host', 'Non défini')}")
        print(f"Utilisateur: {hfsql_config.get('user', 'Non défini')}")
        print(f"Base de données: {hfsql_config.get('database', 'Non défini')}")
        print(f"Port: {hfsql_config.get('port', 'Non défini')}")
        
        # Connexion HFSQL
        host_value = f"DSN={hfsql_config['dsn']}" if hfsql_config.get("dsn") else hfsql_config.get("host", "localhost")
        
        print(f"\n🔌 Connexion à HFSQL...")
        print(f"Paramètres: {host_value}")
        
        conn = connect_to_hfsql(
            host_value,
            hfsql_config.get("user", "admin"),
            hfsql_config.get("password", ""),
            hfsql_config.get("database", "HFSQL"),
            hfsql_config.get("port", "4900")
        )
        
    elif software == "batigest" and "sqlserver" in creds:
        print("❌ Configuration SQL Server détectée, mais requête HFSQL demandée")
        print("Veuillez configurer Codial avec HFSQL pour exécuter cette requête")
        return False
    else:
        print("❌ Configuration HFSQL non trouvée")
        return False
    
    if not conn:
        print("❌ Échec de la connexion HFSQL")
        return False
    
    print("✅ Connexion HFSQL réussie")
    print()
    
    try:
        # Exécution de la requête
        print("📊 EXÉCUTION DE LA REQUÊTE")
        print("-" * 30)
        print("Requête: SELECT * FROM REPARAT")
        print()
        
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM REPARAT")
        
        # Récupération des résultats
        results = cursor.fetchall()
        
        if not results:
            print("⚠️  Aucun résultat trouvé dans la table REPARAT")
            print("La table existe mais est vide")
        else:
            # Récupération des noms de colonnes
            columns = [description[0] for description in cursor.description]
            
            print(f"✅ {len(results)} enregistrement(s) trouvé(s)")
            print()
            
            # Affichage des résultats dans un tableau
            print("📋 RÉSULTATS DE LA REQUÊTE")
            print("-" * 50)
            
            # Création du tableau avec tabulate
            table = tabulate(results, headers=columns, tablefmt="grid", stralign="left")
            print(table)
            
            # Statistiques
            print()
            print("📈 STATISTIQUES")
            print("-" * 20)
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

def show_configuration_status():
    """Affiche le statut de la configuration"""
    print("🔍 VÉRIFICATION DE LA CONFIGURATION")
    print("-" * 40)
    
    creds = load_credentials()
    if not creds:
        print("❌ Aucune configuration trouvée")
        print("💡 Accédez à http://localhost:8000 pour configurer la connexion")
        return False
    
    software = creds.get("software", "batigest")
    print(f"✅ Configuration trouvée - Logiciel: {software}")
    
    if software == "codial":
        if "hfsql" in creds:
            hfsql_config = creds["hfsql"]
            print(f"✅ Configuration HFSQL trouvée")
            print(f"   Host/DSN: {hfsql_config.get('host', 'Non défini')}")
            print(f"   Base: {hfsql_config.get('database', 'Non défini')}")
        else:
            print("❌ Configuration HFSQL manquante")
            return False
    else:
        print(f"⚠️  Logiciel configuré: {software} (HFSQL requis)")
        return False
    
    return True

def main():
    """Fonction principale"""
    print("🔍 REQUÊTE HFSQL AVEC CONFIGURATION FORMULAIRE")
    print("Table: REPARAT")
    print("Configuration: Depuis credentials.json")
    print()
    
    # Vérifier la configuration
    if not show_configuration_status():
        print()
        print("💡 SOLUTIONS:")
        print("1. Accédez à http://localhost:8000")
        print("2. Configurez la connexion HFSQL (logiciel: Codial)")
        print("3. Sauvegardez la configuration")
        print("4. Relancez ce script")
        return
    
    print()
    
    # Exécuter la requête
    success = execute_query_with_form_config()
    
    print()
    print("=" * 80)
    if success:
        print("🎉 REQUÊTE EXÉCUTÉE AVEC SUCCÈS")
    else:
        print("❌ ÉCHEC DE LA REQUÊTE")
    print("=" * 80)

if __name__ == "__main__":
    main()
