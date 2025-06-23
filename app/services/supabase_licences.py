# Module de gestion des licences avec Supabase
# Ce fichier contient les fonctions nécessaires pour gérer les licences via Supabase

import hashlib
import datetime
import uuid
import json
import os
from typing import Optional, Dict, List, Tuple
import requests
from supabase import create_client, Client

# ============================================================================
# CONFIGURATION SUPABASE
# ============================================================================

# Configuration Supabase (à remplacer par vos vraies valeurs)
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your-anon-key")

# Clé secrète pour la génération des licences (à changer en production)
SECRET_KEY = "connecteur-sages-v1-secret-key-2024"

# Durée de validité par défaut des licences (en jours)
DEFAULT_LICENSE_DURATION = 365

# ============================================================================
# INITIALISATION SUPABASE
# ============================================================================

def get_supabase_client() -> Client:
    """
    Crée et retourne un client Supabase.
    
    Returns:
        Client: Client Supabase configuré
    """
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return supabase
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation du client Supabase: {e}")
        return None

# ============================================================================
# GÉNÉRATION ET VALIDATION DES LICENCES
# ============================================================================

def generate_license_key(client_name: str, client_email: str, duration_days: int = DEFAULT_LICENSE_DURATION) -> str:
    """
    Génère une clé de licence unique pour un client.
    
    Args:
        client_name (str): Nom du client
        client_email (str): Email du client
        duration_days (int): Durée de validité en jours
        
    Returns:
        str: Clé de licence générée
    """
    # Créer une chaîne unique basée sur les informations du client
    unique_string = f"{client_name}:{client_email}:{duration_days}:{SECRET_KEY}"
    
    # Générer un hash SHA-256
    hash_object = hashlib.sha256(unique_string.encode())
    hash_hex = hash_object.hexdigest()
    
    # Formater la clé en groupes de 4 caractères séparés par des tirets
    formatted_key = '-'.join([hash_hex[i:i+4] for i in range(0, 32, 4)])
    
    return formatted_key.upper()

def validate_license_key(license_key: str) -> bool:
    """
    Valide le format d'une clé de licence.
    
    Args:
        license_key (str): Clé de licence à valider
        
    Returns:
        bool: True si le format est valide, False sinon
    """
    if not license_key:
        return False
    
    # Supprimer les tirets et vérifier la longueur
    clean_key = license_key.replace('-', '').replace(' ', '')
    if len(clean_key) != 32:
        return False
    
    # Vérifier que tous les caractères sont hexadécimaux
    try:
        int(clean_key, 16)
        return True
    except ValueError:
        return False

# ============================================================================
# GESTION DE LA BASE DE DONNÉES SUPABASE
# ============================================================================

def create_licenses_table() -> bool:
    """
    Crée la table licenses dans Supabase si elle n'existe pas.
    Note: Cette fonction nécessite des privilèges d'administrateur dans Supabase.
    
    Returns:
        bool: True si la table a été créée avec succès
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        # SQL pour créer la table (à exécuter dans l'interface SQL de Supabase)
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS licenses (
            id BIGSERIAL PRIMARY KEY,
            license_key VARCHAR(255) UNIQUE NOT NULL,
            client_name VARCHAR(255) NOT NULL,
            client_email VARCHAR(255) NOT NULL,
            company_name VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            last_used TIMESTAMP WITH TIME ZONE,
            usage_count INTEGER DEFAULT 0,
            max_usage INTEGER DEFAULT -1,
            notes TEXT
        );
        
        -- Créer un index sur license_key pour les performances
        CREATE INDEX IF NOT EXISTS idx_licenses_license_key ON licenses(license_key);
        
        -- Créer un index sur is_active pour les requêtes de validation
        CREATE INDEX IF NOT EXISTS idx_licenses_is_active ON licenses(is_active);
        """
        
        print("📝 Veuillez exécuter le SQL suivant dans l'interface SQL de Supabase:")
        print(create_table_sql)
        print("✅ Table licenses créée avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de la table licenses: {e}")
        return False

def add_license(client_name: str, client_email: str, company_name: str = None, 
                duration_days: int = DEFAULT_LICENSE_DURATION, max_usage: int = -1, notes: str = None) -> Optional[str]:
    """
    Ajoute une nouvelle licence dans Supabase.
    
    Args:
        client_name (str): Nom du client
        client_email (str): Email du client
        company_name (str): Nom de l'entreprise (optionnel)
        duration_days (int): Durée de validité en jours
        max_usage (int): Nombre maximum d'utilisations (-1 pour illimité)
        notes (str): Notes additionnelles
        
    Returns:
        str: Clé de licence générée ou None en cas d'erreur
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return None
        
        # Générer la clé de licence
        license_key = generate_license_key(client_name, client_email, duration_days)
        
        # Calculer la date d'expiration
        expires_at = datetime.datetime.now() + datetime.timedelta(days=duration_days)
        
        # Préparer les données
        license_data = {
            'license_key': license_key,
            'client_name': client_name,
            'client_email': client_email,
            'company_name': company_name,
            'expires_at': expires_at.isoformat(),
            'max_usage': max_usage,
            'notes': notes
        }
        
        # Insérer dans Supabase
        result = supabase.table('licenses').insert(license_data).execute()
        
        if result.data:
            print(f"✅ Licence créée avec succès pour {client_name}")
            return license_key
        else:
            print("❌ Erreur lors de l'ajout de la licence")
            return None
        
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout de la licence: {e}")
        return None

def get_license_info(license_key: str) -> Optional[Dict]:
    """
    Récupère les informations d'une licence depuis Supabase.
    
    Args:
        license_key (str): Clé de licence
        
    Returns:
        dict: Informations de la licence ou None si non trouvée
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return None
        
        # Rechercher la licence
        result = supabase.table('licenses').select('*').eq('license_key', license_key).execute()
        
        if result.data and len(result.data) > 0:
            license_data = result.data[0]
            
            # Convertir les dates string en objets datetime
            if license_data.get('created_at'):
                license_data['created_at'] = datetime.datetime.fromisoformat(license_data['created_at'].replace('Z', '+00:00'))
            if license_data.get('expires_at'):
                license_data['expires_at'] = datetime.datetime.fromisoformat(license_data['expires_at'].replace('Z', '+00:00'))
            if license_data.get('last_used'):
                license_data['last_used'] = datetime.datetime.fromisoformat(license_data['last_used'].replace('Z', '+00:00'))
            
            return license_data
        
        return None
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de la licence: {e}")
        return None

def validate_license(license_key: str) -> Tuple[bool, str]:
    """
    Valide une licence (vérifie l'existence, l'expiration, l'activation, etc.).
    
    Args:
        license_key (str): Clé de licence à valider
        
    Returns:
        tuple: (is_valid, message) - Validité et message d'erreur si applicable
    """
    # Vérifier le format de la clé
    if not validate_license_key(license_key):
        return False, "Format de clé de licence invalide"
    
    # Récupérer les informations de la licence
    license_info = get_license_info(license_key)
    if not license_info:
        return False, "Licence non trouvée"
    
    # Vérifier si la licence est active
    if not license_info['is_active']:
        return False, "Licence désactivée"
    
    # Vérifier l'expiration
    if license_info['expires_at'] < datetime.datetime.now():
        return False, "Licence expirée"
    
    # Vérifier le nombre d'utilisations
    if license_info['max_usage'] > 0 and license_info['usage_count'] >= license_info['max_usage']:
        return False, "Limite d'utilisation atteinte"
    
    return True, "Licence valide"

def update_license_usage(license_key: str) -> bool:
    """
    Met à jour les statistiques d'utilisation d'une licence dans Supabase.
    
    Args:
        license_key (str): Clé de licence
        
    Returns:
        bool: True si la mise à jour a réussi
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        # Mettre à jour l'utilisation
        result = supabase.table('licenses').update({
            'last_used': datetime.datetime.now().isoformat(),
            'usage_count': supabase.raw('usage_count + 1')
        }).eq('license_key', license_key).execute()
        
        return len(result.data) > 0
        
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour de l'utilisation: {e}")
        return False

def deactivate_license(license_key: str) -> bool:
    """
    Désactive une licence dans Supabase.
    
    Args:
        license_key (str): Clé de licence à désactiver
        
    Returns:
        bool: True si la désactivation a réussi
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        # Désactiver la licence
        result = supabase.table('licenses').update({
            'is_active': False
        }).eq('license_key', license_key).execute()
        
        if len(result.data) > 0:
            print(f"✅ Licence {license_key} désactivée")
            return True
        else:
            print(f"❌ Licence {license_key} non trouvée")
            return False
        
    except Exception as e:
        print(f"❌ Erreur lors de la désactivation: {e}")
        return False

def get_all_licenses() -> List[Dict]:
    """
    Récupère toutes les licences depuis Supabase.
    
    Returns:
        list: Liste des licences
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return []
        
        # Récupérer toutes les licences
        result = supabase.table('licenses').select('*').order('created_at', desc=True).execute()
        
        licenses = []
        for license_data in result.data:
            # Convertir les dates string en objets datetime
            if license_data.get('created_at'):
                license_data['created_at'] = datetime.datetime.fromisoformat(license_data['created_at'].replace('Z', '+00:00'))
            if license_data.get('expires_at'):
                license_data['expires_at'] = datetime.datetime.fromisoformat(license_data['expires_at'].replace('Z', '+00:00'))
            if license_data.get('last_used'):
                license_data['last_used'] = datetime.datetime.fromisoformat(license_data['last_used'].replace('Z', '+00:00'))
            
            licenses.append(license_data)
        
        return licenses
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des licences: {e}")
        return []

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def format_license_key(license_key: str) -> str:
    """
    Formate une clé de licence pour l'affichage.
    
    Args:
        license_key (str): Clé de licence brute
        
    Returns:
        str: Clé formatée
    """
    clean_key = license_key.replace('-', '').replace(' ', '')
    return '-'.join([clean_key[i:i+4] for i in range(0, 32, 4)]).upper()

def get_license_status_text(license_info: Dict) -> str:
    """
    Retourne le statut textuel d'une licence.
    
    Args:
        license_info (dict): Informations de la licence
        
    Returns:
        str: Statut textuel
    """
    if not license_info['is_active']:
        return "Désactivée"
    
    if license_info['expires_at'] < datetime.datetime.now():
        return "Expirée"
    
    if license_info['max_usage'] > 0 and license_info['usage_count'] >= license_info['max_usage']:
        return "Limite atteinte"
    
    return "Active"

def days_until_expiration(license_info: Dict) -> int:
    """
    Calcule le nombre de jours avant expiration.
    
    Args:
        license_info (dict): Informations de la licence
        
    Returns:
        int: Nombre de jours avant expiration (négatif si expirée)
    """
    delta = license_info['expires_at'] - datetime.datetime.now()
    return delta.days

# ============================================================================
# CONFIGURATION SUPABASE
# ============================================================================

def setup_supabase_config():
    """
    Aide à configurer Supabase pour le système de licences.
    """
    print("🚀 Configuration Supabase pour le système de licences")
    print("\n1. Créez un projet Supabase sur https://supabase.com")
    print("2. Récupérez votre URL et clé API dans Settings > API")
    print("3. Configurez les variables d'environnement:")
    print("   - SUPABASE_URL=https://your-project.supabase.co")
    print("   - SUPABASE_KEY=your-anon-key")
    print("\n4. Exécutez le SQL suivant dans l'interface SQL de Supabase:")
    
    sql_script = """
    -- Créer la table licenses
    CREATE TABLE IF NOT EXISTS licenses (
        id BIGSERIAL PRIMARY KEY,
        license_key VARCHAR(255) UNIQUE NOT NULL,
        client_name VARCHAR(255) NOT NULL,
        client_email VARCHAR(255) NOT NULL,
        company_name VARCHAR(255),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        last_used TIMESTAMP WITH TIME ZONE,
        usage_count INTEGER DEFAULT 0,
        max_usage INTEGER DEFAULT -1,
        notes TEXT
    );
    
    -- Créer les index pour les performances
    CREATE INDEX IF NOT EXISTS idx_licenses_license_key ON licenses(license_key);
    CREATE INDEX IF NOT EXISTS idx_licenses_is_active ON licenses(is_active);
    CREATE INDEX IF NOT EXISTS idx_licenses_expires_at ON licenses(expires_at);
    
    -- Activer Row Level Security (RLS) pour la sécurité
    ALTER TABLE licenses ENABLE ROW LEVEL SECURITY;
    
    -- Créer une politique pour permettre la lecture publique (à ajuster selon vos besoins)
    CREATE POLICY "Allow public read access" ON licenses
        FOR SELECT USING (true);
    
    -- Créer une politique pour permettre l'insertion (à ajuster selon vos besoins)
    CREATE POLICY "Allow public insert" ON licenses
        FOR INSERT WITH CHECK (true);
    
    -- Créer une politique pour permettre la mise à jour (à ajuster selon vos besoins)
    CREATE POLICY "Allow public update" ON licenses
        FOR UPDATE USING (true);
    """
    
    print(sql_script)
    print("\n5. Testez la configuration avec la fonction de test") 