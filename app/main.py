# Application principale du Connecteur SAGES
# Ce fichier initialise l'application FastAPI et configure les routes,
# les fichiers statiques et les templates.

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routes import form_routes

# ============================================================================
# CONFIGURATION DE L'APPLICATION
# ============================================================================

# Création de l'instance FastAPI
app = FastAPI(
    title="Connecteur SAGES",
    description="Application de connexion et de synchronisation avec les bases de données SAGES",
    version="1.0.0"
)

# ============================================================================
# CONFIGURATION DES RESSOURCES STATIQUES
# ============================================================================

# Configuration des fichiers statiques (CSS, JS, images)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configuration du moteur de templates Jinja2
templates = Jinja2Templates(directory="app/templates")

# ============================================================================
# INCLUSION DES ROUTES
# ============================================================================

# Inclusion des routes définies dans form_routes
app.include_router(form_routes.router)
