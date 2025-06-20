# Module de connexion aux bases de données
# Ce fichier contient les fonctions nécessaires pour établir des connexions
# avec SQL Server et PostgreSQL, ainsi que la gestion des identifiants

import pyodbc
import psycopg2
import json
import os
import requests
import pypyodbc


# Chemin du fichier stockant les identifiants de connexion
CREDENTIALS_FILE = "app/services/credentials.json"

# ============================================================================
# CONNEXION SQL SERVER
# ============================================================================

def connect_to_sqlserver(server, user, password, database):
    """
    Établit une connexion à une base de données SQL Server.
    
    Args:
        server (str): Nom ou adresse IP du serveur
        user (str): Nom d'utilisateur
        password (str): Mot de passe
        database (str): Nom de la base de données
        
    Returns:
        pyodbc.Connection: Objet de connexion si réussi, None si échec
    """
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password};"
        f"TrustServerCertificate=yes;"  # Permet la connexion même avec un certificat auto-signé
    )
    try:
        conn = pyodbc.connect(conn_str)
        print("✅ Connexion SQL Server réussie")
        return conn
    except Exception as e:
        print("❌ Erreur de connexion SQL Server:", e)
        return None

# ============================================================================
# CONNEXION POSTGRESQL
# ============================================================================

def connect_to_postgres(host, user, password, database, port="5432"):
    """
    Établit une connexion à une base de données PostgreSQL.
    
    Args:
        host (str): Nom d'hôte ou adresse IP du serveur
        user (str): Nom d'utilisateur
        password (str): Mot de passe
        database (str): Nom de la base de données
        port (str): Port de connexion (par défaut: 5432)
        
    Returns:
        psycopg2.connection: Objet de connexion si réussi, None si échec
    """
    try:
        # Paramètres de connexion avec encodage explicite
        conn = psycopg2.connect(
            host=host,
            dbname=database,
            user=user,
            password=password,
            port=port,
            client_encoding='utf8',
            options='-c client_encoding=utf8'
        )
        print("✅ Connexion PostgreSQL réussie")
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Erreur de connexion PostgreSQL : {e}")
        return None
    except Exception as e:
        print(f"❌ Erreur PostgreSQL : {e}")
        return None
    
# ============================================================================
# CONNEXION HFSQL
# ============================================================================

def connect_to_hfsql(host, user="admin", password="", database="HFSQL", port="4900"):
    """
    Établit une connexion à une base de données HFSQL.
    
    Args:
        host (str): Nom d'hôte ou adresse IP du serveur
        user (str): Nom d'utilisateur (par défaut: admin)
        password (str): Mot de passe    (par défaut: )
        database (str): Nom de la base de données
        port (str): Port de connexion (par défaut: 4900)
        
    Returns:
        pypyodbc.Connection: Objet de connexion si réussi, None si échec
    """ 
    try:
        conn = pypyodbc.connect(
            host=host,
            user=user,
            password=password,
            database=database,  
            port=port
        )
        print("✅ Connexion HFSQL réussie")
        return conn
    except Exception as e:
        print("❌ Erreur HFSQL :", e)
        return None

# ============================================================================
# GESTION DES IDENTIFIANTS
# ============================================================================

def save_credentials(data):
    """
    Sauvegarde les identifiants de connexion dans un fichier JSON.
    
    Args:
        data (dict): Dictionnaire contenant les identifiants à sauvegarder
    """
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(data, f)

def load_credentials():
    """
    Charge les identifiants de connexion depuis le fichier JSON.
    
    Returns:
        dict: Dictionnaire contenant les identifiants, None si le fichier n'existe pas
    """
    if not os.path.exists(CREDENTIALS_FILE):
        return None
    with open(CREDENTIALS_FILE, "r") as f:
        return json.load(f)

# ============================================================================
# AUTHENTIFICATION BATISIMPLY
# ============================================================================

def recup_batisimply_token():
    """
    Récupère le token d'authentification pour l'API BatiSimply.
    
    Returns:
        str: Token d'accès si réussi, None si échec
    """
    url = "https://sso.staging.batisimply.fr/auth/realms/jhipster/protocol/openid-connect/token"

    payload = {
        "client_id": "bridge-data", 
        "grant_type": "password",
        "username": "enzo@apication.fr",
        "client_secret": "e46938bc-e853-4240-be78-48dbeccdcceb",
        "password": "TestBS123"  
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.post(url, data=payload, headers=headers)

    if response.status_code == 200:
        token_data = response.json()
        return token_data["access_token"]
    else:
        print(f"❌ Erreur lors de la récupération du token : {response.status_code} → {response.text}")
        return None

# ============================================================================
# VÉRIFICATION DES CONNEXIONS
# ============================================================================

def check_connection_status():
    """
    Vérifie l'état des connexions aux bases de données.
    
    Returns:
        tuple: (sql_connected, pg_connected) - États de connexion pour SQL Server et PostgreSQL
    """
    creds = load_credentials()
    sql_connected = False
    pg_connected = False
    
    if creds:
        # Vérifier SQL Server
        if "sqlserver" in creds:
            sql_creds = creds["sqlserver"]
            conn = connect_to_sqlserver(
                sql_creds["server"],
                sql_creds["user"],
                sql_creds["password"],
                sql_creds["database"]
            )
            sql_connected = conn is not None
            if conn:
                conn.close()
        
        # Vérifier PostgreSQL
        if "postgres" in creds:
            pg_creds = creds["postgres"]
            conn = connect_to_postgres(
                pg_creds["host"],
                pg_creds["user"],
                pg_creds["password"],
                pg_creds["database"],
                pg_creds.get("port", "5432")
            )
            pg_connected = conn is not None
            if conn:
                conn.close()
    
    return sql_connected, pg_connected

# ============================================================================
# CONNEXION 
# ============================================================================

def connexion():
    """
    Établit une connexion aux BDD (SQL Server et PostgreSQL) en utilisant les identifiants stockés.

    Returns:
        tuple: (postgres_conn, sqlserver_conn) - Objets de connexion pour PostgreSQL et SQL Server
    """
    creds = load_credentials()
    if not creds or "sqlserver" not in creds or "postgres" not in creds:
        return None, None

    sql = creds["sqlserver"]
    pg = creds["postgres"]

    postgres_conn = connect_to_postgres(
        pg["host"], pg["user"], pg["password"], pg["database"], pg.get("port", "5432")
    )
    sqlserver_conn = connect_to_sqlserver(
        sql["server"], sql["user"], sql["password"], sql["database"]
    )

    return postgres_conn, sqlserver_conn

# ============================================================================
# 


