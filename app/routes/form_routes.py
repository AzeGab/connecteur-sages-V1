# app/routes/form_routes.py

# Module de gestion des routes pour le formulaire de connexion
# Ce fichier contient toutes les routes pour gérer les connexions aux bases de données
# et le transfert des données entre SQL Server et PostgreSQL

from datetime import datetime
from fastapi import APIRouter, Request, Form, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import os
import io
from contextlib import redirect_stdout, redirect_stderr

# Import du moteur de templates depuis main.py pour garantir le bon chemin
from app.utils.paths import templates_path
templates = Jinja2Templates(directory=templates_path)

# Services - Connexion
from app.services.connex import (
    connect_to_sqlserver,
    connect_to_postgres,
    connect_to_hfsql,
    save_credentials,
    load_credentials,
    check_connection_status
)

import app.services.batigest as batigest_services
import app.services.codial as codial_services

# Services - Licence
from app.services.license import (
    validate_license_key,
    save_license_info,
    load_license_info,
    is_license_valid,
    get_license_expiry_date,
    get_client_name,
    refresh_license_validation
)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Création du routeur FastAPI
router = APIRouter()

# =============================================================
# DEBUG MODE (activable via DEBUG_CONNECTEUR=true)
# =============================================================
def _is_debug_mode():
    return os.getenv("DEBUG_CONNECTEUR", "false").lower() == "true"

def _capture_output(func, *args, **kwargs):
    buffer = io.StringIO()
    with redirect_stdout(buffer), redirect_stderr(buffer):
        result = func(*args, **kwargs)
    return result, buffer.getvalue()

def _effective_debug_mode():
    creds = load_credentials() or {}
    return _is_debug_mode() or bool(creds.get("debug", False))

# =============================================================
# AIDE: Formatage des messages pour l'UI (résumé + détails)
# =============================================================
def _split_message_for_display(message: str):
    if not message:
        return None, None
    text = str(message)
    # 1) Si c'est une représentation d'un tuple d'exception type ("HY090", "[HY090] ..."),
    #    extraire la partie message humaine (2ème élément)
    try:
        import re
        m = re.match(r"^\('.*?',\s*\"([\s\S]*)\"\)$", text)
        if m:
            text = m.group(1)
    except Exception:
        pass
    # 2) Décoder les séquences échappées (\r\n, \t, etc.)
    try:
        import codecs
        text = codecs.decode(text, 'unicode_escape')
    except Exception:
        pass
    # 3) Normalisation robuste des sauts de ligne et tabulations (gère \r\n réels)
    try:
        import re
        text = re.sub(r"(\r\n|\n|\r)+", "\n", text)
        text = text.replace("\t", "    ")
    except Exception:
        pass
    stripped = text.strip()
    # Construire un résumé court (1ère ligne ou 160 chars)
    if "\n" in stripped:
        first_line, rest = stripped.split("\n", 1)
    else:
        first_line, rest = stripped, ""
    summary = first_line.strip()
    # 4) Enrichir légèrement le résumé si on repère un code ODBC [HYxxx]
    try:
        import re
        code_match = re.search(r"\[(H[Yy]\d{3})\]", stripped)
        if code_match and code_match.group(1) not in summary:
            summary = f"{summary} (ODBC {code_match.group(1)})"
    except Exception:
        pass
    if len(summary) > 160:
        summary = summary[:160] + "…"
    # Toujours fournir des détails si le message est long ou si du contenu suit
    details = rest.strip() if rest.strip() else (stripped if len(stripped) > 160 else None)
    return summary, details

# ============================================================================
# ROUTES PRINCIPALES
# ============================================================================

@router.get("/", response_class=HTMLResponse)
async def form_page(request: Request):
    """
    Route principale affichant le formulaire de connexion.
    
    Args:
        request (Request): Requête FastAPI
        
    Returns:
        TemplateResponse: Page HTML du formulaire
    """
    sql_connected, pg_connected = check_connection_status()
    creds = load_credentials() or {}
    return templates.TemplateResponse("index.html", {
        "request": request,
        "sql_connected": sql_connected,
        "pg_connected": pg_connected,
        "software": creds.get("software", "batigest"),
        "debug_mode": _effective_debug_mode(),
        "debug_output": None
    })

# ============================================================================
# ROUTES DE CONNEXION
# ============================================================================

@router.post("/connect-sqlserver", response_class=HTMLResponse)
async def connect_sqlserver(
    request: Request,
    server: str = Form(...),
    user: str = Form(...),
    password: str = Form(...),
    database: str = Form(...)
):
    """
    Route pour tester et sauvegarder la connexion SQL Server.
    
    Args:
        request (Request): Requête FastAPI
        server (str): Nom ou adresse du serveur SQL
        user (str): Nom d'utilisateur
        password (str): Mot de passe
        database (str): Nom de la base de données
        
    Returns:
        TemplateResponse: Page HTML avec le message de résultat
    """
    debug_mode = _effective_debug_mode()
    debug_output = None
    if debug_mode:
        try:
            import time, pyodbc, struct
            start = time.perf_counter()
            drivers = ", ".join(pyodbc.drivers())
            arch = struct.calcsize('P') * 8
        except Exception:
            start = None
            drivers = "(drivers indisponibles)"
            arch = "?"
        conn, logs = _capture_output(connect_to_sqlserver, server, user, password, database)
        elapsed = (time.perf_counter() - start) * 1000 if start else None
        header = (
            "=== Debug: /connect-sqlserver ===\n"
            f"Server={server} DB={database} User={user}\n"
            f"Python bits={arch}\nODBC Drivers=[{drivers}]\n"
        )
        if elapsed is not None:
            header += f"Elapsed={elapsed:.1f} ms\n"
        debug_output = header + logs
    else:
        conn = connect_to_sqlserver(server, user, password, database)
    if conn:
        # Si la connexion réussit, on sauvegarde les identifiants
        creds = load_credentials() or {}
        creds["sqlserver"] = {
            "server": server,
            "user": user,
            "password": password,
            "database": database
        }
        save_credentials(creds)
        message = "[OK] Connexion SQL Server réussie !"
    else:
        message = "[ERREUR] Connexion SQL Server échouée."
    
    sql_connected, pg_connected = check_connection_status()
    return templates.TemplateResponse("configuration.html", {
        "request": request,
        "message": message,
        "sql_connected": sql_connected,
        "pg_connected": pg_connected,
        "software": (load_credentials() or {}).get("software", "batigest"),
        "debug_mode": debug_mode,
        "debug_output": debug_output,
        "current_section": "databases"
    })

@router.post("/connect-hfsql", response_class=HTMLResponse)
async def connect_hfsql(
    request: Request,
    server: str = Form(...),
    user: str = Form("admin"),
    password: str = Form(""),
    database: str = Form("HFSQL"),
    port: str = Form("4900"),
    dsn: str = Form(None)
):
    """
    Teste et sauvegarde la connexion HFSQL (Codial) si le logiciel sélectionné est Codial.
    """
    # Si software != codial, on refuse silencieusement et on affiche l’onglet
    creds = load_credentials() or {}
    debug_mode = _effective_debug_mode()
    debug_output = None
    if creds.get("software", "batigest") != "codial":
        message = "[INFO] Logiciel non configuré sur Codial. Basculez d’abord le logiciel."
    else:
        if debug_mode:
            # Collecte d'informations utiles
            try:
                import pyodbc, struct
                drivers = ", ".join(pyodbc.drivers())
                arch = struct.calcsize('P') * 8
            except Exception as e:
                drivers = f"Erreur drivers: {e}"
                arch = "?"
            header = (
                "=== Debug: /connect-hfsql ===\n"
                f"DSN={dsn or ''}\nHost={server}\nUser={user}\nDB={database}\nPort={port}\n"
                f"Python bits={arch}\nODBC Drivers=[{drivers}]\n"
            )
            host_value = f"DSN={dsn}" if dsn else server
            conn, logs = _capture_output(connect_to_hfsql, host_value, user, password, database, port)
            debug_output = header + logs
        else:
            host_value = f"DSN={dsn}" if dsn else server
            conn = connect_to_hfsql(host_value, user, password, database, port)
        if conn:
            creds["hfsql"] = {
                "host": server,
                "dsn": dsn,
                "user": user,
                "password": password,
                "database": database,
                "port": port
            }
            save_credentials(creds)
            message = "[OK] Connexion HFSQL réussie !"
            conn.close()
        else:
            message = "[ERREUR] Connexion HFSQL échouée."

    sql_connected, pg_connected = check_connection_status()
    return templates.TemplateResponse("configuration.html", {
        "request": request,
        "message": message,
        "sql_connected": sql_connected,
        "pg_connected": pg_connected,
        "debug_mode": debug_mode,
        "debug_output": debug_output,
        "software": (load_credentials() or {}).get("software", "batigest"),
        "current_section": "databases"
    })

@router.post("/connect-postgres", response_class=HTMLResponse)
async def connect_postgres(
    request: Request,
    host: str = Form(...),
    user: str = Form(...),
    password: str = Form(...),
    database: str = Form(...),
    port: str = Form("5432")
):
    """
    Route pour tester et sauvegarder la connexion PostgreSQL.
    
    Args:
        request (Request): Requête FastAPI
        host (str): Nom d'hôte ou adresse IP du serveur
        user (str): Nom d'utilisateur
        password (str): Mot de passe
        database (str): Nom de la base de données
        port (str): Port de connexion (défaut: 5432)
        
    Returns:
        TemplateResponse: Page HTML avec le message de résultat
    """
    debug_mode = _effective_debug_mode()
    debug_output = None
    if debug_mode:
        try:
            import time
            start = time.perf_counter()
        except Exception:
            start = None
        conn, logs = _capture_output(connect_to_postgres, host, user, password, database, port)
        elapsed = (time.perf_counter() - start) * 1000 if start else None
        header = (
            "=== Debug: /connect-postgres ===\n"
            f"Host={host} DB={database} User={user} Port={port}\n"
        )
        if elapsed is not None:
            header += f"Elapsed={elapsed:.1f} ms\n"
        debug_output = header + logs
    else:
        conn = connect_to_postgres(host, user, password, database, port)
    if conn:
        # Si la connexion réussit, on sauvegarde les identifiants
        creds = load_credentials() or {}
        creds["postgres"] = {
            "host": host,
            "user": user,
            "password": password,
            "database": database,
            "port": port
        }
        save_credentials(creds)
        message = "[OK] Connexion PostgreSQL réussie !"
    else:
        message = "[ERREUR] Connexion PostgreSQL échouée."
    
    sql_connected, pg_connected = check_connection_status()
    return templates.TemplateResponse("configuration.html", {
        "request": request,
        "message": message,
        "sql_connected": sql_connected,
        "pg_connected": pg_connected,
        "software": (load_credentials() or {}).get("software", "batigest"),
        "debug_mode": debug_mode,
        "debug_output": debug_output,
        "current_section": "databases"
    })

# ============================================================================
# ROUTES DE TRANSFERT
# ============================================================================

@router.post("/transfer", response_class=HTMLResponse)
async def transfer_data(request: Request):
    """
    Route pour lancer le transfert des données entre SQL Server et PostgreSQL.
    Vérifie d'abord que les deux connexions sont configurées avant de procéder.
    
    Args:
        request (Request): Requête FastAPI
        
    Returns:
        TemplateResponse: Page HTML avec le message de résultat du transfert
    """
    creds = load_credentials()

    debug_mode = _effective_debug_mode()
    debug_output = None
    if not creds or "sqlserver" not in creds or "postgres" not in creds:
        message = "[ERREUR] Merci de renseigner les informations de connexion SQL Server et PostgreSQL avant de lancer le transfert."
    else:
        if debug_mode:
            (success, message), logs = _capture_output(batigest_services.transfer_chantiers_sqlserver_to_postgres)
            debug_output = f"=== Debug: /transfer ===\n{logs}"
        else:
            success, message = batigest_services.transfer_chantiers_sqlserver_to_postgres()
    
    sql_connected, pg_connected = check_connection_status()
    creds = load_credentials() or {}
    msg_summary, msg_details = _split_message_for_display(message)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": msg_summary or message,
        "message_details": msg_details,
        "message_type": "success" if success else "error",
        "sql_connected": sql_connected,
        "pg_connected": pg_connected,
        "software": creds.get("software", "batigest"),
        "debug_mode": debug_mode,
        "debug_output": debug_output
    })

@router.post("/transfer-batisimply", response_class=HTMLResponse)
async def transfer_batisimply(request: Request):
    """
    Route pour transférer les chantiers vers BatiSimply.

    Args:
        request (Request): Objet de requête FastAPI.

    Returns:
        TemplateResponse: Affiche le résultat dans le template HTML.
    """
    debug_mode = _effective_debug_mode()
    debug_output = None
    try:
        if debug_mode:
            success, logs = _capture_output(transfer_chantiers_vers_batisimply)
            debug_output = f"=== Debug: /transfer-batisimply ===\n{logs}"
        else:
            success = transfer_chantiers_vers_batisimply()
        if success:
            message = "[OK] Chantier créé avec succès dans BatiSimply."
        else:
            message = "[ERREUR] Échec de la création du chantier dans BatiSimply."

    except Exception as e:
        message = f"[ERREUR] Erreur lors de la création du chantier : {str(e)}"

    sql_connected, pg_connected = check_connection_status()
    creds = load_credentials() or {}
    msg_summary, msg_details = _split_message_for_display(message)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": msg_summary or message,
        "message_details": msg_details,
        "message_type": "success" if success else "error",
        "sql_connected": sql_connected,
        "pg_connected": pg_connected,
        "software": creds.get("software", "batigest"),
        "debug_mode": debug_mode,
        "debug_output": debug_output
    })


@router.post("/recup-heures", response_class=HTMLResponse)
async def recup_heures_batisimply(request: Request):
    """
    Route pour récupérer les heures depuis BatiSimply et les insérer dans PostgreSQL.

    Args:
        request (Request): Objet de requête FastAPI.

    Returns:
        TemplateResponse: Affiche le résultat dans le template HTML.
    """
    debug_mode = _effective_debug_mode()
    debug_output = None
    try:
        if debug_mode:
            success, logs = _capture_output(batigest_services.transfer_heures_sqlserver_to_postgres)
            debug_output = f"=== Debug: /recup-heures ===\n{logs}"
        else:
            success, message = batigest_services.transfer_heures_sqlserver_to_postgres()
        if success:
            message = "[OK] Heures récupérées et insérées dans PostgreSQL avec succès."
        else:
            message = "[ERREUR] Échec du transfert des heures depuis BatiSimply."

    except Exception as e:
        message = f"[ERREUR] Erreur lors du transfert des heures : {str(e)}"

    sql_connected, pg_connected = check_connection_status()
    creds = load_credentials() or {}
    msg_summary, msg_details = _split_message_for_display(message)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": msg_summary or message,
        "message_details": msg_details,
        "message_type": "success" if success else "error",
        "sql_connected": sql_connected,
        "pg_connected": pg_connected,
        "software": creds.get("software", "batigest"),
        "debug_mode": debug_mode,
        "debug_output": debug_output
    })

@router.post("/update-code-projet", response_class=HTMLResponse)
async def update_code_projet(request: Request):
    """
    Route pour mettre à jour les codes projet des chantiers dans PostgreSQL.

    Args:
        request (Request): Objet de requête FastAPI.

    Returns:
        TemplateResponse: Affiche le résultat dans le template HTML.
    """ 
    debug_mode = _effective_debug_mode()
    debug_output = None
    try:
        if debug_mode:
            success, logs = _capture_output(update_code_projet_chantiers)
            debug_output = f"=== Debug: /update-code-projet ===\n{logs}"
        else:
            success = update_code_projet_chantiers()
        if success:
            message = "[OK] Codes projet mis à jour avec succès dans PostgreSQL."
        else:
            message = "[ERREUR] Échec de la mise à jour des codes projet dans PostgreSQL."    

    except Exception as e:
        message = f"[ERREUR] Erreur lors de la mise à jour des codes projet : {str(e)}"

    sql_connected, pg_connected = check_connection_status()
    creds = load_credentials() or {}
    msg_summary, msg_details = _split_message_for_display(message)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": msg_summary or message,
        "message_details": msg_details,
        "message_type": "success" if success else "error",
        "sql_connected": sql_connected,
        "pg_connected": pg_connected,
        "software": creds.get("software", "batigest"),
        "debug_mode": debug_mode,
        "debug_output": debug_output
    })


@router.post("/transfer-heure-batigest", response_class=HTMLResponse)
async def transfer_heure_batigest(request: Request):
    """
    Route pour transférer les heures depuis PostgreSQL vers SQL Server (Batigest).

    Args:
        request (Request): Objet de requête FastAPI.

    Returns:
        TemplateResponse: Retourne la page principale avec message de confirmation ou d'erreur.
    """
    debug_mode = _effective_debug_mode()
    debug_output = None
    try:
        if debug_mode:
            transferred_count, logs = _capture_output(transfer_heures_to_sqlserver)
            debug_output = f"=== Debug: /transfer-heure-batigest ===\n{logs}"
        else:
            transferred_count = transfer_heures_to_sqlserver()
        if transferred_count > 0:
            message = f"[OK] {transferred_count} heure(s) envoyée(s) avec succès dans Batigest."
        else:
            message = "[INFO] Aucune heure à transférer ou aucune correspondance trouvée."
    except Exception as e:
        message = f"[ERREUR] Erreur lors du transfert des heures vers Batigest : {str(e)}"

    sql_connected, pg_connected = check_connection_status()
    creds = load_credentials() or {}
    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": message,
        "sql_connected": sql_connected,
        "pg_connected": pg_connected,
        "software": creds.get("software", "batigest"),
        "debug_mode": debug_mode,
        "debug_output": debug_output
    })

@router.post("/sync-batigest-to-batisimply", response_class=HTMLResponse)
async def sync_batigest_to_batisimply_route(request: Request):
    """
    Route pour synchroniser les chantiers de Batigest vers Batisimply.
    
    Args:
        request (Request): Requête FastAPI
        
    Returns:
        TemplateResponse: Page HTML avec le message de résultat
    """
    debug_mode = _effective_debug_mode()
    debug_output = None
    try:
        if debug_mode:
            (success, message), logs = _capture_output(batigest_services.sync_sqlserver_to_batisimply)
            debug_output = f"=== Debug: /sync-batigest-to-batisimply ===\n{logs}"
        else:
            success, message = batigest_services.sync_sqlserver_to_batisimply()
    except Exception as e:
        success = False
        message = f"[ERREUR] Erreur lors de la synchronisation : {e}"
    
    sql_connected, pg_connected = check_connection_status()
    creds = load_credentials() or {}
    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": message,
        "sql_connected": sql_connected,
        "pg_connected": pg_connected,
        "software": creds.get("software", "batigest"),
        "debug_mode": debug_mode,
        "debug_output": debug_output
    })

@router.post("/sync-batisimply-to-batigest", response_class=HTMLResponse)
async def sync_batisimply_to_batigest_route(request: Request):
    """
    Route pour synchroniser les chantiers de Batisimply vers Batigest.
    
    Args:
        request (Request): Requête FastAPI
        
    Returns:
        TemplateResponse: Page HTML avec le message de résultat
    """
    debug_mode = _is_debug_mode()
    debug_output = None
    try:
        if debug_mode:
            (success, message), logs = _capture_output(batigest_services.sync_batisimply_to_sqlserver)
            debug_output = f"=== Debug: /sync-batisimply-to-batigest ===\n{logs}"
        else:
            success, message = batigest_services.sync_batisimply_to_sqlserver()
    except Exception as e:
        success = False
        message = f"[ERREUR] Erreur lors de la synchronisation : {e}"
    
    sql_connected, pg_connected = check_connection_status()
    creds = load_credentials() or {}
    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": message,
        "sql_connected": sql_connected,
        "pg_connected": pg_connected,
        "software": creds.get("software", "batigest"),
        "debug_mode": debug_mode,
        "debug_output": debug_output
    })

# ============================================================================
# ROUTES DE SYNCHRONISATION CODIAL
# ============================================================================

@router.post("/sync-codial-to-batisimply", response_class=HTMLResponse)
async def sync_codial_to_batisimply_route(request: Request):
    """
    Route pour synchroniser les données de Codial (HFSQL) vers BatiSimply.
    
    Args:
        request (Request): Requête FastAPI
        
    Returns:
        TemplateResponse: Page HTML avec le message de résultat
    """
    debug_mode = _effective_debug_mode()
    debug_output = None
    try:
        if debug_mode:
            (success, message), logs = _capture_output(codial_services.sync_hfsql_to_batisimply)
            debug_output = f"=== Debug: /sync-codial-to-batisimply ===\n{logs}"
        else:
            success, message = codial_services.sync_hfsql_to_batisimply()
    except Exception as e:
        success = False
        message = f"[ERREUR] Erreur lors de la synchronisation Codial -> BatiSimply : {e}"
    
    sql_connected, pg_connected = check_connection_status()
    creds = load_credentials() or {}
    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": message,
        "sql_connected": sql_connected,
        "pg_connected": pg_connected,
        "software": creds.get("software", "batigest"),
        "debug_mode": debug_mode,
        "debug_output": debug_output
    })

@router.post("/sync-batisimply-to-codial", response_class=HTMLResponse)
async def sync_batisimply_to_codial_route(request: Request):
    """
    Route pour synchroniser les données de BatiSimply vers Codial (HFSQL).
    
    Args:
        request (Request): Requête FastAPI
        
    Returns:
        TemplateResponse: Page HTML avec le message de résultat
    """
    debug_mode = _effective_debug_mode()
    debug_output = None
    try:
        if debug_mode:
            (success, message), logs = _capture_output(codial_services.sync_batisimply_to_hfsql)
            debug_output = f"=== Debug: /sync-batisimply-to-codial ===\n{logs}"
        else:
            success, message = codial_services.sync_batisimply_to_hfsql()
    except Exception as e:
        success = False
        message = f"[ERREUR] Erreur lors de la synchronisation BatiSimply -> Codial : {e}"
    
    sql_connected, pg_connected = check_connection_status()
    creds = load_credentials() or {}
    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": message,
        "sql_connected": sql_connected,
        "pg_connected": pg_connected,
        "software": creds.get("software", "batigest"),
        "debug_mode": debug_mode,
        "debug_output": debug_output
    })

@router.post("/init-batigest-tables", response_class=HTMLResponse)
async def init_batigest_tables_route(request: Request):
    """
    Route pour initialiser les tables PostgreSQL Batigest.
    
    Args:
        request (Request): Requête FastAPI
        
    Returns:
        TemplateResponse: Page HTML avec le message de résultat
    """
    try:
        success = batigest_services.init_batigest_tables()()
        if success:
            message = "[OK] Tables PostgreSQL Batigest initialisées avec succès"
        else:
            message = "[ERREUR] Erreur lors de l'initialisation des tables Batigest"
                
    except Exception as e:
        message = f"[ERREUR] Erreur lors de l'initialisation des tables Batigest : {e}"
    
    sql_connected, pg_connected = check_connection_status()
    creds = load_credentials() or {}
    return templates.TemplateResponse("configuration.html", {
        "request": request,
        "message": message,
        "sql_connected": sql_connected,
        "pg_connected": pg_connected,
        "software": creds.get("software", "batigest"),
        "current_section": "system"
    })

@router.post("/init-codial-tables", response_class=HTMLResponse)
async def init_codial_tables_route(request: Request):
    """
    Route pour initialiser les tables PostgreSQL Codial.
    
    Args:
        request (Request): Requête FastAPI
        
    Returns:
        TemplateResponse: Page HTML avec le message de résultat
    """
    try:
        success = codial_services.init_codial_tables()
        if success:
            message = "[OK] Tables PostgreSQL Codial initialisées avec succès"
        else:
            message = "[ERREUR] Erreur lors de l'initialisation des tables Codial"
                
    except Exception as e:
        message = f"[ERREUR] Erreur lors de l'initialisation des tables Codial : {e}"
    
    sql_connected, pg_connected = check_connection_status()
    creds = load_credentials() or {}
    return templates.TemplateResponse("configuration.html", {
        "request": request,
        "message": message,
        "sql_connected": sql_connected,
        "pg_connected": pg_connected,
        "software": creds.get("software", "batigest"),
        "current_section": "system"
    })

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/configuration", response_class=HTMLResponse)
async def configuration_page(request: Request):
    # Vérifier si l'utilisateur est connecté
    # if not request.session.get("authenticated"):
    #     return RedirectResponse(url="/login", status_code=303)
    
    creds = load_credentials()
    sql_connected, pg_connected = check_connection_status()
    
    # Récupérer les informations de licence
    license_info = load_license_info()
    license_key = None
    license_valid = is_license_valid()
    license_expiry_date = get_license_expiry_date()
    
    # Toujours afficher la clé sauvegardée, même si elle est invalide
    if license_info:
        license_key = license_info.get("key")
    
    return templates.TemplateResponse("configuration.html", {
        "request": request,
        "mode": creds.get("mode", "chantier") if creds else "chantier",
        "software": creds.get("software", "batigest") if creds else "batigest",
        "debug": creds.get("debug", False) if creds else False,
        "batisimply": creds.get("batisimply", {}) if creds else {},
        "license_key": license_key,
        "license_valid": license_valid,
        "license_expiry_date": license_expiry_date,
        "current_section": "license",
        "sql_connected": sql_connected,
        "pg_connected": pg_connected
    })

@router.get("/license-expired", response_class=HTMLResponse)
async def license_expired_page(request: Request):
    """
    Route pour afficher la page de licence expirée.
    
    Args:
        request (Request): Requête FastAPI
        
    Returns:
        TemplateResponse: Page HTML de licence expirée
    """
    # Récupérer les informations de licence pour l'affichage
    license_info = load_license_info()
    license_key = None
    license_expiry_date = None
    client_name = None
    
    if license_info:
        license_key = license_info.get("key")
        license_expiry_date = license_info.get("expiry_date")
        client_name = license_info.get("client_name")
    
    return templates.TemplateResponse("license_expired.html", {
        "request": request,
        "license_key": license_key,
        "license_expiry_date": license_expiry_date,
        "client_name": client_name
    })

@router.post("/login", response_class=HTMLResponse)
async def login(request: Request, password: str = Form(...)):
    if password == "gumgum":  # Le mot de passe est défini dans login.html
        request.session["authenticated"] = True
        return RedirectResponse(url="/configuration", status_code=303)
    else:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Mot de passe incorrect"
        })

@router.post("/update-mode")
def update_mode(request: Request, type: str = Form("chantier")):
    """
    Route pour mettre à jour le mode de données (chantier/devis).
    
    Args:
        request (Request): Requête FastAPI
        type (str): Type de données (chantier ou devis)
        
    Returns:
        TemplateResponse: Page HTML de configuration
    """
    creds = load_credentials() or {}
    creds["mode"] = type
    save_credentials(creds)
    
    sql_connected, pg_connected = check_connection_status()
    return templates.TemplateResponse("configuration.html", {
        "request": request,
        "message": f"Mode mis à jour : {type}",
        "mode": type,
        "software": creds.get("software", "batigest"),
        "debug": creds.get("debug", False),
        "batisimply": creds.get("batisimply", {}),
        "current_section": "mode",
        "sql_connected": sql_connected,
        "pg_connected": pg_connected
    })

@router.post("/update-software")
def update_software(request: Request, software: str = Form("batigest")):
    """
    Route pour mettre à jour le logiciel principal (codial/batigest).
    
    Args:
        request (Request): Requête FastAPI
        software (str): Logiciel principal (codial ou batigest)
        
    Returns:
        TemplateResponse: Page HTML de configuration
    """
    creds = load_credentials() or {}
    creds["software"] = software
    save_credentials(creds)
    
    sql_connected, pg_connected = check_connection_status()
    return templates.TemplateResponse("configuration.html", {
        "request": request,
        "message": f"Logiciel mis à jour : {software}",
        "software": software,
        "mode": creds.get("mode", "chantier"),
        "debug": creds.get("debug", False),
        "batisimply": creds.get("batisimply", {}),
        "current_section": "software",
        "sql_connected": sql_connected,
        "pg_connected": pg_connected
    })

@router.post("/update-debug")
def update_debug(request: Request, debug: str = Form("false")):
    """
    Active/Désactive le mode debug (persisté dans credentials.json).
    """
    creds = load_credentials() or {}
    creds["debug"] = (debug.lower() == "true")
    save_credentials(creds)

    sql_connected, pg_connected = check_connection_status()
    return templates.TemplateResponse("configuration.html", {
        "request": request,
        "message": f"Mode debug: {'activé' if creds['debug'] else 'désactivé'}",
        "mode": creds.get("mode", "chantier"),
        "software": creds.get("software", "batigest"),
        "debug": creds.get("debug", False),
        "batisimply": creds.get("batisimply", {}),
        "current_section": "system",
        "sql_connected": sql_connected,
        "pg_connected": pg_connected
    })

@router.post("/update-batisimply")
def update_batisimply(
    request: Request,
    sso_url: str = Form("https://sso.staging.batisimply.fr/auth/realms/jhipster/protocol/openid-connect/token"),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    grant_type: str = Form("password"),
    scope: str = Form("openid email profile"),
):
    creds = load_credentials() or {}
    creds["batisimply"] = {
        "sso_url": sso_url,
        "client_id": client_id,
        "client_secret": client_secret,
        "username": username,
        "password": password,
        "grant_type": grant_type,
        "scope": scope,
    }
    save_credentials(creds)

    sql_connected, pg_connected = check_connection_status()
    return templates.TemplateResponse("configuration.html", {
        "request": request,
        "message": "Configuration BatiSimply enregistrée",
        "mode": creds.get("mode", "chantier"),
        "software": creds.get("software", "batigest"),
        "debug": creds.get("debug", False),
        "batisimply": creds.get("batisimply", {}),
        "current_section": "batisimply",
        "sql_connected": sql_connected,
        "pg_connected": pg_connected
    })

@router.post("/update-license")
def update_license(request: Request, license_key: str = Form(...)):
    """
    Route pour mettre à jour la clé de licence.
    
    Args:
        request (Request): Requête FastAPI
        license_key (str): Clé de licence à sauvegarder
        
    Returns:
        TemplateResponse: Page HTML de configuration
    """
    try:
        print(f"[DEBUG] Tentative de mise à jour de la licence: {license_key[:8]}...")
        
        # Valider la clé de licence avec rafraîchissement
        is_valid, license_info = refresh_license_validation(license_key)
        
        print(f"[INFO] Résultat de validation: {is_valid}")
        if license_info:
            print(f"[INFO] Données de licence: {license_info}")
        
        if is_valid and license_info:
            # La licence est déjà sauvegardée par refresh_license_validation
            message = "[OK] Clé de licence validée et enregistrée avec succès !"
            license_valid = True
            license_expiry_date = license_info.get("expires_at")
            print("[OK] Licence sauvegardée avec succès")
        else:
            # Sauvegarder quand même la clé saisie (même invalide) pour que l'utilisateur puisse la voir
            if license_info:
                # Si on a des infos de licence (même invalide), les sauvegarder
                save_license_info(license_key, license_info)
            else:
                # Si pas d'infos, créer une entrée basique avec la clé invalide
                invalid_license_info = {
                    "key": license_key,
                    "is_active": False,
                    "expires_at": None,
                    "client_id": "invalide"
                }
                save_license_info(license_key, invalid_license_info)
            
            message = "[ERREUR] Clé de licence invalide ou expirée. Veuillez vérifier votre clé."
            license_valid = False
            license_expiry_date = None
            print("[ERREUR] Licence invalide mais sauvegardée")
        
        sql_connected, pg_connected = check_connection_status()
        creds = load_credentials()
        return templates.TemplateResponse("configuration.html", {
            "request": request,
            "message": message,
            "license_key": license_key,
            "license_valid": license_valid,
            "license_expiry_date": license_expiry_date,
            "mode": creds.get("mode", "chantier") if creds else "chantier",
            "software": creds.get("software", "batigest") if creds else "batigest",
            "current_section": "license",
            "sql_connected": sql_connected,
            "pg_connected": pg_connected
        })
        
    except Exception as e:
        print(f"[ERREUR] Erreur lors de la mise à jour: {str(e)}")
        message = f"[ERREUR] Erreur lors de la validation : {str(e)}"
        license_valid = False
        license_expiry_date = None
        
        sql_connected, pg_connected = check_connection_status()
        creds = load_credentials()
        return templates.TemplateResponse("configuration.html", {
            "request": request,
            "message": message,
            "license_key": license_key,
            "license_valid": license_valid,
            "license_expiry_date": license_expiry_date,
            "mode": creds.get("mode", "chantier") if creds else "chantier",
            "software": creds.get("software", "batigest") if creds else "batigest",
            "current_section": "license",
            "sql_connected": sql_connected,
            "pg_connected": pg_connected
        })

@router.post("/refresh-license")
async def refresh_license(request: Request, license_key: str = Form(...)):
    """
    Route pour rafraîchir la validation d'une licence.
    
    Args:
        request (Request): Requête FastAPI
        license_key (str): Clé de licence à valider
        
    Returns:
        JSONResponse: Résultat de la validation
    """
    try:
        print(f"[DEBUG] Tentative de rafraîchissement de la licence: {license_key[:8]}...")
        
        # Valider la clé de licence
        is_valid, license_data = refresh_license_validation(license_key)
        
        print(f"[INFO] Résultat de validation: {is_valid}")
        if license_data:
            print(f"[INFO] Données de licence: {license_data}")
        
        if is_valid:
            # Sauvegarder les informations de licence mises à jour
            save_license_info(license_key, license_data)
            print("[OK] Licence sauvegardée avec succès")
            
            return JSONResponse({
                "success": True,
                "message": "Licence validée avec succès",
                "expires_at": license_data.get("expires_at"),
                "client_name": license_data.get("client_name")
            })
        else:
            print("[ERREUR] Licence invalide ou expirée")
            return JSONResponse({
                "success": False,
                "message": "Licence invalide ou expirée",
                "details": license_data if isinstance(license_data, str) else "Validation échouée"
            }, status_code=400)
            
    except Exception as e:
        print(f"[ERREUR] Erreur lors du rafraîchissement: {str(e)}")
        return JSONResponse({
            "success": False,
            "message": f"Erreur lors de la validation : {str(e)}"
        }, status_code=500)

# ============================================================================
# ROUTES DE LICENCE
# ============================================================================

@router.get("/check-license-status")
async def check_license_status():
    """
    Route pour vérifier le statut de la licence.
    Utilisée par le JavaScript pour vérifier automatiquement la licence.
    
    Returns:
        JSONResponse: Statut de la licence et redirection si nécessaire
    """
    # Vérifier d'abord la licence locale
    if is_license_valid():
        return JSONResponse({
            "valid": True,
            "message": "Licence valide"
        })
    
    # Si la licence locale n'est pas valide, essayer de la rafraîchir
    license_info = load_license_info()
    if license_info and license_info.get("key"):
        # Tenter de rafraîchir la validation avec la clé locale
        is_valid, _ = refresh_license_validation(license_info.get("key"))
        if is_valid:
            return JSONResponse({
                "valid": True,
                "message": "Licence rafraîchie avec succès"
            })
        else:
            return JSONResponse({
                "valid": False,
                "redirect_to": "license-expired",
                "message": "Licence expirée ou invalide",
                "debug": {
                    "stored": license_info
                }
            })
    else:
        return JSONResponse({
            "valid": False,
            "redirect_to": "configuration",
            "message": "Aucune licence configurée"
        })

@router.get("/get-license-key")
async def get_license_key():
    """
    Route pour récupérer la clé de licence depuis les credentials.
    Utilisée par la page license_expired.html pour revérifier la licence.
    
    Returns:
        JSONResponse: Clé de licence stockée localement
    """
    license_info = load_license_info()
    if license_info and license_info.get("key"):
        return JSONResponse({
            "license_key": license_info.get("key"),
            "found": True
        })
    else:
        return JSONResponse({
            "license_key": None,
            "found": False,
            "message": "Aucune clé de licence trouvée dans les credentials"
        })

# ============================================================================
# ROUTES JSON POUR LA BARRE DE PROGRESSION
# ============================================================================

@router.post("/api/sync-batigest-to-batisimply")
async def api_sync_batigest_to_batisimply():
    """
    API pour la synchronisation Batigest -> BatiSimply avec retour JSON.
    
    Returns:
        JSONResponse: Résultat de la synchronisation
    """
    try:
        success, message = batigest_services.sync_sqlserver_to_batisimply()
        return JSONResponse({
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"[ERREUR] Erreur lors de la synchronisation Batigest -> BatiSimply : {str(e)}",
            "timestamp": datetime.now().isoformat()
        })

@router.post("/api/sync-batisimply-to-batigest")
async def api_sync_batisimply_to_batigest():
    """
    API pour la synchronisation BatiSimply -> Batigest avec retour JSON.
    
    Returns:
        JSONResponse: Résultat de la synchronisation
    """
    try:
        success, message = batigest_services.sync_batisimply_to_sqlserver()
        return JSONResponse({
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"[ERREUR] Erreur lors de la synchronisation BatiSimply -> Batigest : {str(e)}",
            "timestamp": datetime.now().isoformat()
        })

@router.post("/api/sync-codial-to-batisimply")
async def api_sync_codial_to_batisimply():
    """
    API pour la synchronisation Codial -> BatiSimply avec retour JSON.
    
    Returns:
        JSONResponse: Résultat de la synchronisation
    """
    try:
        success, message = codial_services.sync_hfsql_to_batisimply()
        return JSONResponse({
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"[ERREUR] Erreur lors de la synchronisation Codial -> BatiSimply : {str(e)}",
            "timestamp": datetime.now().isoformat()
        })

@router.post("/api/sync-batisimply-to-codial")
async def api_sync_batisimply_to_codial():
    """
    API pour la synchronisation BatiSimply -> Codial avec retour JSON.
    
    Returns:
        JSONResponse: Résultat de la synchronisation
    """
    try:
        success, message = codial_services.sync_batisimply_to_hfsql()
        return JSONResponse({
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"[ERREUR] Erreur lors de la synchronisation BatiSimply -> Codial : {str(e)}",
            "timestamp": datetime.now().isoformat()
        })
