# -*- coding: utf-8 -*-
# Point d'entrée principal de l'application FastAPI
# --------------------------------------------------
# Ce fichier est responsable de :
# 1. Créer l'instance principale de l'application FastAPI.
# 2. Monter le répertoire 'static' pour servir les fichiers CSS, JS et images.
# 3. Inclure les routeurs des différentes sections de l'application (licences, formulaires).
# 4. Définir une route racine pour la redirection initiale.

import webbrowser
import threading
import uvicorn
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import pypyodbc  # pour PyInstaller
import os
import sys
from dotenv import load_dotenv

from app.routes import form_routes
from app.utils.paths import templates_path, static_path
from app.utils.templates_engine import templates
from app.middleware.license_middleware import LicenseMiddleware

# ============================================================================
# CONFIGURATION DE L'APPLICATION
# ============================================================================
# Détection du mode d'exécution (PyInstaller ou dev)
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
    templates_path = os.path.join(BASE_DIR, "templates")
    static_path = os.path.join(BASE_DIR, "static")
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    templates_path = os.path.join(BASE_DIR, "templates")
    static_path = os.path.join(BASE_DIR, "static")

# Création de l'instance FastAPI
app = FastAPI(
    title="Connecteur Sages",
    description="Service pour le connecteur Sages.",
    version="1.0.0"
)

# Ajout du middleware de session
app.add_middleware(
    SessionMiddleware,
    secret_key="votre_cle_secrete_ici",  # À changer en production
    session_cookie="connecteur_session"
)

# Ajout du middleware de vérification de licence
app.add_middleware(LicenseMiddleware)

# Enregistrement des fichiers statiques
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configuration du moteur de templates Jinja2
# (Les templates sont dans app/templates)
templates = Jinja2Templates(directory="app/templates")

# Route de santé pour vérifier que l'application fonctionne
@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "Connecteur SAGES opérationnel"}

# Route d'API de santé
@app.get("/api/health")
def api_health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "database": "supabase",
        "features": ["forms"]
    }

# Fonction pour lancer le navigateur
def open_browser():
    webbrowser.open("http://127.0.0.1:8000")

# Inclusion des routes définies dans form_routes
app.include_router(form_routes.router)

# Redirection de la racine vers le formulaire de configuration
@app.get("/", include_in_schema=False)
async def root(request: Request):
    return RedirectResponse(url="/form")

# Ce bloc permet d'exécuter l'application directement avec 'python app/main.py'.
# Utile pour le développement local.
if __name__ == "__main__":
    threading.Timer(1.0, open_browser).start()  # Lance le navigateur après 1 seconde
    uvicorn.run("app.main:app", host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", 8000)), reload=True)
