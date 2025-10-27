#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test rapide pour la connexion HFSQL
Utilise les fonctions améliorées du module connex
"""

import sys
import os

# Ajouter le répertoire app au path pour importer les modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.connex import connect_to_hfsql

def test_hfsql_connection():
    """Teste la connexion HFSQL avec les paramètres du debug"""
    print("=== TEST CONNEXION HFSQL ===")
    print("Utilisation des paramètres du debug...")
    print()
    
    # Paramètres du debug
    host = "PC-JEAN-PIERRE"
    user = "admin"
    password = ""
    database = "DATA_DEMO"
    port = "4900"
    
    print(f"Host: {host}")
    print(f"User: {user}")
    print(f"Database: {database}")
    print(f"Port: {port}")
    print()
    
    # Test de connexion
    print("Tentative de connexion...")
    conn = connect_to_hfsql(host, user, password, database, port)
    
    if conn:
        print("\n✅ CONNEXION RÉUSSIE!")
        print("Test de requête simple...")
        try:
            cursor = conn.cursor()
            # Essayer une requête simple
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            print(f"Résultat du test: {result}")
            cursor.close()
            conn.close()
            print("✅ Test de requête réussi!")
            return True
        except Exception as e:
            print(f"❌ Erreur lors du test de requête: {e}")
            conn.close()
            return False
    else:
        print("\n❌ ÉCHEC DE LA CONNEXION")
        print("Consultez les messages d'erreur ci-dessus pour plus de détails.")
        return False

def test_dsn_connection():
    """Teste la connexion via DSN si disponible"""
    print("\n=== TEST CONNEXION VIA DSN ===")
    
    # Essayer de trouver des DSN HFSQL
    import pyodbc
    try:
        dsn_list = pyodbc.dataSources()
        hfsql_dsns = []
        
        for dsn_name, dsn_desc in dsn_list.items():
            if "HFSQL" in dsn_desc.upper():
                hfsql_dsns.append((dsn_name, dsn_desc))
                print(f"DSN trouvé: {dsn_name} - {dsn_desc}")
        
        if not hfsql_dsns:
            print("Aucun DSN HFSQL trouvé")
            return False
        
        # Tester chaque DSN
        for dsn_name, dsn_desc in hfsql_dsns:
            print(f"\nTest du DSN: {dsn_name}")
            try:
                conn = connect_to_hfsql(f"DSN={dsn_name}")
                if conn:
                    print(f"✅ DSN {dsn_name} fonctionne!")
                    conn.close()
                    return True
                else:
                    print(f"❌ DSN {dsn_name} échoue")
            except Exception as e:
                print(f"❌ Erreur DSN {dsn_name}: {e}")
        
    except Exception as e:
        print(f"Erreur lors de la lecture des DSN: {e}")
    
    return False

def main():
    """Fonction principale"""
    print("=== DIAGNOSTIC RAPIDE HFSQL ===")
    print("Version: 1.0")
    print()
    
    # Test 1: Connexion directe
    success_direct = test_hfsql_connection()
    
    # Test 2: Connexion DSN
    success_dsn = test_dsn_connection()
    
    # Résumé
    print("\n" + "="*50)
    print("RÉSUMÉ DES TESTS")
    print("="*50)
    print(f"Connexion directe: {'✅ RÉUSSIE' if success_direct else '❌ ÉCHOUÉE'}")
    print(f"Connexion DSN: {'✅ RÉUSSIE' if success_dsn else '❌ ÉCHOUÉE'}")
    
    if not success_direct and not success_dsn:
        print("\n🔧 SOLUTIONS RECOMMANDÉES:")
        print("1. Exécuter le diagnostic avancé: python debug_hfsql_advanced.py")
        print("2. Mettre à jour le client HFSQL")
        print("3. Créer un DSN Windows")
        print("4. Vérifier la compatibilité serveur/client")
    elif success_dsn and not success_direct:
        print("\n💡 RECOMMANDATION:")
        print("Utilisez un DSN Windows dans votre configuration:")
        print("host = 'DSN=NomDeVotreDSN'")
    else:
        print("\n🎉 VOTRE CONFIGURATION HFSQL FONCTIONNE!")

if __name__ == "__main__":
    main()
