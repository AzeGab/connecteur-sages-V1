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

def connect_to_hfsql(host: str, user: str = "admin", password: str = "", database: str = "HFSQL", port: str = "4900"):
    """
    Établit une connexion ODBC à HFSQL (Client/Serveur).

    - Requiert l'installation du pilote ODBC PC SOFT (HFSQL Client/Serveur)
    - Connexion "DSN-less" avec Driver explicite
    - Supporte un host de type "DSN=NomDeDSN" si vous utilisez un DSN Windows
    """
    try:
        # Si un DSN Windows est fourni (ex: "DSN=MON_DSN"), utiliser tel quel
        if host.upper().startswith("DSN="):
            conn_str = f"{host};UID={user};PWD={password}"
            conn = pypyodbc.connect(conn_str)
            print("✅ Connexion HFSQL via DSN réussie")
            return conn

        # Essayer plusieurs noms de driver possibles
        driver_candidates = [
            "HFSQL Client/Server (Unicode)",
            "HFSQL Client/Server",
            "HFSQL (Unicode)",
            "HFSQL",
        ]

        last_error = None
        for drv in driver_candidates:
            try:
                conn_str = (
                    "Driver={{{driver}}};"
                    "Server Name={host};"
                    "Server Port={port};"
                    "Database={database};"
                    "UID={user};"
                    "PWD={password}"
                ).format(driver=drv, host=host, port=port, database=database, user=user, password=password)
                conn = pypyodbc.connect(conn_str)
                print(f"✅ Connexion HFSQL réussie avec le driver '{drv}'")
                return conn
            except Exception as e:  # garder la dernière erreur pour diagnostic
                last_error = e
                continue

        print("❌ Erreur HFSQL (pilote/DSN):", last_error)
        print("ℹ️ Vérifiez que le pilote ODBC HFSQL Client/Serveur est installé et que le nom du driver est correct.")
        return None
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
        print(f"❌ Paramètres BatiSimply manquants ({grant_type}) : {', '.join(missing)}")
        print("ℹ️ Renseigne la section 'batisimply' dans credentials.json ou les variables d'environnement BATISIMPLY_*.")
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
        print(f"❌ Erreur réseau lors de la récupération du token : {e}")
        print(f"ℹ️ URL SSO utilisée: {url} | grant_type={grant_type} | client_id={client_id}")
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
        print(f"❌ Token SSO échec [{resp.status_code}] {err_msg}")
        print(f"ℹ️ URL SSO utilisée: {url} | grant_type={grant_type} | client_id={client_id}")
        return None

    # 5) Extraire access_token
    try:
        data = resp.json()
    except ValueError:
        print(f"❌ Réponse SSO non JSON: {resp.text[:200]}")
        return None

    access_token = data.get("access_token")
    if not access_token:
        print(f"❌ 'access_token' absent dans la réponse SSO: {data}")
        return None

    if "expires_in" in data:
        print(f"✅ Token récupéré (expire dans {data['expires_in']}s)")
    else:
        print("✅ Token récupéré")

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


