# app/routes/form_routes.py

# Module de gestion des routes pour le formulaire de connexion
# Ce fichier contient toutes les routes pour gérer les connexions aux bases de données
# et le transfert des données entre SQL Server et PostgreSQL

from datetime import datetime
from fastapi import APIRouter, Request, Form, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

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

# ============================================================================
# CONFIGURATION
# ============================================================================

# Création du routeur FastAPI
router = APIRouter()

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
    return templates.TemplateResponse("index.html", {
        "request": request,
        "sql_connected": sql_connected,
        "pg_connected": pg_connected
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
        "pg_connected": pg_connected
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
        "pg_connected": pg_connected
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

    if not creds or "sqlserver" not in creds or "postgres" not in creds:
        message = "❌ Merci de renseigner les informations de connexion SQL Server et PostgreSQL avant de lancer le transfert."
    else:
        success, message = transfer_chantiers()
    
    sql_connected, pg_connected = check_connection_status()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": message,
        "sql_connected": sql_connected,
        "pg_connected": pg_connected
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
    try:
        success = transfer_chantiers_vers_batisimply()
        if success:
            message = "✅ Chantier créé avec succès dans BatiSimply."
        else:
            message = "❌ Échec de la création du chantier dans BatiSimply."

    except Exception as e:
        message = f"❌ Erreur lors de la création du chantier : {str(e)}"

    sql_connected, pg_connected = check_connection_status()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": message,
        "sql_connected": sql_connected,
        "pg_connected": pg_connected
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
    try:
        success = transfer_heures_to_postgres()
        if success:
            message = "✅ Heures récupérées et insérées dans PostgreSQL avec succès."
        else:
            message = "❌ Échec du transfert des heures depuis BatiSimply."

    except Exception as e:
        message = f"❌ Erreur lors du transfert des heures : {str(e)}"

    sql_connected, pg_connected = check_connection_status()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": message,
        "sql_connected": sql_connected,
        "pg_connected": pg_connected
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
    try:
        success = update_code_projet_chantiers()
        if success:
            message = "✅ Codes projet mis à jour avec succès dans PostgreSQL."
        else:
            message = "❌ Échec de la mise à jour des codes projet dans PostgreSQL."    

    except Exception as e:
        message = f"❌ Erreur lors de la mise à jour des codes projet : {str(e)}"

    sql_connected, pg_connected = check_connection_status()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": message,
        "sql_connected": sql_connected,
        "pg_connected": pg_connected
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
    try:
        transferred_count = transfer_heures_to_sqlserver()
        if transferred_count > 0:
            message = f"✅ {transferred_count} heure(s) envoyée(s) avec succès dans Batigest."
        else:
            message = "ℹ️ Aucune heure à transférer ou aucune correspondance trouvée."
    except Exception as e:
        message = f"❌ Erreur lors du transfert des heures vers Batigest : {str(e)}"

    sql_connected, pg_connected = check_connection_status()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": message,
        "sql_connected": sql_connected,
        "pg_connected": pg_connected
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
    try:
        success, message = sync_batigest_to_batisimply()
    except Exception as e:
        success = False
        message = f"❌ Erreur lors de la synchronisation : {e}"
    
    sql_connected, pg_connected = check_connection_status()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": message,
        "sql_connected": sql_connected,
        "pg_connected": pg_connected
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
    try:
        success, message = sync_batisimply_to_batigest()
    except Exception as e:
        success = False
        message = f"❌ Erreur lors de la synchronisation : {e}"
    
    sql_connected, pg_connected = check_connection_status()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": message,
        "sql_connected": sql_connected,
        "pg_connected": pg_connected
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
        "pg_connected": pg_connected
    })

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/configuration", response_class=HTMLResponse)
async def configuration_page(request: Request):
    # Vérifier si l'utilisateur est connecté
    if not request.session.get("authenticated"):
        return RedirectResponse(url="/login", status_code=303)
    
    creds = load_credentials()
    mode = creds.get("mode", "chantier") if creds else "chantier"
    return templates.TemplateResponse("configuration.html", {"request": request, "mode": mode})

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
    creds = load_credentials()
    if creds:
        creds["mode"] = type  # type sera "chantier" ou "devis"
        save_credentials(creds)
        print(f"Mode mis à jour en: {type}")
    return RedirectResponse(url="/configuration", status_code=303) #templates.TemplateResponse("configuration.html", {"request": request})
