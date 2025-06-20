# Middleware de validation des licences
# Ce fichier contient le middleware pour valider les licences à chaque requête

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.services.licences import validate_license, get_license_info
from app.services.connex import connect_to_postgres, load_credentials
import json

class LicenseMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour valider les licences à chaque requête.
    """
    
    def __init__(self, app, exclude_paths=None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/",
            "/licenses/",
            "/licenses/create",
            "/licenses/api/",
            "/static/",
            "/docs",
            "/openapi.json",
            "/favicon.ico"
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Vérifier si le chemin est exclu de la validation
        if self._is_path_excluded(request.url.path):
            return await call_next(request)
        
        # Récupérer la clé de licence depuis les headers ou les cookies
        license_key = self._get_license_key(request)
        
        if not license_key:
            return self._create_license_required_response()
        
        # Valider la licence
        is_valid, message = await self._validate_license(license_key)
        
        if not is_valid:
            return self._create_invalid_license_response(message)
        
        # Licence valide, continuer
        response = await call_next(request)
        return response
    
    def _is_path_excluded(self, path: str) -> bool:
        """
        Vérifie si le chemin est exclu de la validation des licences.
        """
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return True
        return False
    
    def _get_license_key(self, request: Request) -> str:
        """
        Récupère la clé de licence depuis les headers ou les cookies.
        """
        # Vérifier dans les headers
        license_key = request.headers.get("X-License-Key")
        if license_key:
            return license_key
        
        # Vérifier dans les cookies
        license_key = request.cookies.get("license_key")
        if license_key:
            return license_key
        
        # Vérifier dans les paramètres de requête (pour les tests)
        license_key = request.query_params.get("license_key")
        if license_key:
            return license_key
        
        return None
    
    async def _validate_license(self, license_key: str) -> tuple[bool, str]:
        """
        Valide une licence de manière asynchrone.
        """
        try:
            # Charger les identifiants PostgreSQL
            creds = load_credentials()
            if not creds or 'postgresql' not in creds:
                return False, "Configuration PostgreSQL manquante"
            
            pg_creds = creds['postgresql']
            conn = connect_to_postgres(
                pg_creds['host'],
                pg_creds['user'],
                pg_creds['password'],
                pg_creds['database'],
                pg_creds.get('port', '5432')
            )
            
            if not conn:
                return False, "Impossible de se connecter à la base de données"
            
            # Valider la licence
            is_valid, message = validate_license(conn, license_key)
            
            if is_valid:
                # Mettre à jour les statistiques d'utilisation
                from app.services.licences import update_license_usage
                update_license_usage(conn, license_key)
            
            conn.close()
            return is_valid, message
            
        except Exception as e:
            return False, f"Erreur lors de la validation: {str(e)}"
    
    def _create_license_required_response(self) -> Response:
        """
        Crée une réponse indiquant qu'une licence est requise.
        """
        error_data = {
            "error": "license_required",
            "message": "Une clé de licence est requise pour accéder à cette ressource",
            "details": {
                "how_to_provide": [
                    "Ajouter l'en-tête HTTP: X-License-Key: YOUR_LICENSE_KEY",
                    "Ajouter un cookie: license_key=YOUR_LICENSE_KEY",
                    "Ajouter un paramètre de requête: ?license_key=YOUR_LICENSE_KEY"
                ]
            }
        }
        
        return Response(
            content=json.dumps(error_data, indent=2),
            status_code=401,
            media_type="application/json",
            headers={
                "WWW-Authenticate": "License",
                "Content-Type": "application/json"
            }
        )
    
    def _create_invalid_license_response(self, message: str) -> Response:
        """
        Crée une réponse indiquant que la licence est invalide.
        """
        error_data = {
            "error": "invalid_license",
            "message": message,
            "details": {
                "possible_reasons": [
                    "Licence expirée",
                    "Licence désactivée",
                    "Limite d'utilisation atteinte",
                    "Format de clé invalide"
                ]
            }
        }
        
        return Response(
            content=json.dumps(error_data, indent=2),
            status_code=403,
            media_type="application/json",
            headers={"Content-Type": "application/json"}
        )

# Fonction utilitaire pour valider une licence depuis n'importe où dans l'application
def validate_license_for_request(license_key: str) -> tuple[bool, str, dict]:
    """
    Valide une licence et retourne les informations associées.
    
    Returns:
        tuple: (is_valid, message, license_info)
    """
    try:
        creds = load_credentials()
        if not creds or 'postgresql' not in creds:
            return False, "Configuration PostgreSQL manquante", None
        
        pg_creds = creds['postgresql']
        conn = connect_to_postgres(
            pg_creds['host'],
            pg_creds['user'],
            pg_creds['password'],
            pg_creds['database'],
            pg_creds.get('port', '5432')
        )
        
        if not conn:
            return False, "Impossible de se connecter à la base de données", None
        
        # Valider la licence
        is_valid, message = validate_license(conn, license_key)
        
        # Récupérer les informations de la licence
        license_info = None
        if is_valid:
            license_info = get_license_info(conn, license_key)
            # Mettre à jour les statistiques d'utilisation
            from app.services.licences import update_license_usage
            update_license_usage(conn, license_key)
        
        conn.close()
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