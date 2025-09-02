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
    save_credentials,
    load_credentials,
    check_connection_status
)

# Services - Chantiers
from app.services.chantier import (
    transfer_chantiers,
    transfer_chantiers_vers_batisimply,
    update_code_projet_chantiers,
    recup_chantiers_batisimply,
    recup_code_projet_chantiers,
    sync_batigest_to_batisimply,
    sync_batisimply_to_batigest,
    init_postgres_table
)

# Services - Heures
from app.services.heures import (
    transfer_heures_to_postgres,
    transfer_heures_to_sqlserver
)

# Services - Devis
from app.services.devis import transfer_devis

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
        message = "✅ Connexion SQL Server réussie !"
    else:
        message = "❌ Connexion SQL Server échouée."
    
    sql_connected, pg_connected = check_connection_status()
    return templates.TemplateResponse("configuration.html", {
        "request": request,
        "message": message,
        "sql_connected": sql_connected,
        "pg_connected": pg_connected,
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
        message = "✅ Connexion PostgreSQL réussie !"
    else:
        message = "❌ Connexion PostgreSQL échouée."
    
    sql_connected, pg_connected = check_connection_status()
    return templates.TemplateResponse("configuration.html", {
        "request": request,
        "message": message,
        "sql_connected": sql_connected,
        "pg_connected": pg_connected,
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
        message = "❌ Merci de renseigner les informations de connexion SQL Server et PostgreSQL avant de lancer le transfert."
    else:
        if debug_mode:
            (success, message), logs = _capture_output(transfer_chantiers)
            debug_output = f"=== Debug: /transfer ===\n{logs}"
        else:
            success, message = transfer_chantiers()
    
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
            message = "✅ Chantier créé avec succès dans BatiSimply."
        else:
            message = "❌ Échec de la création du chantier dans BatiSimply."

    except Exception as e:
        message = f"❌ Erreur lors de la création du chantier : {str(e)}"

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
            success, logs = _capture_output(transfer_heures_to_postgres)
            debug_output = f"=== Debug: /recup-heures ===\n{logs}"
        else:
            success = transfer_heures_to_postgres()
        if success:
            message = "✅ Heures récupérées et insérées dans PostgreSQL avec succès."
        else:
            message = "❌ Échec du transfert des heures depuis BatiSimply."

    except Exception as e:
        message = f"❌ Erreur lors du transfert des heures : {str(e)}"

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
            message = "✅ Codes projet mis à jour avec succès dans PostgreSQL."
        else:
            message = "❌ Échec de la mise à jour des codes projet dans PostgreSQL."    

    except Exception as e:
        message = f"❌ Erreur lors de la mise à jour des codes projet : {str(e)}"

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
            message = f"✅ {transferred_count} heure(s) envoyée(s) avec succès dans Batigest."
        else:
            message = "ℹ️ Aucune heure à transférer ou aucune correspondance trouvée."
    except Exception as e:
        message = f"❌ Erreur lors du transfert des heures vers Batigest : {str(e)}"

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
            (success, message), logs = _capture_output(sync_batigest_to_batisimply)
            debug_output = f"=== Debug: /sync-batigest-to-batisimply ===\n{logs}"
        else:
            success, message = sync_batigest_to_batisimply()
    except Exception as e:
        success = False
        message = f"❌ Erreur lors de la synchronisation : {e}"
    
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
            (success, message), logs = _capture_output(sync_batisimply_to_batigest)
            debug_output = f"=== Debug: /sync-batisimply-to-batigest ===\n{logs}"
        else:
            success, message = sync_batisimply_to_batigest()
    except Exception as e:
        success = False
        message = f"❌ Erreur lors de la synchronisation : {e}"
    
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

@router.post("/init-table", response_class=HTMLResponse)
async def init_table_route(request: Request):
    """
    Route pour initialiser la table PostgreSQL.
    
    Args:
        request (Request): Requête FastAPI
        
    Returns:
        TemplateResponse: Page HTML avec le message de résultat
    """
    try:
        success = init_postgres_table()
        if success:
            message = "✅ Table PostgreSQL initialisée avec succès"
        else:
            message = "❌ Erreur lors de l'initialisation de la table"
    except Exception as e:
        message = f"❌ Erreur lors de l'initialisation : {e}"
    
    sql_connected, pg_connected = check_connection_status()
    return templates.TemplateResponse("configuration.html", {
        "request": request,
        "message": message,
        "sql_connected": sql_connected,
        "pg_connected": pg_connected,
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
        "current_section": "system",
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
        print(f"🔍 Tentative de mise à jour de la licence: {license_key[:8]}...")
        
        # Valider la clé de licence avec rafraîchissement
        is_valid, license_info = refresh_license_validation(license_key)
        
        print(f"📊 Résultat de validation: {is_valid}")
        if license_info:
            print(f"📋 Données de licence: {license_info}")
        
        if is_valid and license_info:
            # La licence est déjà sauvegardée par refresh_license_validation
            message = "✅ Clé de licence validée et enregistrée avec succès !"
            license_valid = True
            license_expiry_date = license_info.get("expires_at")
            print("✅ Licence sauvegardée avec succès")
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
            
            message = "❌ Clé de licence invalide ou expirée. Veuillez vérifier votre clé."
            license_valid = False
            license_expiry_date = None
            print("❌ Licence invalide mais sauvegardée")
        
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
        print(f"💥 Erreur lors de la mise à jour: {str(e)}")
        message = f"❌ Erreur lors de la validation : {str(e)}"
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
        print(f"🔍 Tentative de rafraîchissement de la licence: {license_key[:8]}...")
        
        # Valider la clé de licence
        is_valid, license_data = refresh_license_validation(license_key)
        
        print(f"📊 Résultat de validation: {is_valid}")
        if license_data:
            print(f"📋 Données de licence: {license_data}")
        
        if is_valid:
            # Sauvegarder les informations de licence mises à jour
            save_license_info(license_key, license_data)
            print("✅ Licence sauvegardée avec succès")
            
            return JSONResponse({
                "success": True,
                "message": "Licence validée avec succès",
                "expires_at": license_data.get("expires_at"),
                "client_name": license_data.get("client_name")
            })
        else:
            print("❌ Licence invalide ou expirée")
            return JSONResponse({
                "success": False,
                "message": "Licence invalide ou expirée",
                "details": license_data if isinstance(license_data, str) else "Validation échouée"
            }, status_code=400)
            
    except Exception as e:
        print(f"💥 Erreur lors du rafraîchissement: {str(e)}")
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
                "message": "Licence expirée ou invalide"
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