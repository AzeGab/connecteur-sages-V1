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
import logging
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import pypyodbc  # pour PyInstaller
import os
import sys
from dotenv import load_dotenv
from app.utils.console import install_console_colors

from app.routes import form_routes
from app.utils.paths import templates_path, static_path
from app.middleware.license_middleware import LicenseMiddleware

# ============================================================================
# CONFIGURATION DE L'APPLICATION
# ============================================================================
# Charger les variables d'environnement
load_dotenv()
install_console_colors()

# Création de l'instance FastAPI
app = FastAPI(
    title="Connecteur Sages",
    description="Service pour le connecteur Sages.",
    version="1.0.0"
)

# Ajout du middleware de session
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "change-me"),  # À définir en production
    session_cookie="connecteur_session"
)

# Ajout du middleware de vérification de licence
app.add_middleware(LicenseMiddleware)

# Enregistrement des fichiers statiques
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Configuration du moteur de templates Jinja2
# (Chemin compatible PyInstaller via utils.paths)
templates = Jinja2Templates(directory=templates_path)

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
    try:
        webbrowser.open("http://127.0.0.1:8000")
    except Exception:
        pass

# Inclusion des routes définies dans form_routes
app.include_router(form_routes.router)

# La route racine est définie dans les routeurs inclus (voir form_routes)

# Ce bloc permet d'exécuter l'application directement avec 'python app/main.py'.
# Utile pour le développement local.
if __name__ == "__main__":
    is_frozen = getattr(sys, "frozen", False)

    # Configuration logging compatible exécutable (pas de TTY)
    log_config = None
    if is_frozen:
        base_dir = os.path.dirname(sys.executable)
        log_file = os.path.join(base_dir, "connecteur.log")
        log_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s %(levelname)s %(name)s: %(message)s"
                }
            },
            "handlers": {
                "file": {
                    "class": "logging.FileHandler",
                    "formatter": "default",
                    "filename": log_file,
                    "mode": "a",
                    "encoding": "utf-8"
                }
            },
            "loggers": {
                "uvicorn": {"handlers": ["file"], "level": "INFO"},
                "uvicorn.error": {"handlers": ["file"], "level": "INFO", "propagate": True},
                "uvicorn.access": {"handlers": ["file"], "level": "INFO", "propagate": False},
            },
        }

    # Ouvrir le navigateur seulement en dev
    if not is_frozen:
        threading.Timer(1.0, open_browser).start()

    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=not is_frozen,
        log_config=log_config,
    )
