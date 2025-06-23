# -*- coding: utf-8 -*-
# Module de gestion des licences avec Supabase
# ---------------------------------------------
# Ce fichier centralise toutes les fonctions pour la création, validation,
# et gestion des licences en interagissant avec la base de données Supabase.

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

# Récupère l'URL de Supabase depuis les variables d'environnement.
# Une valeur par défaut est utilisée si la variable n'est pas définie.
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")

# Récupère la clé API "anon" de Supabase depuis les variables d'environnement.
# C'est une clé publique et sécurisée, utilisable côté client.
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your-anon-key")

# Clé secrète utilisée pour rendre la génération de hash de licence unique.
# À garder secrète et à ne pas exposer côté client.
SECRET_KEY = "connecteur-sages-v1-secret-key-2024"

# Durée de validité standard pour une nouvelle licence, en jours.
DEFAULT_LICENSE_DURATION = 365

# ============================================================================
# INITIALISATION SUPABASE
# ============================================================================

def get_supabase_client() -> Optional[Client]:
    """
    Initialise et retourne un client Supabase.

    Cette fonction est le point d'entrée pour toute communication avec Supabase.
    Elle utilise les variables d'environnement SUPABASE_URL et SUPABASE_KEY.

    Returns:
        Client: Une instance du client Supabase, ou None en cas d'erreur.
    """
    try:
        # Crée le client en utilisant les informations de configuration.
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return supabase
    except Exception as e:
        # Affiche une erreur claire si l'initialisation échoue.
        print(f"❌ Erreur lors de l'initialisation du client Supabase: {e}")
        return None

# ============================================================================
# GÉNÉRATION ET VALIDATION DES CLÉS
# ============================================================================

def generate_license_key(client_name: str, client_email: str, duration_days: int = DEFAULT_LICENSE_DURATION) -> str:
    """
    Génère une clé de licence unique et déterministe basée sur les informations du client.

    La clé est un hash SHA-256 d'une chaîne combinant les détails du client
    et une clé secrète, garantissant son unicité.

    Args:
        client_name (str): Le nom du client.
        client_email (str): L'email du client.
        duration_days (int): La durée de validité de la licence en jours.

    Returns:
        str: La clé de licence générée, formatée pour la lisibilité (ex: XXXX-XXXX-...).
    """
    # Crée une chaîne unique pour le hashing.
    unique_string = f"{client_name}:{client_email}:{duration_days}:{SECRET_KEY}"
    
    # Génère un hash SHA-256 pour garantir une clé non-devinable.
    hash_object = hashlib.sha256(unique_string.encode())
    hash_hex = hash_object.hexdigest()
    
    # Formate la clé en groupes de 4 caractères pour une meilleure lisibilité.
    # On ne prend que les 32 premiers caractères du hash pour une clé plus courte.
    formatted_key = '-'.join([hash_hex[i:i+4] for i in range(0, 32, 4)])
    
    return formatted_key.upper()

def validate_license_key(license_key: str) -> bool:
    """
    Valide le format d'une clé de licence (longueur, caractères hexadécimaux).

    Args:
        license_key (str): La clé de licence à vérifier.

    Returns:
        bool: True si le format est valide, False sinon.
    """
    if not license_key:
        return False
    
    # Nettoie la clé en retirant les tirets et les espaces.
    clean_key = license_key.replace('-', '').replace(' ', '')
    # Une clé valide doit contenir 32 caractères hexadécimaux.
    if len(clean_key) != 32:
        return False
    
    # Vérifie que tous les caractères sont bien hexadécimaux.
    try:
        int(clean_key, 16)
        return True
    except ValueError:
        return False

# ============================================================================
# GESTION DES LICENCES DANS SUPABASE (CRUD)
# ============================================================================

def create_licenses_table() -> bool:
    """
    Fournit le script SQL pour créer la table 'licenses' dans Supabase.

    Note: Cette fonction n'exécute pas le SQL. L'utilisateur doit le copier
    et l'exécuter dans l'éditeur SQL de l'interface Supabase pour des raisons
    de sécurité et de permissions.

    Returns:
        bool: Toujours True pour indiquer que le script a été fourni.
    """
    # Le SQL est fourni comme une aide pour l'administrateur.
    # Les opérations de type DDL (Data Definition Language) sont généralement
    # gérées via des migrations ou directement dans l'interface Supabase.
    create_table_sql = """
    -- Script de création de la table des licences
    CREATE TABLE IF NOT EXISTS public.licenses (
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
        max_usage INTEGER DEFAULT -1, -- -1 signifie illimité
        notes TEXT
    );
    
    -- Index pour accélérer les recherches par clé de licence
    CREATE INDEX IF NOT EXISTS idx_licenses_license_key ON public.licenses(license_key);
    
    -- Index pour filtrer rapidement les licences actives/inactives
    CREATE INDEX IF NOT EXISTS idx_licenses_is_active ON public.licenses(is_active);
    """
    
    print("📝 Veuillez exécuter le SQL suivant dans l'interface SQL de Supabase pour créer la table:")
    print(create_table_sql)
    return True

def add_license(client_name: str, client_email: str, company_name: Optional[str] = None, 
                duration_days: int = DEFAULT_LICENSE_DURATION, max_usage: int = -1, notes: Optional[str] = None) -> Optional[str]:
    """
    Ajoute une nouvelle licence dans la base de données Supabase.

    Args:
        client_name (str): Nom du client.
        client_email (str): Email du client.
        company_name (Optional[str]): Nom de l'entreprise (facultatif).
        duration_days (int): Durée de validité en jours.
        max_usage (int): Nombre maximum d'utilisations (-1 pour illimité).
        notes (Optional[str]): Notes additionnelles (facultatif).

    Returns:
        str: La clé de licence générée si l'ajout a réussi, sinon None.
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return None
        
        # Génère une nouvelle clé unique.
        license_key = generate_license_key(client_name, client_email, duration_days)
        
        # Calcule la date d'expiration à partir de la date actuelle.
        expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=duration_days)
        
        # Prépare l'objet de données à insérer.
        license_data = {
            'license_key': license_key,
            'client_name': client_name,
            'client_email': client_email,
            'company_name': company_name,
            'expires_at': expires_at.isoformat(),
            'max_usage': max_usage,
            'notes': notes,
            'is_active': True,
            'usage_count': 0
        }
        
        # Insère les données dans la table 'licenses'.
        result = supabase.table('licenses').insert(license_data).execute()
        
        # Vérifie que l'insertion a réussi.
        if result.data:
            print(f"✅ Licence créée avec succès pour {client_name}")
            return license_key
        else:
            print(f"❌ Erreur lors de l'ajout de la licence à Supabase: {result.error.message if result.error else 'Raison inconnue'}")
            return None
        
    except Exception as e:
        print(f"❌ Erreur fonctionnelle lors de l'ajout de la licence: {e}")
        return None

def get_license_info(license_key: str) -> Optional[Dict]:
    """
    Récupère les informations détaillées d'une licence spécifique depuis Supabase.

    Args:
        license_key (str): La clé de licence à rechercher.

    Returns:
        dict: Un dictionnaire contenant les informations de la licence, 
              ou None si la licence n'est pas trouvée.
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return None
        
        # Recherche la licence par sa clé unique.
        # .single() garantit qu'on attend une seule ligne et la retourne directement.
        result = supabase.table('licenses').select('*').eq('license_key', license_key).single().execute()
        
        license_info = result.data
        if license_info:
            # --- Standardisation des dates ---
            # Convertit les chaînes de date ISO 8601 de la DB en objets datetime Python
            # pour faciliter les manipulations (calculs, formatage).
            if license_info.get('created_at'):
                license_info['created_at'] = datetime.datetime.fromisoformat(license_info['created_at'].replace('Z', '+00:00'))
            if license_info.get('expires_at'):
                license_info['expires_at'] = datetime.datetime.fromisoformat(license_info['expires_at'].replace('Z', '+00:00'))
            if license_info.get('last_used'):
                license_info['last_used'] = datetime.datetime.fromisoformat(license_info['last_used'].replace('Z', '+00:00'))
            
            return license_info
        return None
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de la licence: {e}")
        return None

def get_all_licenses() -> List[Dict]:
    """
    Récupère la liste de toutes les licences enregistrées dans Supabase.

    Returns:
        list: Une liste de dictionnaires, où chaque dictionnaire représente une licence.
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return []
        
        # Récupère toutes les lignes de la table, triées par date de création.
        result = supabase.table('licenses').select('*').order('created_at', desc=True).execute()
        
        if not result.data:
            return []
            
        licenses = []
        for license_data in result.data:
            # Standardise les dates pour chaque licence de la liste.
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

def validate_license(license_key: str) -> Tuple[bool, str]:
    """
    Valide une licence en vérifiant son format, son existence, son statut et sa date d'expiration.

    Args:
        license_key (str): La clé de licence à valider.

    Returns:
        tuple: Un tuple (bool, str) contenant:
               - True si la licence est valide, False sinon.
               - Un message décrivant le statut ("Licence valide", "Licence expirée", etc.).
    """
    # 1. Vérifier le format de la clé.
    if not validate_license_key(license_key):
        return False, "Format de clé de licence invalide"
    
    # 2. Récupérer les informations de la licence.
    license_info = get_license_info(license_key)
    if not license_info:
        return False, "Licence non trouvée"
    
    # 3. Utiliser la logique de get_license_status_text pour déterminer le statut.
    status_text = get_license_status_text(license_info)
    
    if status_text == "Active":
        return True, "Licence valide"
    else:
        return False, status_text

def update_license_usage(license_key: str) -> bool:
    """
    Met à jour les statistiques d'utilisation d'une licence après une validation réussie.
    Incrémente le compteur d'utilisation et met à jour la date de dernière utilisation.

    Args:
        license_key (str): La clé de licence à mettre à jour.

    Returns:
        bool: True si la mise à jour a réussi, False sinon.
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        # Récupère le compteur d'utilisation actuel.
        license_info = get_license_info(license_key)
        if not license_info:
            return False
        current_usage = license_info.get('usage_count', 0)
        
        # Prépare les données à mettre à jour.
        update_data = {
            'last_used': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'usage_count': current_usage + 1
        }
        
        # Exécute la mise à jour.
        result = supabase.table('licenses').update(update_data).eq('license_key', license_key).execute()
        
        return bool(result.data)
        
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour de l'utilisation: {e}")
        return False

def deactivate_license(license_key: str) -> bool:
    """
    Désactive une licence en passant son champ 'is_active' à False.

    Args:
        license_key (str): La clé de licence à désactiver.

    Returns:
        bool: True si la désactivation a réussi, False sinon.
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        # Met à jour le champ 'is_active'.
        result = supabase.table('licenses').update({'is_active': False}).eq('license_key', license_key).execute()
        
        if result.data:
            print(f"✅ Licence {license_key} désactivée")
            return True
        else:
            print(f"❌ Erreur lors de la désactivation de la licence {license_key}")
            return False
        
    except Exception as e:
        print(f"❌ Erreur lors de la désactivation: {e}")
        return False

def reactivate_license(license_key: str) -> bool:
    """
    Réactive une licence qui a été désactivée.

    Args:
        license_key (str): La clé de licence à réactiver.

    Returns:
        bool: True si la réactivation a réussi, False sinon.
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        # Met à jour le champ 'is_active' pour le passer à True.
        result = supabase.table('licenses').update({'is_active': True}).eq('license_key', license_key).execute()
        
        if result.data:
            print(f"✅ Licence {license_key} réactivée")
            return True
        else:
            print(f"❌ Erreur lors de la réactivation de la licence {license_key}")
            return False
        
    except Exception as e:
        print(f"❌ Erreur lors de la réactivation: {e}")
        return False

def extend_license(license_key: str, days_to_add: int) -> bool:
    """
    Prolonge la durée de validité d'une licence en ajoutant un nombre de jours.
    
    Args:
        license_key (str): La clé de licence à prolonger.
        days_to_add (int): Le nombre de jours à ajouter à la date d'expiration.
        
    Returns:
        bool: True si la prolongation a réussi, False sinon.
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
            
        # Récupère les informations actuelles, y compris la date d'expiration.
        license_info = get_license_info(license_key)
        if not license_info:
            print(f"❌ Licence {license_key} non trouvée pour la prolongation.")
            return False
            
        # get_license_info retourne déjà un objet datetime, pas besoin de reconvertir.
        expires_at = license_info.get('expires_at')
        if not expires_at:
            print(f"❌ La licence {license_key} n'a pas de date d'expiration.")
            return False
        
        # Calcule la nouvelle date d'expiration.
        new_expires_at = expires_at + datetime.timedelta(days=days_to_add)
        
        # Met à jour la licence avec la nouvelle date.
        result = supabase.table('licenses').update({
            'expires_at': new_expires_at.isoformat()
        }).eq('license_key', license_key).execute()
        
        if result.data:
            print(f"✅ Licence {license_key} prolongée de {days_to_add} jours.")
            return True
        else:
            print(f"❌ Erreur lors de la prolongation de la licence {license_key}.")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la prolongation: {e}")
        return False

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def format_license_key(license_key: str) -> str:
    """
    Formate une clé de licence pour un affichage standard (groupes de 4).
    
    Args:
        license_key (str): Clé de licence brute.
        
    Returns:
        str: La clé formatée (ex: XXXX-XXXX-...).
    """
    clean_key = license_key.replace('-', '').replace(' ', '')
    return '-'.join([clean_key[i:i+4] for i in range(0, 32, 4)]).upper()

def get_license_status_text(license_info: Dict) -> str:
    """
    Retourne une chaîne de caractères décrivant le statut d'une licence.
    Cette fonction est principalement utilisée pour l'affichage dans l'interface.
    
    Args:
        license_info (dict): Le dictionnaire contenant les données de la licence.
        
    Returns:
        str: Le statut textuel ("Active", "Expirée", "Désactivée", "Limite atteinte").
    """
    # Priorité 1: la licence est-elle désactivée manuellement ?
    if not license_info.get('is_active'):
        return "Désactivée"
    
    expires_at = license_info.get('expires_at')
    # Priorité 2: la licence a-t-elle expiré ?
    if expires_at:
        # S'assure que la date est bien un objet datetime.
        if isinstance(expires_at, str):
            expires_at = datetime.datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        
        # Compare avec la date/heure actuelle en UTC pour éviter les erreurs de fuseau.
        if expires_at < datetime.datetime.now(datetime.timezone.utc):
            return "Expirée"

    # Priorité 3: la limite d'utilisation a-t-elle été atteinte ?
    if license_info.get('max_usage', -1) > 0 and license_info.get('usage_count', 0) >= license_info.get('max_usage', -1):
        return "Limite atteinte"
    
    # Si aucune des conditions ci-dessus n'est remplie, la licence est active.
    return "Active"

def days_until_expiration(license_info: Dict) -> int:
    """
    Calcule et retourne le nombre de jours restants avant l'expiration d'une licence.
    
    Args:
        license_info (dict): Le dictionnaire de la licence.
        
    Returns:
        int: Le nombre de jours restants. Négatif si la licence a déjà expiré.
    """
    expires_at = license_info['expires_at']
    
    # S'assure que 'expires_at' est un objet datetime pour le calcul.
    if isinstance(expires_at, str):
        expires_at = datetime.datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
    
    # Utilise une date/heure actuelle "aware" (avec fuseau UTC) pour une comparaison correcte.
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    
    # Calcule la différence.
    delta = expires_at - now_utc
    return delta.days

# ============================================================================
# SCRIPT DE CONFIGURATION
# ============================================================================

def setup_supabase_config():
    """
    Affiche des instructions pour aider l'administrateur à configurer Supabase.
    """
    print("🚀 Aide à la configuration Supabase pour le système de licences")
    print("\n1. Créez un projet Supabase sur https://supabase.com")
    print("2. Dans votre projet, allez dans Settings > API.")
    print("3. Récupérez votre 'Project URL' et votre clé 'anon' (public).")
    print("4. Créez un fichier .env à la racine du projet et ajoutez ces lignes:")
    print("   SUPABASE_URL=VOTRE_URL_ICI")
    print("   SUPABASE_KEY=VOTRE_CLE_ANON_ICI")
    print("\n5. Allez dans l'éditeur SQL ('SQL Editor') et exécutez le script de création de table (fourni par la fonction create_licenses_table()).")
    print("\n6. (IMPORTANT) Allez dans Authentication > Policies et créez une policy pour autoriser les mises à jour (UPDATE) sur la table 'licenses', ou exécutez le SQL suivant:")
    
    sql_policy_script = """
    -- Policy pour autoriser les mises à jour sur la table 'licenses'
    -- Sans cela, les fonctions comme désactiver, réactiver, prolonger échoueront.
    CREATE POLICY "Allow all updates for anon"
    ON public.licenses
    FOR UPDATE
    TO anon
    USING (true)
    WITH CHECK (true);
    """
    print(sql_policy_script) 