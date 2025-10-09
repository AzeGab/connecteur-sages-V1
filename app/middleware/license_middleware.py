# Middleware de vérification de licence
# Ce fichier contient le middleware pour vérifier la validité de la licence

from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.license import is_license_valid, refresh_license_validation, load_license_info
from app.utils.paths import templates_path
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory=templates_path)

class LicenseMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour vérifier la validité de la licence.
    Redirige vers la page de licence expirée si la licence n'est pas valide.
    """
    
    def __init__(self, app):
        super().__init__(app)
        # Routes qui nécessitent une licence valide
        self.protected_routes = [
            "/",
            "/transfer",
            "/transfer-batisimply",
            "/recup-heures",
            "/update-code-projet",
            "/transfer-heure-batigest",
            "/sync-batigest-to-batisimply",
            "/sync-batisimply-to-batigest"
        ]
        
        # Routes qui ne nécessitent pas de licence
        self.excluded_routes = [
            "/login",
            "/configuration",
            "/static",
            "/favicon.ico",
            "/license-expired",
            "/update-license",
            "/refresh-license"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """
        Vérifie la licence avant de traiter la requête.
        
        Args:
            request (Request): Requête FastAPI
            call_next: Fonction pour continuer le traitement
            
        Returns:
            Response: Réponse HTTP
        """
        path = request.url.path
        
        # Vérifier si la route est exclue de la vérification de licence
        if any(path.startswith(excluded) for excluded in self.excluded_routes):
            return await call_next(request)
        
        # Vérifier si la route nécessite une licence valide
        if any(path == protected for protected in self.protected_routes):
            # Vérifier d'abord la licence locale
            if not is_license_valid():
                # Si la licence locale n'est pas valide, essayer de la rafraîchir
                license_info = load_license_info()
                if license_info and license_info.get("key"):
                    # Tenter de rafraîchir la validation avec la clé locale
                    is_valid, _ = refresh_license_validation(license_info.get("key"))
                    if not is_valid:
                        # Afficher directement la page license_expired.html avec les infos de la licence
                        return templates.TemplateResponse(
                            "license_expired.html",
                            {
                                "request": request,
                                "license_expiry_date": license_info.get("expires_at"),
                                "client_name": license_info.get("client_name"),
                                "license_key": license_info.get("key")
                            },
                            status_code=403
                        )
                else:
                    # Pas de licence locale, rediriger vers la configuration
                    return RedirectResponse(url="/configuration", status_code=303)
        
        return await call_next(request) 