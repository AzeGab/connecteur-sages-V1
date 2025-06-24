# -*- coding: utf-8 -*-
"""
Utilitaire pour initialiser le moteur de templates Jinja2
Permet d'utiliser les templates HTML dans FastAPI avec des filtres personnalisés si besoin.
"""
from fastapi.templating import Jinja2Templates

# Initialisation du moteur de templates sur le dossier app/templates
templates = Jinja2Templates(directory="app/templates")

def get_templates():
    """
    Retourne l'instance du moteur de templates Jinja2.
    Utile pour l'injection de dépendance dans les routes.
    """
    return templates 