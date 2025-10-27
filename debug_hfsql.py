#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnostic HFSQL
Teste différentes méthodes de connexion et fournit des recommandations
"""

import pyodbc
import pypyodbc
import sys
import platform

def list_odbc_drivers():
    """Liste tous les drivers ODBC disponibles"""
    print("=== DRIVERS ODBC DISPONIBLES ===")
    drivers = pyodbc.drivers()
    for i, driver in enumerate(drivers, 1):
        print(f"{i:2d}. {driver}")
    return drivers

def test_hfsql_connection(host, user, password, database, port):
    """Teste la connexion HFSQL avec différents drivers"""
    print(f"\n=== TEST CONNEXION HFSQL ===")
    print(f"Host: {host}")
    print(f"User: {user}")
    print(f"Database: {database}")
    print(f"Port: {port}")
    print(f"Python: {platform.architecture()[0]} bits")
    
    # Drivers HFSQL à tester
    hfsql_drivers = [
        "HFSQL Client/Server (Unicode)",
        "HFSQL Client/Server", 
        "HFSQL (Unicode)",
        "HFSQL",
        "HFSQL Client/Server 32-bit",
        "HFSQL Client/Server 64-bit"
    ]
    
    # Test avec pyodbc
    print("\n--- Test avec pyodbc ---")
    for driver in hfsql_drivers:
        if driver in pyodbc.drivers():
            try:
                conn_str = (
                    f"DRIVER={{{driver}}};"
                    f"SERVER={host};"
                    f"PORT={port};"
                    f"DATABASE={database};"
                    f"UID={user};"
                    f"PWD={password}"
                )
                print(f"Test driver: {driver}")
                conn = pyodbc.connect(conn_str, timeout=10)
                print(f"SUCCES avec {driver}")
                conn.close()
                return True
            except Exception as e:
                print(f"ECHEC avec {driver}: {e}")
        else:
            print(f"Driver non disponible: {driver}")
    
    # Test avec pypyodbc
    print("\n--- Test avec pypyodbc ---")
    for driver in hfsql_drivers:
        try:
            conn_str = (
                f"Driver={{{driver}}};"
                f"Server Name={host};"
                f"Server Port={port};"
                f"Database={database};"
                f"UID={user};"
                f"PWD={password}"
            )
            print(f"Test driver: {driver}")
            conn = pypyodbc.connect(conn_str)
            print(f"SUCCES avec {driver}")
            conn.close()
            return True
        except Exception as e:
            print(f"ECHEC avec {driver}: {e}")
    
    return False

def test_dsn_connection():
    """Teste les connexions DSN disponibles"""
    print("\n=== DSN DISPONIBLES ===")
    try:
        dsn_list = pyodbc.dataSources()
        if dsn_list:
            for dsn_name, dsn_desc in dsn_list.items():
                print(f"DSN: {dsn_name} - {dsn_desc}")
                
                # Test de connexion DSN
                if "HFSQL" in dsn_desc.upper():
                    try:
                        conn = pyodbc.connect(f"DSN={dsn_name}")
                        print(f"DSN {dsn_name} fonctionne")
                        conn.close()
                        return dsn_name
                    except Exception as e:
                        print(f"DSN {dsn_name} echoue: {e}")
        else:
            print("Aucun DSN trouvé")
    except Exception as e:
        print(f"Erreur lors de la lecture des DSN: {e}")
    
    return None

def main():
    print("=== DIAGNOSTIC HFSQL ===")
    print(f"Système: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")
    
    # Lister les drivers
    drivers = list_odbc_drivers()
    
    # Paramètres de connexion (à adapter selon votre configuration)
    host = "PC-JEAN-PIERRE"
    user = "admin"
    password = ""
    database = "DATA_DEMO"
    port = "4900"
    
    # Test connexion directe
    success = test_hfsql_connection(host, user, password, database, port)
    
    if not success:
        # Test DSN
        dsn = test_dsn_connection()
        
        print("\n=== RECOMMANDATIONS ===")
        print("1. Mettre à jour le client HFSQL vers la dernière version")
        print("   Télécharger depuis: https://www.pcsoft.fr/telechargements/")
        print("2. Créer un DSN Windows pour HFSQL")
        print("   - Ouvrir 'Sources de données ODBC' (odbcad32.exe)")
        print("   - Créer un nouveau DSN système")
        print("   - Sélectionner le driver HFSQL approprié")
        print("3. Vérifier la compatibilité des versions serveur/client")
        print("4. Contacter l'administrateur du serveur HFSQL")
        
        if dsn:
            print(f"\nUtilisez le DSN '{dsn}' dans votre configuration")

if __name__ == "__main__":
    main()
