# Routes pour la gestion des licences
# Ce fichier contient les routes FastAPI pour gérer les licences

from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.services.licences import (
    create_licenses_table, add_license, get_license_info, validate_license,
    update_license_usage, deactivate_license, get_all_licenses,
    format_license_key, get_license_status_text, days_until_expiration
)
from app.services.connex import connect_to_postgres, load_credentials
from app.utils.templates_engine import templates
import datetime
from typing import Optional
from pydantic import BaseModel

# Créer le router pour les routes de licences
router = APIRouter(prefix="/licenses", tags=["licenses"])

# Modèles Pydantic pour les requêtes API
class CreateLicenseRequest(BaseModel):
    client_name: str
    client_email: str
    company_name: Optional[str] = None
    duration_days: int = 365
    max_usage: int = -1
    notes: Optional[str] = None

class ValidateLicenseRequest(BaseModel):
    license_key: str

# ============================================================================
# ROUTES D'AFFICHAGE
# ============================================================================

@router.get("/", response_class=HTMLResponse)
async def license_dashboard(request: Request):
    """
    Page principale de gestion des licences.
    """
    try:
        # Charger les identifiants PostgreSQL
        creds = load_credentials()
        if not creds or 'postgresql' not in creds:
            return templates.TemplateResponse("license_dashboard.html", {
                "request": request,
                "licenses": [],
                "error": "Configuration PostgreSQL manquante"
            })
        
        # Se connecter à PostgreSQL
        pg_creds = creds['postgresql']
        conn = connect_to_postgres(
            pg_creds['host'],
            pg_creds['user'],
            pg_creds['password'],
            pg_creds['database'],
            pg_creds.get('port', '5432')
        )
        
        if not conn:
            return templates.TemplateResponse("license_dashboard.html", {
                "request": request,
                "licenses": [],
                "error": "Impossible de se connecter à la base de données"
            })
        
        # Créer la table si elle n'existe pas
        create_licenses_table(conn)
        
        # Récupérer toutes les licences
        licenses = get_all_licenses(conn)
        
        # Ajouter des informations calculées
        for license_info in licenses:
            license_info['status_text'] = get_license_status_text(license_info)
            license_info['days_until_expiration'] = days_until_expiration(license_info)
            license_info['formatted_key'] = format_license_key(license_info['license_key'])
        
        conn.close()
        
        return templates.TemplateResponse("license_dashboard.html", {
            "request": request,
            "licenses": licenses
        })
        
    except Exception as e:
        return templates.TemplateResponse("license_dashboard.html", {
            "request": request,
            "licenses": [],
            "error": f"Erreur lors du chargement des licences: {str(e)}"
        })

@router.get("/create", response_class=HTMLResponse)
async def create_license_form(request: Request):
    """
    Formulaire de création d'une nouvelle licence.
    """
    return templates.TemplateResponse("create_license.html", {"request": request})

@router.get("/{license_key}", response_class=HTMLResponse)
async def license_details(request: Request, license_key: str):
    """
    Affiche les détails d'une licence spécifique.
    """
    try:
        creds = load_credentials()
        if not creds or 'postgresql' not in creds:
            return RedirectResponse(url="/licenses/", status_code=302)
        
        pg_creds = creds['postgresql']
        conn = connect_to_postgres(
            pg_creds['host'],
            pg_creds['user'],
            pg_creds['password'],
            pg_creds['database'],
            pg_creds.get('port', '5432')
        )
        
        if not conn:
            return RedirectResponse(url="/licenses/", status_code=302)
        
        license_info = get_license_info(conn, license_key)
        conn.close()
        
        if not license_info:
            return RedirectResponse(url="/licenses/", status_code=302)
        
        # Ajouter des informations calculées
        license_info['status_text'] = get_license_status_text(license_info)
        license_info['days_until_expiration'] = days_until_expiration(license_info)
        license_info['formatted_key'] = format_license_key(license_info['license_key'])
        
        return templates.TemplateResponse("license_details.html", {
            "request": request,
            "license": license_info
        })
        
    except Exception as e:
        return RedirectResponse(url="/licenses/", status_code=302)

# ============================================================================
# ROUTES API
# ============================================================================

@router.post("/api/create")
async def api_create_license(request: CreateLicenseRequest):
    """
    API pour créer une nouvelle licence.
    """
    try:
        # Charger les identifiants PostgreSQL
        creds = load_credentials()
        if not creds or 'postgresql' not in creds:
            raise HTTPException(status_code=500, detail="Configuration PostgreSQL manquante")
        
        pg_creds = creds['postgresql']
        conn = connect_to_postgres(
            pg_creds['host'],
            pg_creds['user'],
            pg_creds['password'],
            pg_creds['database'],
            pg_creds.get('port', '5432')
        )
        
        if not conn:
            raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
        
        # Créer la table si elle n'existe pas
        create_licenses_table(conn)
        
        # Créer la licence
        license_key = add_license(
            conn=conn,
            client_name=request.client_name,
            client_email=request.client_email,
            company_name=request.company_name,
            duration_days=request.duration_days,
            max_usage=request.max_usage,
            notes=request.notes
        )
        
        conn.close()
        
        if license_key:
            return {
                "success": True,
                "message": "Licence créée avec succès",
                "license_key": license_key,
                "formatted_key": format_license_key(license_key)
            }
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la création de la licence")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@router.post("/api/validate")
async def api_validate_license(request: ValidateLicenseRequest):
    """
    API pour valider une licence.
    """
    try:
        # Charger les identifiants PostgreSQL
        creds = load_credentials()
        if not creds or 'postgresql' not in creds:
            raise HTTPException(status_code=500, detail="Configuration PostgreSQL manquante")
        
        pg_creds = creds['postgresql']
        conn = connect_to_postgres(
            pg_creds['host'],
            pg_creds['user'],
            pg_creds['password'],
            pg_creds['database'],
            pg_creds.get('port', '5432')
        )
        
        if not conn:
            raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
        
        # Valider la licence
        is_valid, message = validate_license(conn, request.license_key)
        
        if is_valid:
            # Mettre à jour les statistiques d'utilisation
            update_license_usage(conn, request.license_key)
            
            # Récupérer les informations de la licence
            license_info = get_license_info(conn, request.license_key)
            conn.close()
            
            return {
                "success": True,
                "message": message,
                "license_info": license_info
            }
        else:
            conn.close()
            raise HTTPException(status_code=400, detail=message)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@router.post("/api/deactivate/{license_key}")
async def api_deactivate_license(license_key: str):
    """
    API pour désactiver une licence.
    """
    try:
        creds = load_credentials()
        if not creds or 'postgresql' not in creds:
            raise HTTPException(status_code=500, detail="Configuration PostgreSQL manquante")
        
        pg_creds = creds['postgresql']
        conn = connect_to_postgres(
            pg_creds['host'],
            pg_creds['user'],
            pg_creds['password'],
            pg_creds['database'],
            pg_creds.get('port', '5432')
        )
        
        if not conn:
            raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
        
        success = deactivate_license(conn, license_key)
        conn.close()
        
        if success:
            return {"success": True, "message": "Licence désactivée avec succès"}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la désactivation")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@router.get("/api/list")
async def api_list_licenses():
    """
    API pour lister toutes les licences.
    """
    try:
        creds = load_credentials()
        if not creds or 'postgresql' not in creds:
            raise HTTPException(status_code=500, detail="Configuration PostgreSQL manquante")
        
        pg_creds = creds['postgresql']
        conn = connect_to_postgres(
            pg_creds['host'],
            pg_creds['user'],
            pg_creds['password'],
            pg_creds['database'],
            pg_creds.get('port', '5432')
        )
        
        if not conn:
            raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données")
        
        licenses = get_all_licenses(conn)
        conn.close()
        
        # Ajouter des informations calculées
        for license_info in licenses:
            license_info['status_text'] = get_license_status_text(license_info)
            license_info['days_until_expiration'] = days_until_expiration(license_info)
            license_info['formatted_key'] = format_license_key(license_info['license_key'])
        
        return {"success": True, "licenses": licenses}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

# ============================================================================
# ROUTES DE REDIRECTION
# ============================================================================

@router.post("/create")
async def create_license(
    request: Request,
    client_name: str = Form(...),
    client_email: str = Form(...),
    company_name: Optional[str] = Form(None),
    duration_days: int = Form(365),
    max_usage: int = Form(-1),
    notes: Optional[str] = Form(None)
):
    """
    Traitement du formulaire de création de licence.
    """
    try:
        # Charger les identifiants PostgreSQL
        creds = load_credentials()
        if not creds or 'postgresql' not in creds:
            return RedirectResponse(url="/licenses/create", status_code=302)
        
        pg_creds = creds['postgresql']
        conn = connect_to_postgres(
            pg_creds['host'],
            pg_creds['user'],
            pg_creds['password'],
            pg_creds['database'],
            pg_creds.get('port', '5432')
        )
        
        if not conn:
            return RedirectResponse(url="/licenses/create", status_code=302)
        
        # Créer la table si elle n'existe pas
        create_licenses_table(conn)
        
        # Créer la licence
        license_key = add_license(
            conn=conn,
            client_name=client_name,
            client_email=client_email,
            company_name=company_name,
            duration_days=duration_days,
            max_usage=max_usage,
            notes=notes
        )
        
        conn.close()
        
        if license_key:
            return RedirectResponse(url=f"/licenses/{license_key}", status_code=302)
        else:
            return RedirectResponse(url="/licenses/create", status_code=302)
            
    except Exception as e:
        return RedirectResponse(url="/licenses/create", status_code=302) 