# Module de gestion des licences
# Ce fichier contient les fonctions nécessaires pour valider et gérer les licences
# La validation se fait via l'API Supabase pour des raisons de sécurité

import json
import os
import requests
import uuid
import platform
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Chemin du fichier stockant les identifiants de connexion
CREDENTIALS_FILE = "app/services/credentials.json"

# Configuration Supabase (via variables d'environnement)
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://rxqveiaawggfyeukpvyz.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Configuration Licence Manager API (service centralisé)
LICENSE_API_BASE_URL = os.getenv("LICENSE_API_BASE_URL")  # ex: http://127.0.0.1:3000
LICENSE_API_KEY = os.getenv("LICENSE_API_KEY")
LICENSE_HEARTBEAT_ENABLED = os.getenv("LICENSE_HEARTBEAT_ENABLED", "false").lower() == "true"
LICENSE_HEARTBEAT_INTERVAL_SECONDS = int(os.getenv("LICENSE_HEARTBEAT_INTERVAL_SECONDS", "300"))
LICENSE_CLIENT_ID = os.getenv("LICENSE_CLIENT_ID", "connecteur-sages-client")
LICENSE_CLIENT_VERSION = os.getenv("LICENSE_CLIENT_VERSION", "1.0.0")
LICENSE_MACHINE_ID = os.getenv("LICENSE_MACHINE_ID")

def _get_machine_id() -> str:
    if LICENSE_MACHINE_ID:
        return LICENSE_MACHINE_ID
    try:
        # Combine hostname and MAC for a stable identifier
        mac = uuid.getnode()
        host = platform.node() or "unknown-host"
        return f"{host}-{mac}"
    except Exception:
        return "unknown-machine"


def _license_api_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {LICENSE_API_KEY}",
        "Content-Type": "application/json"
    }


def _validate_via_license_service(license_key: str) -> Tuple[bool, Optional[Dict]]:
    """
    Valide la licence via le service central (licence-manager) si configuré.
    """
    if not LICENSE_API_BASE_URL or not LICENSE_API_KEY:
        return False, None

    try:
        url = f"{LICENSE_API_BASE_URL.rstrip('/')}/api/v1/validate"
        payload = {
            "license_key": license_key,
            "client_id": LICENSE_CLIENT_ID,
            "client_version": LICENSE_CLIENT_VERSION,
            "machine_id": _get_machine_id()
        }
        resp = requests.post(url, headers=_license_api_headers(), json=payload, timeout=10)
        if resp.status_code != 200:
            return False, None

        data = resp.json()
        # data structure expected from API_DOCUMENTATION.md
        if data.get("valid"):
            license_info = data.get("license_info", {}) or {}
            # Normaliser le format pour stockage local
            normalized = {
                "key": license_key,
                "client_name": license_info.get("client_name"),
                "client_email": license_info.get("client_email"),
                "company_name": license_info.get("company_name"),
                "expiry_date": license_info.get("expires_at"),
                "features": ["chantier", "devis", "heures"],
                "updated_at": datetime.now().isoformat(),
                "valid": True,
                "usage_count": data.get("usage_count", 0),
                "max_usage": data.get("max_usage"),
                "is_active": license_info.get("is_active", False)
            }
            # Sauvegarder localement
            save_license_info(license_key, normalized)
            return True, normalized
        else:
            return False, None
    except Exception:
        return False, None


def send_license_heartbeat(license_key: str) -> bool:
    """
    Envoie un heartbeat au service central si activé et configuré.
    """
    if not LICENSE_HEARTBEAT_ENABLED or not LICENSE_API_BASE_URL or not LICENSE_API_KEY:
        return False
    try:
        url = f"{LICENSE_API_BASE_URL.rstrip('/')}/api/v1/heartbeat/{license_key}"
        resp = requests.post(url, headers=_license_api_headers(), timeout=8)
        return resp.status_code == 200
    except Exception:
        return False


def validate_license_key(license_key: str) -> Tuple[bool, Optional[Dict]]:
    """
    Valide une clé de licence via l'API Supabase.
    
    Args:
        license_key (str): Clé de licence à valider
        
    Returns:
        Tuple[bool, Optional[Dict]]: (est_valide, informations_licence)
    """
    if not license_key:
        print("❌ Clé de licence vide")
        return False, None
    
    # Nettoyage
    license_key = license_key.strip()
    print(f"🔍 Validation de la clé: {license_key[:8]}...")

    # Mode test: super-clé 'Cobalt' (activé seulement si debug ou ALLOW_TEST_LICENSE=true)
    # Lire le flag debug directement depuis credentials.json pour éviter toute dépendance
    debug_mode = False
    try:
        if os.path.exists(CREDENTIALS_FILE) and os.path.getsize(CREDENTIALS_FILE) > 0:
            with open(CREDENTIALS_FILE, "r", encoding="utf-8-sig") as f:
                _creds = json.load(f)
                debug_mode = bool(_creds.get("debug", False))
    except Exception:
        debug_mode = False
    allow_test_env = os.getenv("ALLOW_TEST_LICENSE", "false").lower() == "true"
    if (debug_mode or allow_test_env) and license_key.lower() == "cobalt":
        print("🧪 Super-clé de test détectée (Cobalt) – licence acceptée en mode debug")
        far_future = (datetime.now() + timedelta(days=3650)).isoformat()
        test_license = {
            "client_id": "TEST-COBALT",
            "expires_at": far_future,
            "usage_count": 0,
            "max_usage": -1,
            "is_active": True,
            "is_archived": False
        }
        # Sauvegarder localement au format attendu
        save_license_info(license_key, test_license)
        return True, test_license
    
    try:
        # 1) Tenter via service central si configuré
        if LICENSE_API_BASE_URL and LICENSE_API_KEY:
            valid, info = _validate_via_license_service(license_key)
            if valid and info:
                # Heartbeat optionnel
                send_license_heartbeat(license_key)
                print("✅ Licence valide via service central")
                return True, info

        # 2) Fallback Supabase (ancien comportement)
        if not SUPABASE_KEY:
            print("❌ SUPABASE_KEY manquant. Définissez-le dans votre .env")
            return False, None
        # Appel à l'API Supabase
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        
        # Requête à la table licenses avec filtre et select explicite
        url = f"{SUPABASE_URL}/rest/v1/licenses"
        params = {
            "select": "*",
            "license_key": f"eq.{license_key.strip()}"
        }
        print(f"🌐 URL de requête: {url}")
        print(f"🔎 Paramètres: {params}")
        
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10  # Timeout de 10 secondes
        )
        
        print(f"📡 Statut de la réponse: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Données reçues: {len(data)} licences trouvées")
            try:
                print(f"📩 Content-Range: {response.headers.get('Content-Range')}")
            except Exception:
                pass
            
            # Vérifier si on a des résultats
            if data and len(data) > 0:
                license_info = data[0]  # Prendre le premier résultat
                print(f"📋 Licence trouvée: ID {license_info.get('id')}")
                
                # Vérifier si la licence est active
                is_active = license_info.get("is_active", False)
                print(f"✅ is_active: {is_active}")
                if not is_active:
                    print("❌ Licence inactive")
                    return False, license_info  # Licence inactive
                
                # Vérifier si la licence n'est pas expirée
                expires_at = license_info.get("expires_at")
                print(f"📅 expires_at: {expires_at}")
                if expires_at:
                    try:
                        # Gérer différents formats de date
                        if 'T' in expires_at:
                            expiry_datetime = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                        else:
                            expiry_datetime = datetime.strptime(expires_at, "%Y-%m-%d")
                        
                        now = datetime.now(expiry_datetime.tzinfo)
                        print(f"🕐 Maintenant: {now}")
                        print(f"🕐 Expire le: {expiry_datetime}")
                        
                        if now > expiry_datetime:
                            print("❌ Licence expirée")
                            return False, license_info  # Licence expirée
                        else:
                            print("✅ Licence non expirée")
                    except ValueError as e:
                        print(f"⚠️ Erreur de parsing de date: {e}")
                        # Si la date n'est pas valide, on considère la licence comme valide
                        pass
                
                # Vérifier l'usage count si applicable
                usage_count = license_info.get("usage_count", 0)
                max_usage = license_info.get("max_usage")
                print(f"📊 usage_count: {usage_count}, max_usage: {max_usage}")
                if max_usage and max_usage > 0 and usage_count >= max_usage:
                    print("❌ Limite d'usage atteinte")
                    return False, license_info  # Limite d'usage atteinte
                elif max_usage == -1:
                    print("✅ Usage illimité")
                else:
                    print("✅ Usage dans les limites")
                
                # Vérifier si la licence n'est pas archivée
                is_archived = license_info.get("is_archived", False)
                print(f"📦 is_archived: {is_archived}")
                if is_archived:
                    print("❌ Licence archivée")
                    return False, license_info  # Licence archivée
                
                print("✅ Licence valide")
                # Sauvegarder au format local attendu
                save_license_info(license_key, {
                    "key": license_key,
                    "client_name": f"Client {license_info.get('client_id', 'Inconnu')}",
                    "expiry_date": license_info.get("expires_at"),
                    "features": ["chantier", "devis", "heures"],
                    "updated_at": datetime.now().isoformat(),
                    "valid": True,
                    "usage_count": license_info.get("usage_count", 0),
                    "max_usage": license_info.get("max_usage"),
                    "is_active": license_info.get("is_active", False)
                })
                return True, license_info
            else:
                # Aucune licence trouvée
                print("❌ Aucune licence trouvée avec cette clé")
                return False, None
        else:
            # Erreur serveur
            print(f"❌ Erreur API Supabase: {response.status_code} - {response.text}")
            return False, None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion à Supabase: {e}")
        return False, None
    except json.JSONDecodeError as e:
        print(f"❌ Erreur de décodage de la réponse Supabase: {e}")
        return False, None
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False, None

def save_license_info(license_key: str, license_info: Dict) -> None:
    """
    Sauvegarde les informations de licence dans le fichier de configuration.
    
    Args:
        license_key (str): Clé de licence
        license_info (Dict): Informations de la licence
    """
    if not os.path.exists(CREDENTIALS_FILE):
        creds = {}
    else:
        # Lecture tolérante au BOM et aux fichiers vides
        try:
            if os.path.getsize(CREDENTIALS_FILE) == 0:
                creds = {}
            else:
                with open(CREDENTIALS_FILE, "r", encoding="utf-8-sig") as f:
                    creds = json.load(f)
        except json.JSONDecodeError:
            try:
                with open(CREDENTIALS_FILE, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().lstrip("\ufeff").strip()
                    creds = json.loads(content) if content else {}
            except Exception:
                creds = {}
    
    # Adapter les noms de colonnes pour correspondre à la structure locale
    creds["license"] = {
        "key": license_key,
        "client_name": f"Client {license_info.get('client_id', 'Inconnu')}",  # Utiliser client_id comme nom
        "expiry_date": license_info.get("expires_at"),  # Adapter expires_at vers expiry_date
        "features": ["chantier", "devis", "heures"],  # Fonctionnalités par défaut
        "updated_at": datetime.now().isoformat(),
        "valid": True,
        "usage_count": license_info.get("usage_count", 0),
        "max_usage": license_info.get("max_usage"),
        "is_active": license_info.get("is_active", False)
    }
    
    with open(CREDENTIALS_FILE, "w", encoding="utf-8") as f:
        json.dump(creds, f, indent=2, ensure_ascii=False, sort_keys=True)

def load_license_info() -> Optional[Dict]:
    """
    Charge les informations de licence depuis le fichier de configuration.
    
    Returns:
        Optional[Dict]: Informations de licence ou None si pas de licence
    """
    if not os.path.exists(CREDENTIALS_FILE):
        return None
    try:
        if os.path.getsize(CREDENTIALS_FILE) == 0:
            return None
        with open(CREDENTIALS_FILE, "r", encoding="utf-8-sig") as f:
            creds = json.load(f)
    except json.JSONDecodeError:
        try:
            with open(CREDENTIALS_FILE, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().lstrip("\ufeff").strip()
                if not content:
                    return None
                creds = json.loads(content)
        except Exception:
            return None
    
    return creds.get("license")

def is_license_valid() -> bool:
    """
    Vérifie si la licence actuelle est valide.
    Note: Cette fonction vérifie uniquement la licence locale.
    Pour une vérification en temps réel, utilisez validate_license_key().
    
    Returns:
        bool: True si la licence est valide, False sinon
    """
    license_info = load_license_info()
    if not license_info:
        return False
    
    license_key = license_info.get("key")
    if not license_key:
        return False
    
    # Vérifier si la licence est active
    is_active = license_info.get("is_active", False)
    if not is_active:
        return False
    
    # Vérification locale de l'expiration
    # Supporte les deux clés (compat rétro): expiry_date (préféré) ou expires_at
    expiry_date = license_info.get("expiry_date") or license_info.get("expires_at")
    if expiry_date:
        try:
            expiry_datetime = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
            if datetime.now(expiry_datetime.tzinfo) > expiry_datetime:
                return False
        except ValueError:
            # Si la date n'est pas valide, on considère la licence comme invalide
            return False
    
    return True

def get_license_expiry_date() -> Optional[str]:
    """
    Récupère la date d'expiration de la licence.
    
    Returns:
        Optional[str]: Date d'expiration au format YYYY-MM-DD ou None
    """
    license_info = load_license_info()
    if license_info:
        expiry_date = license_info.get("expiry_date")
        if expiry_date:
            # Convertir le format ISO en format date simple
            try:
                if 'T' in expiry_date:
                    dt = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
                    return dt.strftime("%Y-%m-%d")
                else:
                    return expiry_date
            except ValueError:
                return expiry_date
    return None

def get_client_name() -> Optional[str]:
    """
    Récupère le nom du client associé à la licence.
    
    Returns:
        Optional[str]: Nom du client ou None
    """
    license_info = load_license_info()
    if license_info:
        return license_info.get("client_name")
    return None

def has_feature(feature: str) -> bool:
    """
    Vérifie si la licence actuelle inclut une fonctionnalité spécifique.
    
    Args:
        feature (str): Nom de la fonctionnalité à vérifier
        
    Returns:
        bool: True si la fonctionnalité est disponible, False sinon
    """
    if not is_license_valid():
        return False
    
    license_info = load_license_info()
    if license_info:
        features = license_info.get("features", [])
        return feature in features
    
    return False

def refresh_license_validation(license_key: str) -> Tuple[bool, Optional[Dict]]:
    """
    Rafraîchit la validation de la licence en interrogeant l'API.
    Cette fonction est utile pour vérifier en temps réel si une licence
    a été révoquée ou modifiée.
    
    Args:
        license_key (str): Clé de licence à valider
        
    Returns:
        Tuple[bool, Optional[Dict]]: (est_valide, informations_licence)
    """
    is_valid, license_info = validate_license_key(license_key)
    
    if is_valid and license_info:
        # Mettre à jour les informations locales
        save_license_info(license_key, license_info)
    
    return is_valid, license_info 