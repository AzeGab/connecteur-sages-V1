#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnostic avancé HFSQL
Teste différentes méthodes de connexion et fournit des solutions détaillées
"""

import pyodbc
import pypyodbc
import sys
import platform
import subprocess
import os
from pathlib import Path

def get_system_info():
    """Récupère les informations système détaillées"""
    print("=== INFORMATIONS SYSTÈME ===")
    print(f"Système: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.architecture()[0]}")
    print(f"Python: {sys.version}")
    print(f"Version pyodbc: {pyodbc.version}")
    print(f"Version pypyodbc: {pypyodbc.version}")
    print()

def list_odbc_drivers_detailed():
    """Liste tous les drivers ODBC avec détails"""
    print("=== DRIVERS ODBC DISPONIBLES ===")
    drivers = pyodbc.drivers()
    hfsql_drivers = []
    
    for i, driver in enumerate(drivers, 1):
        print(f"{i:2d}. {driver}")
        if "HFSQL" in driver.upper():
            hfsql_drivers.append(driver)
    
    print(f"\nDrivers HFSQL trouvés: {len(hfsql_drivers)}")
    for driver in hfsql_drivers:
        print(f"  - {driver}")
    
    return drivers, hfsql_drivers

def check_hfsql_installation():
    """Vérifie l'installation HFSQL sur le système"""
    print("\n=== VÉRIFICATION INSTALLATION HFSQL ===")
    
    # Chemins typiques d'installation HFSQL
    hfsql_paths = [
        r"C:\Program Files\PC SOFT\HFSQL Client",
        r"C:\Program Files (x86)\PC SOFT\HFSQL Client",
        r"C:\Program Files\PC SOFT\HFSQL",
        r"C:\Program Files (x86)\PC SOFT\HFSQL",
        r"C:\HFSQL",
    ]
    
    found_installation = False
    for path in hfsql_paths:
        if os.path.exists(path):
            print(f"Installation trouvée: {path}")
            found_installation = True
            
            # Chercher les fichiers de version
            version_files = ["version.txt", "VERSION.TXT", "hfsql.exe", "HFSQL.EXE"]
            for vfile in version_files:
                vpath = os.path.join(path, vfile)
                if os.path.exists(vpath):
                    try:
                        with open(vpath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()[:200]
                            print(f"  Version info ({vfile}): {content.strip()}")
                    except:
                        pass
    
    if not found_installation:
        print("Aucune installation HFSQL trouvée dans les chemins standards")
    
    return found_installation

def test_connection_methods(host, user, password, database, port):
    """Teste différentes méthodes de connexion"""
    print(f"\n=== TEST CONNEXION HFSQL ===")
    print(f"Host: {host}")
    print(f"User: {user}")
    print(f"Database: {database}")
    print(f"Port: {port}")
    
    # Méthode 1: Connexion directe avec différents drivers
    print("\n--- Méthode 1: Connexion directe ---")
    success = test_direct_connection(host, user, password, database, port)
    
    if success:
        return True
    
    # Méthode 2: Connexion via DSN
    print("\n--- Méthode 2: Connexion via DSN ---")
    success = test_dsn_connection()
    
    if success:
        return True
    
    # Méthode 3: Connexion avec paramètres alternatifs
    print("\n--- Méthode 3: Paramètres alternatifs ---")
    success = test_alternative_parameters(host, user, password, database, port)
    
    return success

def test_direct_connection(host, user, password, database, port):
    """Teste la connexion directe avec différents drivers"""
    # Drivers HFSQL à tester (ordre de préférence)
    hfsql_drivers = [
        "HFSQL Client/Server (Unicode)",
        "HFSQL Client/Server", 
        "HFSQL (Unicode)",
        "HFSQL",
        "HFSQL Client/Server 32-bit",
        "HFSQL Client/Server 64-bit",
        "HFSQL Client/Server Unicode",
        "HFSQL Unicode Client/Server"
    ]
    
    # Test avec pyodbc
    print("Test avec pyodbc:")
    for driver in hfsql_drivers:
        if driver in pyodbc.drivers():
            try:
                # Format de chaîne de connexion pour pyodbc
                conn_str = (
                    f"DRIVER={{{driver}}};"
                    f"SERVER={host};"
                    f"PORT={port};"
                    f"DATABASE={database};"
                    f"UID={user};"
                    f"PWD={password};"
                    f"Timeout=30"
                )
                print(f"  Test driver: {driver}")
                conn = pyodbc.connect(conn_str, timeout=30)
                print(f"  ✓ SUCCÈS avec {driver}")
                conn.close()
                return True
            except Exception as e:
                print(f"  ✗ ÉCHEC avec {driver}: {str(e)[:100]}")
        else:
            print(f"  - Driver non disponible: {driver}")
    
    # Test avec pypyodbc
    print("\nTest avec pypyodbc:")
    for driver in hfsql_drivers:
        try:
            # Format de chaîne de connexion pour pypyodbc
            conn_str = (
                f"Driver={{{driver}}};"
                f"Server Name={host};"
                f"Server Port={port};"
                f"Database={database};"
                f"UID={user};"
                f"PWD={password}"
            )
            print(f"  Test driver: {driver}")
            conn = pypyodbc.connect(conn_str)
            print(f"  ✓ SUCCÈS avec {driver}")
            conn.close()
            return True
        except Exception as e:
            print(f"  ✗ ÉCHEC avec {driver}: {str(e)[:100]}")
    
    return False

def test_dsn_connection():
    """Teste les connexions DSN disponibles"""
    print("Recherche des DSN HFSQL...")
    try:
        dsn_list = pyodbc.dataSources()
        hfsql_dsns = []
        
        for dsn_name, dsn_desc in dsn_list.items():
            if "HFSQL" in dsn_desc.upper():
                hfsql_dsns.append((dsn_name, dsn_desc))
                print(f"  DSN trouvé: {dsn_name} - {dsn_desc}")
        
        if not hfsql_dsns:
            print("  Aucun DSN HFSQL trouvé")
            return False
        
        # Test de connexion pour chaque DSN HFSQL
        for dsn_name, dsn_desc in hfsql_dsns:
            try:
                print(f"  Test DSN: {dsn_name}")
                conn = pyodbc.connect(f"DSN={dsn_name}", timeout=30)
                print(f"  ✓ DSN {dsn_name} fonctionne")
                conn.close()
                return True
            except Exception as e:
                print(f"  ✗ DSN {dsn_name} échoue: {str(e)[:100]}")
        
    except Exception as e:
        print(f"  Erreur lors de la lecture des DSN: {e}")
    
    return False

def test_alternative_parameters(host, user, password, database, port):
    """Teste des paramètres de connexion alternatifs"""
    print("Test de paramètres alternatifs...")
    
    # Variations de paramètres
    variations = [
        {"host": host, "port": port, "database": database},
        {"host": host, "port": "4900", "database": database},
        {"host": f"{host}:{port}", "port": "", "database": database},
        {"host": host, "port": port, "database": ""},
    ]
    
    for i, params in enumerate(variations, 1):
        print(f"  Variation {i}: {params}")
        try:
            conn_str = (
                f"DRIVER={{HFSQL Client/Server}};"
                f"SERVER={params['host']};"
                f"PORT={params['port']};"
                f"DATABASE={params['database']};"
                f"UID={user};"
                f"PWD={password}"
            )
            conn = pyodbc.connect(conn_str, timeout=10)
            print(f"  ✓ SUCCÈS avec variation {i}")
            conn.close()
            return True
        except Exception as e:
            print(f"  ✗ ÉCHEC variation {i}: {str(e)[:80]}")
    
    return False

def provide_solutions():
    """Fournit des solutions détaillées pour résoudre les problèmes"""
    print("\n" + "="*60)
    print("SOLUTIONS POUR RÉSOUDRE LE PROBLÈME HFSQL")
    print("="*60)
    
    print("\n1. MISE À JOUR DU CLIENT HFSQL")
    print("   Le problème principal est une version client trop ancienne.")
    print("   Solutions:")
    print("   - Télécharger la dernière version depuis: https://www.pcsoft.fr/telechargements/")
    print("   - Installer HFSQL Client/Server (version 64-bit si Python 64-bit)")
    print("   - Redémarrer l'ordinateur après installation")
    
    print("\n2. CRÉATION D'UN DSN WINDOWS")
    print("   Alternative si la mise à jour n'est pas possible:")
    print("   - Ouvrir 'Sources de données ODBC' (odbcad32.exe)")
    print("   - Aller dans l'onglet 'DSN système'")
    print("   - Cliquer 'Ajouter'")
    print("   - Sélectionner 'HFSQL Client/Server'")
    print("   - Configurer:")
    print("     * Nom du serveur: PC-JEAN-PIERRE")
    print("     * Port: 4900")
    print("     * Base de données: DATA_DEMO")
    print("     * Utilisateur: admin")
    print("   - Tester la connexion")
    print("   - Utiliser 'DSN=NomDuDSN' dans votre configuration")
    
    print("\n3. VÉRIFICATION DE LA COMPATIBILITÉ")
    print("   - Vérifier que le serveur HFSQL accepte les connexions")
    print("   - Contacter l'administrateur du serveur")
    print("   - Vérifier les paramètres de pare-feu")
    print("   - Tester la connectivité réseau: telnet PC-JEAN-PIERRE 4900")
    
    print("\n4. CONFIGURATION ALTERNATIVE")
    print("   Si aucune solution ne fonctionne:")
    print("   - Utiliser un autre pilote ODBC compatible")
    print("   - Configurer un tunnel SSH si nécessaire")
    print("   - Utiliser l'API REST HFSQL si disponible")

def create_dsn_script():
    """Crée un script pour configurer automatiquement un DSN"""
    script_content = '''@echo off
echo Configuration automatique du DSN HFSQL
echo.

REM Vérifier les privilèges administrateur
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Privilèges administrateur détectés
) else (
    echo ATTENTION: Ce script nécessite des privilèges administrateur
    echo Relancez en tant qu'administrateur
    pause
    exit /b 1
)

REM Créer le DSN via regedit
echo Création du DSN HFSQL...
reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\ODBC\\ODBC.INI\\HFSQL_DEMO" /v "Driver" /t REG_SZ /d "C:\\Windows\\System32\\HFSQL.DLL" /f
reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\ODBC\\ODBC.INI\\HFSQL_DEMO" /v "Server Name" /t REG_SZ /d "PC-JEAN-PIERRE" /f
reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\ODBC\\ODBC.INI\\HFSQL_DEMO" /v "Server Port" /t REG_SZ /d "4900" /f
reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\ODBC\\ODBC.INI\\HFSQL_DEMO" /v "Database" /t REG_SZ /d "DATA_DEMO" /f

REM Ajouter à la liste des DSN
reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\ODBC\\ODBC.INI\\ODBC Data Sources" /v "HFSQL_DEMO" /t REG_SZ /d "HFSQL Client/Server" /f

echo DSN HFSQL_DEMO créé avec succès
echo Vous pouvez maintenant utiliser "DSN=HFSQL_DEMO" dans votre configuration
pause
'''
    
    with open("create_hfsql_dsn.bat", "w", encoding="utf-8") as f:
        f.write(script_content)
    
    print(f"\nScript de création DSN sauvegardé: create_hfsql_dsn.bat")
    print("Exécutez-le en tant qu'administrateur pour créer automatiquement un DSN")

def main():
    print("=== DIAGNOSTIC AVANCÉ HFSQL ===")
    print("Version: 2.0")
    print()
    
    # Informations système
    get_system_info()
    
    # Vérification installation
    check_hfsql_installation()
    
    # Liste des drivers
    drivers, hfsql_drivers = list_odbc_drivers_detailed()
    
    # Paramètres de connexion
    host = "PC-JEAN-PIERRE"
    user = "admin"
    password = ""
    database = "DATA_DEMO"
    port = "4900"
    
    # Tests de connexion
    success = test_connection_methods(host, user, password, database, port)
    
    if not success:
        # Fournir les solutions
        provide_solutions()
        
        # Créer le script DSN
        create_dsn_script()
        
        print(f"\n{'='*60}")
        print("RÉSUMÉ DU DIAGNOSTIC")
        print(f"{'='*60}")
        print("❌ Aucune connexion HFSQL réussie")
        print("🔧 Solutions recommandées:")
        print("   1. Mettre à jour le client HFSQL")
        print("   2. Créer un DSN Windows")
        print("   3. Vérifier la compatibilité serveur/client")
    else:
        print(f"\n{'='*60}")
        print("✅ CONNEXION HFSQL RÉUSSIE")
        print(f"{'='*60}")
        print("Votre configuration HFSQL fonctionne correctement")

if __name__ == "__main__":
    main()
