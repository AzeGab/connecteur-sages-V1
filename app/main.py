# Application principale du Connecteur SAGES
# Ce fichier initialise l'application FastAPI et configure les routes,
# les fichiers statiques et les templates.
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

from app.routes import form_routes, license_routes
from app.utils.paths import templates_path, static_path
from app.utils.templates_engine import templates

# Import du middleware de licences
from app.middleware.license_middleware import add_license_middleware

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
    title="Connecteur Groupe-SAGES",
    description="Application de connexion et de synchronisation entre ERP",
    version="1.0.0",
    debug=True
)

# Ajout du middleware de session
app.add_middleware(
    SessionMiddleware,
    secret_key="votre_cle_secrete_ici",  # À changer en production
    session_cookie="connecteur_session"
)

# Ajout du middleware de validation des licences
# Commenté par défaut pour permettre l'accès à l'interface de gestion
# Décommentez pour activer la validation des licences
# add_license_middleware(app)

# Enregistrement des fichiers statiques
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Enregistrement des templates Jinja2

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

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
        "features": ["licenses", "forms", "middleware"]
    }

# Fonction pour lancer le navigateur
def open_browser():
    webbrowser.open("http://127.0.0.1:8000")

# Inclusion des routes définies dans form_routes
app.include_router(form_routes.router)

# Inclusion des routes de licences
app.include_router(license_routes.router)

if __name__ == "__main__":
    threading.Timer(1.0, open_browser).start()  # Lance le navigateur après 1 seconde
    uvicorn.run(app, host="127.0.0.1", port=8000, log_config=None)
