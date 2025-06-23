# Middleware de validation des licences
# Ce fichier contient le middleware pour valider les licences à chaque requête

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import re
from typing import List, Optional

# Import du module Supabase
from app.services.supabase_licences import validate_license, update_license_usage

# ============================================================================
# CONFIGURATION
# ============================================================================

# Chemins exclus de la validation des licences
EXCLUDED_PATHS = [
    "/licenses",  # Interface de gestion des licences
    "/licenses/",  # Tableau de bord des licences
    "/licenses/create",  # Création de licence
    "/licenses/setup",  # Configuration Supabase
    "/static",  # Fichiers statiques
    "/docs",  # Documentation FastAPI
    "/openapi.json",  # Schéma OpenAPI
    "/favicon.ico",  # Favicon
    "/",  # Page d'accueil
    "/health",  # Endpoint de santé
    "/api/health",  # API de santé
]

# Noms de paramètres et headers pour la clé de licence
LICENSE_PARAM_NAMES = ["license_key", "license", "key", "api_key"]
LICENSE_HEADER_NAMES = ["X-License-Key", "X-API-Key", "Authorization"]

# ============================================================================
# MIDDLEWARE DE VALIDATION DES LICENCES
# ============================================================================

class LicenseMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour valider les licences à chaque requête.
    """
    
    def __init__(self, app, excluded_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or EXCLUDED_PATHS
    
    async def dispatch(self, request: Request, call_next):
        """
        Traite chaque requête et valide la licence si nécessaire.
        """
        # Vérifier si le chemin est exclu
        if self._is_path_excluded(request.url.path):
            return await call_next(request)
        
        # Extraire la clé de licence
        license_key = self._extract_license_key(request)
        
        if not license_key:
            return self._create_license_required_response()
        
        # Valider la licence
        is_valid, message = validate_license(license_key)
        
        if not is_valid:
            return self._create_invalid_license_response(message)
        
        # Mettre à jour les statistiques d'utilisation
        update_license_usage(license_key)
        
        # Continuer le traitement de la requête
        response = await call_next(request)
        return response
    
    def _is_path_excluded(self, path: str) -> bool:
        """
        Vérifie si un chemin est exclu de la validation des licences.
        
        Args:
            path (str): Chemin de la requête
            
        Returns:
            bool: True si le chemin est exclu
        """
        # Vérifier les correspondances exactes
        if path in self.excluded_paths:
            return True
        
        # Vérifier les correspondances avec wildcard
        for excluded_path in self.excluded_paths:
            if excluded_path.endswith("*"):
                pattern = excluded_path[:-1] + ".*"
                if re.match(pattern, path):
                    return True
            elif path.startswith(excluded_path):
                return True
        
        return False
    
    def _extract_license_key(self, request: Request) -> Optional[str]:
        """
        Extrait la clé de licence de la requête.
        
        Args:
            request (Request): Requête FastAPI
            
        Returns:
            str: Clé de licence ou None si non trouvée
        """
        # Vérifier les paramètres de requête
        for param_name in LICENSE_PARAM_NAMES:
            if param_name in request.query_params:
                license_key = request.query_params[param_name]
                if license_key and license_key.strip():
                    return license_key.strip()
        
        # Vérifier les headers
        for header_name in LICENSE_HEADER_NAMES:
            if header_name in request.headers:
                license_key = request.headers[header_name]
                if license_key and license_key.strip():
                    # Gérer le cas où Authorization contient "Bearer "
                    if header_name == "Authorization" and license_key.startswith("Bearer "):
                        license_key = license_key[7:]
                    return license_key.strip()
        
        # Vérifier les cookies
        if "license_key" in request.cookies:
            license_key = request.cookies["license_key"]
            if license_key and license_key.strip():
                return license_key.strip()
        
        return None
    
    def _create_license_required_response(self) -> JSONResponse:
        """
        Crée une réponse d'erreur pour licence manquante.
        
        Returns:
            JSONResponse: Réponse d'erreur
        """
        return JSONResponse(
            status_code=401,
            content={
                "error": "license_required",
                "message": "Une clé de licence est requise pour accéder à cette ressource",
                "details": {
                    "methods": [
                        "Ajouter la clé dans les paramètres de requête: ?license_key=VOTRE_CLE",
                        "Ajouter la clé dans les headers: X-License-Key: VOTRE_CLE",
                        "Ajouter la clé dans les cookies: license_key=VOTRE_CLE"
                    ]
                }
            }
        )
    
    def _create_invalid_license_response(self, message: str) -> JSONResponse:
        """
        Crée une réponse d'erreur pour licence invalide.
        
        Args:
            message (str): Message d'erreur
            
        Returns:
            JSONResponse: Réponse d'erreur
        """
        return JSONResponse(
            status_code=403,
            content={
                "error": "invalid_license",
                "message": message,
                "details": {
                    "possible_reasons": [
                        "La clé de licence n'existe pas",
                        "La licence a expiré",
                        "La licence a été désactivée",
                        "La limite d'utilisation a été atteinte"
                    ]
                }
            }
        )

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def add_license_middleware(app, excluded_paths: Optional[List[str]] = None):
    """
    Ajoute le middleware de validation des licences à l'application FastAPI.
    
    Args:
        app: Application FastAPI
        excluded_paths (list): Liste des chemins exclus (optionnel)
    """
    app.add_middleware(LicenseMiddleware, excluded_paths=excluded_paths)
    print("✅ Middleware de validation des licences ajouté")

def validate_license_in_request(request: Request) -> tuple[bool, str, Optional[str]]:
    """
    Valide une licence dans une requête (fonction utilitaire).
    
    Args:
        request (Request): Requête FastAPI
        
    Returns:
        tuple: (is_valid, message, license_key)
    """
    # Extraire la clé de licence
    license_key = None
    
    # Vérifier les paramètres de requête
    for param_name in LICENSE_PARAM_NAMES:
        if param_name in request.query_params:
            license_key = request.query_params[param_name]
            break
    
    # Vérifier les headers
    if not license_key:
        for header_name in LICENSE_HEADER_NAMES:
            if header_name in request.headers:
                license_key = request.headers[header_name]
                if header_name == "Authorization" and license_key.startswith("Bearer "):
                    license_key = license_key[7:]
                break
    
    # Vérifier les cookies
    if not license_key and "license_key" in request.cookies:
        license_key = request.cookies["license_key"]
    
    if not license_key:
        return False, "Clé de licence manquante", None
    
    # Valider la licence
    is_valid, message = validate_license(license_key)
    
    if is_valid:
        # Mettre à jour les statistiques d'utilisation
        update_license_usage(license_key)
    
    return is_valid, message, license_key

# Fonction utilitaire pour valider une licence depuis n'importe où dans l'application
def validate_license_for_request(license_key: str) -> tuple[bool, str, dict]:
    """
    Valide une licence et retourne les informations associées.
    
    Returns:
        tuple: (is_valid, message, license_info)
    """
    try:
        # Valider la licence
        is_valid, message = validate_license(license_key)
        
        # Récupérer les informations de la licence
        license_info = None
        if is_valid:
            license_info = get_license_info(conn, license_key)
            # Mettre à jour les statistiques d'utilisation
            update_license_usage(license_key)
        
        return is_valid, message, license_info
        
    except Exception as e:
        return False, f"Erreur lors de la validation: {str(e)}", None

# Décorateur pour protéger une route spécifique
def require_valid_license(func):
    """
    Décorateur pour exiger une licence valide sur une route spécifique.
    """
    async def wrapper(*args, **kwargs):
        # Cette fonction devrait être implémentée selon vos besoins
        # Elle peut être utilisée pour protéger des routes spécifiques
        # sans activer le middleware global
        pass
    return wrapper 