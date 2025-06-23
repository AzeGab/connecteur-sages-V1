# Routes pour la gestion des licences
# Ce fichier contient les routes FastAPI pour gérer les licences

from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import os

# Import du module Supabase au lieu de PostgreSQL
from app.services.supabase_licences import (
    add_license, get_license_info, validate_license, deactivate_license,
    get_all_licenses, update_license_usage, format_license_key,
    get_license_status_text, days_until_expiration, setup_supabase_config
)

# Configuration des templates
templates = Jinja2Templates(directory="app/templates")

# Création du router
router = APIRouter(prefix="/licenses", tags=["licenses"])

# ============================================================================
# ROUTES WEB (INTERFACE UTILISATEUR)
# ============================================================================

@router.get("/", response_class=HTMLResponse)
async def license_dashboard(request: Request):
    """
    Affiche le tableau de bord des licences.
    """
    try:
        # Récupérer toutes les licences
        licenses = get_all_licenses()
        
        # Préparer les données pour l'affichage
        for license_info in licenses:
            license_info['status_text'] = get_license_status_text(license_info)
            license_info['days_until_expiration'] = days_until_expiration(license_info)
            license_info['formatted_key'] = format_license_key(license_info['license_key'])
        
        return templates.TemplateResponse("license_dashboard.html", {
            "request": request,
            "licenses": licenses,
            "total_licenses": len(licenses),
            "active_licenses": len([l for l in licenses if l['is_active']]),
            "expired_licenses": len([l for l in licenses if not l['is_active'] or l['expires_at'] < datetime.datetime.now()])
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
    Affiche le formulaire de création de licence.
    """
    return templates.TemplateResponse("create_license.html", {"request": request})

@router.post("/create")
async def create_license_post(
    request: Request,
    client_name: str = Form(...),
    client_email: str = Form(...),
    company_name: str = Form(None),
    duration_days: int = Form(365),
    max_usage: int = Form(-1),
    notes: str = Form(None)
):
    """
    Traite la création d'une nouvelle licence.
    """
    try:
        # Créer la licence
        license_key = add_license(
            client_name=client_name,
            client_email=client_email,
            company_name=company_name,
            duration_days=duration_days,
            max_usage=max_usage,
            notes=notes
        )
        
        if license_key:
            # Rediriger vers les détails de la licence
            return RedirectResponse(url=f"/licenses/{license_key}", status_code=303)
        else:
            return templates.TemplateResponse("create_license.html", {
                "request": request,
                "error": "Erreur lors de la création de la licence",
                "form_data": {
                    "client_name": client_name,
                    "client_email": client_email,
                    "company_name": company_name,
                    "duration_days": duration_days,
                    "max_usage": max_usage,
                    "notes": notes
                }
            })
            
    except Exception as e:
        return templates.TemplateResponse("create_license.html", {
            "request": request,
            "error": f"Erreur lors de la création de la licence: {str(e)}",
            "form_data": {
                "client_name": client_name,
                "client_email": client_email,
                "company_name": company_name,
                "duration_days": duration_days,
                "max_usage": max_usage,
                "notes": notes
            }
        })

@router.get("/{license_key}", response_class=HTMLResponse)
async def license_details(request: Request, license_key: str):
    """
    Affiche les détails d'une licence.
    """
    try:
        # Récupérer les informations de la licence
        license_info = get_license_info(license_key)
        
        if not license_info:
            raise HTTPException(status_code=404, detail="Licence non trouvée")
        
        # Préparer les données pour l'affichage
        license_info['status_text'] = get_license_status_text(license_info)
        license_info['days_until_expiration'] = days_until_expiration(license_info)
        license_info['formatted_key'] = format_license_key(license_info['license_key'])
        
        return templates.TemplateResponse("license_details.html", {
            "request": request,
            "license": license_info
        })
        
    except HTTPException:
        raise
    except Exception as e:
        return templates.TemplateResponse("license_details.html", {
            "request": request,
            "error": f"Erreur lors du chargement de la licence: {str(e)}"
        })

@router.post("/{license_key}/deactivate")
async def deactivate_license_post(request: Request, license_key: str):
    """
    Désactive une licence.
    """
    try:
        success = deactivate_license(license_key)
        
        if success:
            return RedirectResponse(url=f"/licenses/{license_key}", status_code=303)
        else:
            raise HTTPException(status_code=400, detail="Erreur lors de la désactivation")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

# ============================================================================
# ROUTES API (REST)
# ============================================================================

@router.post("/api/create")
async def api_create_license(
    client_name: str,
    client_email: str,
    company_name: Optional[str] = None,
    duration_days: int = 365,
    max_usage: int = -1,
    notes: Optional[str] = None
):
    """
    API pour créer une nouvelle licence.
    """
    try:
        license_key = add_license(
            client_name=client_name,
            client_email=client_email,
            company_name=company_name,
            duration_days=duration_days,
            max_usage=max_usage,
            notes=notes
        )
        
        if license_key:
            return {
                "success": True,
                "license_key": license_key,
                "message": "Licence créée avec succès"
            }
        else:
            raise HTTPException(status_code=400, detail="Erreur lors de la création de la licence")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@router.get("/api/validate/{license_key}")
async def api_validate_license(license_key: str):
    """
    API pour valider une licence.
    """
    try:
        is_valid, message = validate_license(license_key)
        
        if is_valid:
            # Mettre à jour les statistiques d'utilisation
            update_license_usage(license_key)
        
        return {
            "valid": is_valid,
            "message": message,
            "license_key": license_key
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@router.post("/api/deactivate/{license_key}")
async def api_deactivate_license(license_key: str):
    """
    API pour désactiver une licence.
    """
    try:
        success = deactivate_license(license_key)
        
        if success:
            return {
                "success": True,
                "message": "Licence désactivée avec succès"
            }
        else:
            raise HTTPException(status_code=400, detail="Erreur lors de la désactivation")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@router.get("/api/list")
async def api_list_licenses():
    """
    API pour lister toutes les licences.
    """
    try:
        licenses = get_all_licenses()
        
        # Préparer les données pour l'API
        for license_info in licenses:
            license_info['status_text'] = get_license_status_text(license_info)
            license_info['days_until_expiration'] = days_until_expiration(license_info)
            license_info['formatted_key'] = format_license_key(license_info['license_key'])
        
        return {
            "success": True,
            "licenses": licenses,
            "total": len(licenses)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@router.get("/api/info/{license_key}")
async def api_get_license_info(license_key: str):
    """
    API pour récupérer les informations d'une licence.
    """
    try:
        license_info = get_license_info(license_key)
        
        if not license_info:
            raise HTTPException(status_code=404, detail="Licence non trouvée")
        
        # Préparer les données pour l'API
        license_info['status_text'] = get_license_status_text(license_info)
        license_info['days_until_expiration'] = days_until_expiration(license_info)
        license_info['formatted_key'] = format_license_key(license_info['license_key'])
        
        return {
            "success": True,
            "license": license_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

# ============================================================================
# ROUTES DE CONFIGURATION
# ============================================================================

@router.get("/setup", response_class=HTMLResponse)
async def setup_licenses(request: Request):
    """
    Affiche la page de configuration Supabase.
    """
    return templates.TemplateResponse("license_setup.html", {"request": request})

@router.post("/setup")
async def setup_licenses_post(request: Request):
    """
    Lance la configuration Supabase.
    """
    try:
        setup_supabase_config()
        return templates.TemplateResponse("license_setup.html", {
            "request": request,
            "success": "Configuration Supabase lancée. Vérifiez les instructions dans la console."
        })
    except Exception as e:
        return templates.TemplateResponse("license_setup.html", {
            "request": request,
            "error": f"Erreur lors de la configuration: {str(e)}"
        }) 