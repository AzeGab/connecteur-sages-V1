# Module de connexion aux bases de données
# Ce fichier contient les fonctions nécessaires pour établir des connexions
# avec SQL Server et PostgreSQL, ainsi que la gestion des identifiants

import pyodbc
import psycopg2
import json
import os
import requests
import pypyodbc
from dotenv import load_dotenv
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


# Chemin du fichier stockant les identifiants de connexion
# Chemin du fichier stockant les identifiants de connexion
CREDENTIALS_FILE = "app/services/credentials.json"

# Charger les variables d'environnement depuis .env si présent
load_dotenv()

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
        print("Connexion SQL Server reussie")
        return conn
    except Exception as e:
        print("Erreur de connexion SQL Server:", e)
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
        print("Connexion PostgreSQL reussie")
        return conn
    except psycopg2.OperationalError as e:
        print(f"Erreur de connexion PostgreSQL : {e}")
        return None
    except Exception as e:
        print(f"Erreur PostgreSQL : {e}")
        return None
    
# ============================================================================
# CONNEXION HFSQL
# ============================================================================

def connect_to_hfsql(host: str, user: str = "admin", password: str = "", database: str = "HFSQL", port: str = "4900"):
    """
    Établit une connexion ODBC à HFSQL (Client/Serveur).

    - Requiert l'installation du pilote ODBC PC SOFT (HFSQL Client/Serveur)
    - Connexion "DSN-less" avec Driver explicite
    - Supporte un host de type "DSN=NomDeDSN" si vous utilisez un DSN Windows
    - Gestion avancée des erreurs de version et compatibilité
    
    Solutions pour erreur "couche cliente plus récente":
    1. Mettre à jour le client HFSQL vers la dernière version
    2. Utiliser un DSN Windows configuré
    3. Vérifier la compatibilité serveur/client
    4. Essayer différents formats de chaîne de connexion
    """
    try:
        # Si un DSN Windows est fourni (ex: "DSN=MON_DSN"), forcer la base ciblée
        # Certains DSN imposent une base par défaut; on la surpasse via DATABASE
        if host.upper().startswith("DSN="):
            dsn_conn_strings = [
                f"{host};DATABASE={database};UID={user};PWD={password}",
                f"{host};Database={database};UID={user};PWD={password}",
                f"{host};UID={user};PWD={password}"
            ]
            for idx, conn_str in enumerate(dsn_conn_strings, start=1):
                try:
                    conn = pypyodbc.connect(conn_str)
                    print(f"Connexion HFSQL via DSN reussie (essai {idx}, avec base '{database}')")
                    return conn
                except Exception as e:
                    print(f"Erreur DSN HFSQL (pypyodbc, essai {idx}): {e}")
                    # Essayer aussi avec pyodbc
                    try:
                        conn = pyodbc.connect(conn_str)
                        print(f"Connexion HFSQL via DSN (pyodbc) reussie (essai {idx}, avec base '{database}')")
                        return conn
                    except Exception as e2:
                        print(f"Erreur DSN HFSQL (pyodbc, essai {idx}): {e2}")

        # Essayer plusieurs noms de driver possibles avec différents formats
        driver_candidates = [
            "HFSQL Client/Server (Unicode)",
            "HFSQL Client/Server",
            "HFSQL (Unicode)",
            "HFSQL",
            "HFSQL Client/Server Unicode",
            "HFSQL Unicode Client/Server",
            "HFSQL Client/Server 64-bit",
            "HFSQL Client/Server 32-bit"
        ]

        # Formats de chaîne de connexion à tester
        connection_formats = [
            # Format pypyodbc
            {
                "driver": "Driver={{{driver}}};",
                "server": "Server Name={host};",
                "port": "Server Port={port};",
                "database": "Database={database};",
                "auth": "UID={user};PWD={password}"
            },
            # Format pyodbc
            {
                "driver": "DRIVER={{{driver}}};",
                "server": "SERVER={host};",
                "port": "PORT={port};",
                "database": "DATABASE={database};",
                "auth": "UID={user};PWD={password};TrustServerCertificate=yes"
            },
            # Format alternatif
            {
                "driver": "Driver={{{driver}}};",
                "server": "Server={host};",
                "port": "Port={port};",
                "database": "Database={database};",
                "auth": "User={user};Password={password}"
            }
        ]

        last_error = None
        successful_driver = None
        
        for format_idx, conn_format in enumerate(connection_formats):
            print(f"Test format de connexion {format_idx + 1}...")
            
            for drv in driver_candidates:
                try:
                    # Vérifier si le driver existe
                    if drv not in pyodbc.drivers():
                        continue
                    
                    conn_str = (
                        conn_format["driver"] +
                        conn_format["server"] +
                        conn_format["port"] +
                        conn_format["database"] +
                        conn_format["auth"]
                    ).format(driver=drv, host=host, port=port, database=database, user=user, password=password)
                    
                    # Essayer avec pypyodbc
                    try:
                        conn = pypyodbc.connect(conn_str)
                        print(f"Connexion HFSQL reussie avec le driver '{drv}' (format {format_idx + 1})")
                        return conn
                    except Exception as e1:
                        # Essayer avec pyodbc
                        try:
                            conn = pyodbc.connect(conn_str, timeout=30)
                            print(f"Connexion HFSQL reussie avec le driver '{drv}' (pyodbc, format {format_idx + 1})")
                            return conn
                        except Exception as e2:
                            last_error = e2 if "couche cliente plus récente" in str(e2) else e1
                            continue
                            
                except Exception as e:
                    last_error = e
                    continue

        # Si aucune connexion n'a réussi, essayer des méthodes alternatives
        print("Tentative de connexion avec paramètres alternatifs...")
        
        # Méthode alternative 1: Connexion sans base de données spécifiée
        try:
            for drv in ["HFSQL Client/Server", "HFSQL"]:
                if drv in pyodbc.drivers():
                    conn_str = f"DRIVER={{{drv}}};SERVER={host};PORT={port};UID={user};PWD={password}"
                    conn = pyodbc.connect(conn_str, timeout=30)
                    print(f"Connexion HFSQL reussie (sans base spécifiée) avec '{drv}'")
                    return conn
        except Exception as e:
            pass
        
        # Méthode alternative 2: Connexion avec host:port
        try:
            for drv in ["HFSQL Client/Server", "HFSQL"]:
                if drv in pyodbc.drivers():
                    conn_str = f"DRIVER={{{drv}}};SERVER={host}:{port};DATABASE={database};UID={user};PWD={password}"
                    conn = pyodbc.connect(conn_str, timeout=30)
                    print(f"Connexion HFSQL reussie (host:port) avec '{drv}'")
                    return conn
        except Exception as e:
            pass

        print("Erreur HFSQL (pilote/DSN):", last_error)
        print("Verifiez que le pilote ODBC HFSQL Client/Serveur est installe et que le nom du driver est correct.")
        
        # Diagnostic spécifique pour l'erreur de version
        if last_error and "couche cliente plus récente" in str(last_error):
            print("\n=== DIAGNOSTIC HFSQL DÉTAILLÉ ===")
            print("ERREUR: Version du client HFSQL trop ancienne")
            print("Détails de l'erreur:")
            print(f"  {last_error}")
            print("\nSOLUTIONS RECOMMANDÉES:")
            print("1. Mettre à jour le client HFSQL vers la dernière version")
            print("   - Télécharger depuis: https://www.pcsoft.fr/telechargements/")
            print("   - Installer HFSQL Client/Server (version 64-bit si Python 64-bit)")
            print("   - Redémarrer l'ordinateur après installation")
            print("2. Créer un DSN Windows configuré")
            print("   - Ouvrir 'Sources de données ODBC' (odbcad32.exe)")
            print("   - Créer un DSN système avec les paramètres:")
            print(f"     * Serveur: {host}")
            print(f"     * Port: {port}")
            print(f"     * Base: {database}")
            print(f"     * Utilisateur: {user}")
            print("   - Utiliser 'DSN=NomDuDSN' dans votre configuration")
            print("3. Vérifier la compatibilité serveur/client")
            print("   - Contacter l'administrateur du serveur HFSQL")
            print("   - Vérifier que le serveur accepte les connexions")
            print("4. Exécuter le script de diagnostic: python debug_hfsql_advanced.py")
            print(f"\nVersion client détectée: IEWDHFSRV=13.63")
            print(f"Serveur cible: {host}:{port}")
            print(f"Base de données: {database}")
        
        return None
    except Exception as e:
        print("Erreur HFSQL générale :", e)
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
    with open(CREDENTIALS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)

def load_credentials():
    """
    Charge les identifiants de connexion depuis le fichier JSON.
    Tolère les fichiers vides et l'encodage UTF-8 avec BOM.
    
    Returns:
        dict | None: Identifiants ou None si indisponible/illisible
    """
    try:
        if not os.path.exists(CREDENTIALS_FILE):
            return None
        # Fichier vide
        if os.path.getsize(CREDENTIALS_FILE) == 0:
            return None
        # Lecture tolérante au BOM
        with open(CREDENTIALS_FILE, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except json.JSONDecodeError:
        try:
            # Lecture brute avec nettoyage du BOM et des espaces
            with open(CREDENTIALS_FILE, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().lstrip("\ufeff").strip()
                if not content:
                    return None
                return json.loads(content)
        except Exception:
            return None
    except Exception:
        return None

# ============================================================================
# AUTHENTIFICATION BATISIMPLY
# ============================================================================

def recup_batisimply_token():
    """
    Récupère un access_token Keycloak pour l'API BatiSimply.
    - Supporte grant_type=password (ROPC) et client_credentials.
    - Lit d'abord credentials.json (section "batisimply"), sinon variables d'environnement.
    - Retourne une string (access_token) ou None si échec (avec logs explicites).
    """
    # 1) Lire les creds persistés puis fallback env
    creds = load_credentials() or {}
    bcfg = creds.get("batisimply", {}) if isinstance(creds, dict) else {}

    url = bcfg.get("sso_url") or os.getenv("BATISIMPLY_SSO_URL")
    client_id = bcfg.get("client_id") or os.getenv("BATISIMPLY_CLIENT_ID")
    client_secret = bcfg.get("client_secret") or os.getenv("BATISIMPLY_CLIENT_SECRET")
    username = bcfg.get("username") or os.getenv("BATISIMPLY_USERNAME")
    password = bcfg.get("password") or os.getenv("BATISIMPLY_PASSWORD")
    grant_type = (bcfg.get("grant_type") or os.getenv("BATISIMPLY_GRANT_TYPE") or "password").strip()
    scope = bcfg.get("scope") or os.getenv("BATISIMPLY_SCOPE")

    # 2) Validation ciblée selon le grant
    missing = []
    if not url:
        missing.append("sso_url")
    if not client_id:
        missing.append("client_id")

    if grant_type == "client_credentials":
        if not client_secret:
            missing.append("client_secret")
    else:  # password (ROPC) par défaut
        if not username:
            missing.append("username")
        if not password:
            missing.append("password")
        if not client_secret:
            # la plupart des clients Keycloak sont "confidential" -> secret requis
            missing.append("client_secret")

    if missing:
        print(f"Parametres BatiSimply manquants ({grant_type}) : {', '.join(missing)}")
        print("Renseigne la section 'batisimply' dans credentials.json ou les variables d'environnement BATISIMPLY_*.")
        return None

    # 3) Construire le payload selon le grant
    payload = {
        "client_id": client_id,
        "grant_type": grant_type
    }
    if grant_type == "client_credentials":
        payload["client_secret"] = client_secret
    else:
        payload.update({
            "username": username,
            "password": password,
            "client_secret": client_secret
        })
    if scope:
        payload["scope"] = scope

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    # 4) Session + retries
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["POST"])
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.mount("http://", HTTPAdapter(max_retries=retries))

    try:
        resp = session.post(url, data=payload, headers=headers, timeout=12)
    except requests.RequestException as e:
        print(f"Erreur reseau lors de la recuperation du token : {e}")
        print(f"URL SSO utilisee: {url} | grant_type={grant_type} | client_id={client_id}")
        return None

    content_type = resp.headers.get("Content-Type", "")
    if resp.status_code != 200:
        # Essayer d'extraire l'erreur Keycloak
        err_msg = ""
        if "application/json" in content_type:
            try:
                j = resp.json()
                err_msg = f"{j.get('error')}: {j.get('error_description')}"
            except Exception:
                pass
        if not err_msg:
            err_msg = resp.text[:500].replace("\n", " ")
        print(f"Token SSO echec [{resp.status_code}] {err_msg}")
        print(f"URL SSO utilisee: {url} | grant_type={grant_type} | client_id={client_id}")
        return None

    # 5) Extraire access_token
    try:
        data = resp.json()
    except ValueError:
        print(f"Reponse SSO non JSON: {resp.text[:200]}")
        return None

    access_token = data.get("access_token")
    if not access_token:
        print(f"'access_token' absent dans la reponse SSO: {data}")
        return None

    if "expires_in" in data:
        print(f"Token recupere (expire dans {data['expires_in']}s)")
    else:
        print("Token recupere")

    return access_token

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
        software = creds.get("software", "batigest")
        # Vérifier SQL Server / HFSQL selon logiciel
        if software == "codial":
            if "hfsql" in creds:
                hf = creds["hfsql"]
                host_value = f"DSN={hf['dsn']}" if hf.get("dsn") else hf.get("host", "localhost")
                conn = connect_to_hfsql(
                    host_value,
                    hf.get("user", "admin"),
                    hf.get("password", ""),
                    hf.get("database", "HFSQL"),
                    hf.get("port", "4900"),
                )
                sql_connected = conn is not None
                if conn:
                    conn.close()
        else:
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
    if not creds or "postgres" not in creds:
        return None, None

    software = creds.get("software", "batigest")
    pg = creds["postgres"]

    postgres_conn = connect_to_postgres(
        pg["host"], pg["user"], pg["password"], pg["database"], pg.get("port", "5432")
    )
    # deuxième connexion: SQL Server ou HFSQL selon logiciel
    if software == "codial":
        hf = creds.get("hfsql")
        if not hf:
            return postgres_conn, None
        second_conn = connect_to_hfsql(
            hf.get("host", "localhost"),
            hf.get("user", "admin"),
            hf.get("password", ""),
            hf.get("database", "HFSQL"),
            hf.get("port", "4900"),
        )
    else:
        sql = creds.get("sqlserver")
        if not sql:
            return postgres_conn, None
        second_conn = connect_to_sqlserver(
            sql["server"], sql["user"], sql["password"], sql["database"]
        )

    return postgres_conn, second_conn

# ============================================================================
# 


