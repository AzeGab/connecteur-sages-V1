# Module de connexion aux bases de données
# Ce fichier contient les fonctions nécessaires pour établir des connexions
# avec SQL Server et PostgreSQL, ainsi que la gestion des identifiants

import pyodbc
import psycopg2
import json
import os
import requests

# Chemin du fichier stockant les identifiants de connexion
CREDENTIALS_FILE = "app/services/credentials.json"

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
        conn = psycopg2.connect(
            host=host,
            dbname=database,
            user=user,
            password=password,
            port=port
        )
        print("✅ Connexion PostgreSQL réussie")
        return conn
    except Exception as e:
        print("❌ Erreur PostgreSQL :", e)
        return None
    
    
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