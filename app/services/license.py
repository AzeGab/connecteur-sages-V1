# Module de gestion des licences
# Ce fichier contient les fonctions nécessaires pour valider et gérer les licences
# La validation se fait via l'API Supabase pour des raisons de sécurité

import json
import os
import requests
from datetime import datetime
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Chemin du fichier stockant les identifiants de connexion
CREDENTIALS_FILE = "app/services/credentials.json"

# Configuration Supabase
SUPABASE_URL = "https://rxqveiaawggfyeukpvyz.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ4cXZlaWFhd2dnZnlldWtwdnl6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA2NjQzMjAsImV4cCI6MjA2NjI0MDMyMH0.vYrxDe41M_a8XDcbHwmaiVfy8rKMsyNroiHvNHq5FAM")

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
    
    print(f"🔍 Validation de la clé: {license_key[:8]}...")
    
    try:
        # Appel à l'API Supabase
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        
        # Requête à la table licenses avec filtre sur license_key
        url = f"{SUPABASE_URL}/rest/v1/licenses?license_key=eq.{license_key}"
        print(f"🌐 URL de requête: {url}")
        
        response = requests.get(
            url,
            headers=headers,
            timeout=10  # Timeout de 10 secondes
        )
        
        print(f"📡 Statut de la réponse: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Données reçues: {len(data)} licences trouvées")
            
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
        with open(CREDENTIALS_FILE, "r") as f:
            creds = json.load(f)
    
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
    
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(creds, f, indent=2)

def load_license_info() -> Optional[Dict]:
    """
    Charge les informations de licence depuis le fichier de configuration.
    
    Returns:
        Optional[Dict]: Informations de licence ou None si pas de licence
    """
    if not os.path.exists(CREDENTIALS_FILE):
        return None
    
    with open(CREDENTIALS_FILE, "r") as f:
        creds = json.load(f)
    
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
    expiry_date = license_info.get("expiry_date")
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