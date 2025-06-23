# -*- coding: utf-8 -*-
# Module de gestion des routes pour les licences
# ---------------------------------------------
# Ce fichier contient toutes les routes FastAPI liées à la gestion des licences.
# Il gère l'affichage des pages web (dashboard, détails, création)
# et les points d'API pour les actions (créer, désactiver, etc.).

from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import os
import datetime

# Import du module Supabase au lieu de PostgreSQL
from app.services.supabase_licences import (
    add_license, get_license_info, validate_license, deactivate_license,
    reactivate_license, extend_license,
    get_all_licenses, update_license_usage, format_license_key,
    get_license_status_text, days_until_expiration, setup_supabase_config
)

# Configuration des templates
templates = Jinja2Templates(directory="app/templates")

# Création du router
router = APIRouter(prefix="/licenses", tags=["Licences"])

# ============================================================================
# ROUTES WEB (RENDU DE PAGES HTML)
# ============================================================================

@router.get("/dashboard", response_class=HTMLResponse)
async def license_dashboard(request: Request):
    """
    Affiche le tableau de bord principal avec la liste de toutes les licences.

    Args:
        request (Request): L'objet requête de FastAPI, nécessaire pour le template.

    Returns:
        HTMLResponse: La page HTML du tableau de bord rendue par Jinja2.
    """
    try:
        # Récupérer toutes les licences
        licenses = get_all_licenses()
        
        # Préparer les données pour l'affichage
        for license_info in licenses:
            license_info['status_text'] = get_license_status_text(license_info)
            license_info['days_until_expiration'] = days_until_expiration(license_info)
            license_info['formatted_key'] = format_license_key(license_info['license_key'])
            if isinstance(license_info['expires_at'], str):
                license_info['expires_at'] = datetime.datetime.fromisoformat(license_info['expires_at'].replace('Z', '+00:00'))

        now_utc = datetime.datetime.now(datetime.timezone.utc)

        return templates.TemplateResponse("license_dashboard.html", {
            "request": request,
            "licenses": licenses,
            "total_licenses": len(licenses),
            "active_licenses": len([l for l in licenses if l['is_active']]),
            "expired_licenses": len([l for l in licenses if not l['is_active'] or (l['expires_at'] and l['expires_at'] < now_utc)])
        })
        
    except Exception as e:
        return templates.TemplateResponse("license_dashboard.html", {
            "request": request,
            "licenses": [],
            "error": f"Erreur lors du chargement des licences: {str(e)}"
        })

@router.get("/details/{license_key}", response_class=HTMLResponse)
async def license_details(request: Request, license_key: str):
    """
    Affiche la page de détails pour une licence spécifique.

    Args:
        request (Request): L'objet requête de FastAPI.
        license_key (str): La clé de la licence à afficher.

    Returns:
        HTMLResponse: La page de détails de la licence.
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

@router.get("/create", response_class=HTMLResponse)
async def show_create_license_form(request: Request):
    """
    Affiche le formulaire de création d'une nouvelle licence.

    Args:
        request (Request): L'objet requête de FastAPI.

    Returns:
        HTMLResponse: La page HTML contenant le formulaire.
    """
    return templates.TemplateResponse("create_license.html", {"request": request})

# ============================================================================
# POINTS D'API (ACTIONS)
# ============================================================================

@router.post("/create", status_code=status.HTTP_302_FOUND)
async def create_license_action(
    client_name: str = Form(...),
    client_email: str = Form(...),
    company_name: str = Form(None),
    duration_days: int = Form(365),
    max_usage: int = Form(-1),
    notes: str = Form(None)
):
    """
    Traite la soumission du formulaire de création de licence.
    Crée la licence via le service, puis redirige vers le tableau de bord.

    Args:
        (divers): Données reçues du formulaire HTML.

    Returns:
        RedirectResponse: Redirige l'utilisateur vers le tableau de bord.
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

@router.post("/deactivate/{license_key}", status_code=status.HTTP_302_FOUND)
async def deactivate_license_action(license_key: str):
    """
    Désactive une licence spécifique.
    Appelée via un formulaire POST depuis la page de détails.

    Args:
        license_key (str): La clé de la licence à désactiver.

    Returns:
        RedirectResponse: Redirige vers la page de détails de la licence mise à jour.
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

@router.post("/reactivate/{license_key}", status_code=status.HTTP_302_FOUND)
async def reactivate_license_action(license_key: str):
    """
    Réactive une licence qui était désactivée.
    Appelée via un formulaire POST.

    Args:
        license_key (str): La clé de la licence à réactiver.

    Returns:
        RedirectResponse: Redirige vers la page de détails de la licence.
    """
    try:
        success = reactivate_license(license_key)
        
        if success:
            return RedirectResponse(url=f"/licenses/{license_key}", status_code=303)
        else:
            raise HTTPException(status_code=400, detail="Erreur lors de la réactivation")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@router.post("/extend/{license_key}", status_code=status.HTTP_302_FOUND)
async def extend_license_action(license_key: str, days_to_add: int = Form(...)):
    """
    Prolonge la date d'expiration d'une licence.
    Les données sont reçues d'un formulaire (souvent une modale).

    Args:
        license_key (str): La clé de la licence à prolonger.
        days_to_add (int): Le nombre de jours à ajouter à la date d'expiration.

    Returns:
        RedirectResponse: Redirige vers la page de détails de la licence.
    """
    try:
        # Conversion manuelle en entier
        try:
            num_days = int(days_to_add)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"La valeur '{days_to_add}' n'est pas un nombre de jours valide.")

        success = extend_license(license_key, num_days)
        
        if success:
            return RedirectResponse(url=f"/licenses/{license_key}?message=Licence prolongée avec succès de {num_days} jours.", status_code=303)
        else:
            raise HTTPException(status_code=400, detail="Erreur lors de la prolongation")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

# ============================================================================
# POINT D'API DE VALIDATION (POUR USAGE EXTERNE)
# ============================================================================

@router.post("/validate")
async def validate_license_api(request: Request):
    """
    Point d'API pour la validation d'une clé de licence par un programme externe.
    Attend un JSON contenant la 'license_key'.

    Args:
        request (Request): La requête FastAPI, pour lire le corps JSON.

    Returns:
        JSONResponse: Un objet JSON avec le statut de validation.
    """
    try:
        # Lit le corps de la requête en tant que JSON.
        data = await request.json()
        license_key = data.get('license_key')
        
        if not license_key:
            return JSONResponse(status_code=400, content={"error": "Clé de licence manquante"})
            
        # Valide la clé via le service.
        is_valid, message = validate_license(license_key)
        
        if is_valid:
            # Si valide, met à jour le compteur d'utilisation.
            update_license_usage(license_key)
            return JSONResponse(content={"status": "valid", "message": message})
        else:
            # Si invalide, retourne le message d'erreur approprié.
            return JSONResponse(status_code=403, content={"status": "invalid", "message": message})
            
    except Exception as e:
        # Gère les erreurs de parsing JSON ou autres problèmes.
        return JSONResponse(status_code=500, content={"error": f"Erreur interne: {e}"})

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