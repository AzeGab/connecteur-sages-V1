# -*- coding: utf-8 -*-
# !! MODULE OBSOLÈTE !!
# ============================================================================
# Ce module gérait le système de licences avec une base de données PostgreSQL.
# Il a été ENTIÈREMENT REMPLACÉ par 'app/services/supabase_licences.py'.
#
# Ce fichier est conservé à des fins d'archivage ou pour d'éventuelles
# consultations sur l'ancienne logique. NE PAS L'UTILISER pour du nouveau
# développement.
# ============================================================================

import hashlib
import datetime
import uuid
import json
import os
from typing import Optional, Dict, List, Tuple
from app.services.connex import connect_to_postgres

# ============================================================================
# CONFIGURATION (Ancienne)
# ============================================================================

# Clé secrète pour la génération des licences.
SECRET_KEY = "connecteur-sages-v1-secret-key-2024"

# Durée de validité par défaut (en jours).
DEFAULT_LICENSE_DURATION = 365

# ============================================================================
# GÉNÉRATION ET VALIDATION (Logique conservée)
# ============================================================================

def generate_license_key(client_name: str, client_email: str, duration_days: int = DEFAULT_LICENSE_DURATION) -> str:
    """
    Génère une clé de licence unique pour un client.
    (Cette fonction est conceptuellement similaire à celle de Supabase).
    
    Args:
        client_name (str): Nom du client.
        client_email (str): Email du client.
        duration_days (int): Durée de validité en jours.
        
    Returns:
        str: Clé de licence générée.
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
    (Logique identique à celle utilisée pour Supabase).
    
    Args:
        license_key (str): Clé de licence à valider.
        
    Returns:
        bool: True si le format est valide, False sinon.
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
# GESTION POSTGRESQL (OBSOLÈTE)
# ============================================================================

def create_licenses_table(conn) -> bool:
    """
    (Obsolète) Crée la table 'licenses' dans la base de données PostgreSQL.
    
    Args:
        conn: Objet de connexion PostgreSQL (psycopg2).
        
    Returns:
        bool: True si la table a été créée avec succès.
    """
    try:
        cursor = conn.cursor()
        
        create_table_query = """
        CREATE TABLE IF NOT EXISTS licenses (
            id SERIAL PRIMARY KEY,
            license_key VARCHAR(255) UNIQUE NOT NULL,
            client_name VARCHAR(255) NOT NULL,
            client_email VARCHAR(255) NOT NULL,
            company_name VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            last_used TIMESTAMP,
            usage_count INTEGER DEFAULT 0,
            max_usage INTEGER DEFAULT -1,
            notes TEXT
        );
        """
        
        cursor.execute(create_table_query)
        conn.commit()
        cursor.close()
        print("✅ Table licenses créée avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de la table licenses: {e}")
        return False

def add_license(conn, client_name: str, client_email: str, company_name: str = None, 
                duration_days: int = DEFAULT_LICENSE_DURATION, max_usage: int = -1, notes: str = None) -> Optional[str]:
    """
    (Obsolète) Ajoute une nouvelle licence dans la table PostgreSQL.
    
    Args:
        conn: Connexion PostgreSQL.
        client_name (str): Nom du client.
        client_email (str): Email du client.
        company_name (str): Nom de l'entreprise (optionnel).
        duration_days (int): Durée de validité.
        max_usage (int): Nombre max d'utilisations.
        notes (str): Notes additionnelles.
        
    Returns:
        str: Clé de licence générée ou None en cas d'erreur.
    """
    try:
        # Générer la clé de licence
        license_key = generate_license_key(client_name, client_email, duration_days)
        
        # Calculer la date d'expiration
        expires_at = datetime.datetime.now() + datetime.timedelta(days=duration_days)
        
        cursor = conn.cursor()
        
        insert_query = """
        INSERT INTO licenses (license_key, client_name, client_email, company_name, 
                            expires_at, max_usage, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(insert_query, (
            license_key, client_name, client_email, company_name,
            expires_at, max_usage, notes
        ))
        
        conn.commit()
        cursor.close()
        
        print(f"✅ Licence créée avec succès pour {client_name}")
        return license_key
        
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout de la licence: {e}")
        return None

def get_license_info(conn, license_key: str) -> Optional[Dict]:
    """
    (Obsolète) Récupère les informations d'une licence depuis PostgreSQL.
    
    Args:
        conn: Connexion PostgreSQL.
        license_key (str): Clé de licence.
        
    Returns:
        dict: Informations de la licence ou None si non trouvée.
    """
    try:
        cursor = conn.cursor()
        
        select_query = """
        SELECT id, license_key, client_name, client_email, company_name,
               created_at, expires_at, is_active, last_used, usage_count, max_usage, notes
        FROM licenses
        WHERE license_key = %s
        """
        
        cursor.execute(select_query, (license_key,))
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            return {
                'id': result[0],
                'license_key': result[1],
                'client_name': result[2],
                'client_email': result[3],
                'company_name': result[4],
                'created_at': result[5],
                'expires_at': result[6],
                'is_active': result[7],
                'last_used': result[8],
                'usage_count': result[9],
                'max_usage': result[10],
                'notes': result[11]
            }
        return None
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de la licence: {e}")
        return None

def validate_license(conn, license_key: str) -> Tuple[bool, str]:
    """
    (Obsolète) Valide une licence en interrogeant la base PostgreSQL.
    
    Args:
        conn: Connexion PostgreSQL.
        license_key (str): Clé de licence à valider.
        
    Returns:
        tuple: (is_valid, message)
    """
    # Vérifier le format de la clé
    if not validate_license_key(license_key):
        return False, "Format de clé de licence invalide"
    
    # Récupérer les informations de la licence
    license_info = get_license_info(conn, license_key)
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

def update_license_usage(conn, license_key: str) -> bool:
    """
    (Obsolète) Met à jour le compteur d'utilisation dans PostgreSQL.
    
    Args:
        conn: Connexion PostgreSQL.
        license_key (str): Clé de licence.
        
    Returns:
        bool: True si la mise à jour a réussi.
    """
    try:
        cursor = conn.cursor()
        
        update_query = """
        UPDATE licenses 
        SET last_used = CURRENT_TIMESTAMP, usage_count = usage_count + 1
        WHERE license_key = %s
        """
        
        cursor.execute(update_query, (license_key,))
        conn.commit()
        cursor.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour de l'utilisation: {e}")
        return False

def deactivate_license(conn, license_key: str) -> bool:
    """
    (Obsolète) Désactive une licence dans PostgreSQL.
    
    Args:
        conn: Connexion PostgreSQL.
        license_key (str): Clé de licence à désactiver.
        
    Returns:
        bool: True si la désactivation a réussi.
    """
    try:
        cursor = conn.cursor()
        
        update_query = """
        UPDATE licenses 
        SET is_active = FALSE
        WHERE license_key = %s
        """
        
        cursor.execute(update_query, (license_key,))
        conn.commit()
        cursor.close()
        
        print(f"✅ Licence {license_key} désactivée")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la désactivation: {e}")
        return False

def get_all_licenses(conn) -> List[Dict]:
    """
    (Obsolète) Récupère toutes les licences depuis PostgreSQL.
    
    Args:
        conn: Connexion PostgreSQL.
        
    Returns:
        list: Liste des licences.
    """
    try:
        cursor = conn.cursor()
        
        select_query = """
        SELECT id, license_key, client_name, client_email, company_name,
               created_at, expires_at, is_active, last_used, usage_count, max_usage, notes
        FROM licenses
        ORDER BY created_at DESC
        """
        
        cursor.execute(select_query)
        results = cursor.fetchall()
        cursor.close()
        
        licenses = []
        for result in results:
            licenses.append({
                'id': result[0],
                'license_key': result[1],
                'client_name': result[2],
                'client_email': result[3],
                'company_name': result[4],
                'created_at': result[5],
                'expires_at': result[6],
                'is_active': result[7],
                'last_used': result[8],
                'usage_count': result[9],
                'max_usage': result[10],
                'notes': result[11]
            })
        
        return licenses
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des licences: {e}")
        return []

# ============================================================================
# FONCTIONS UTILITAIRES (Logique conservée)
# ============================================================================

def format_license_key(license_key: str) -> str:
    """
    Formate une clé de licence pour l'affichage.
    """
    clean_key = license_key.replace('-', '').replace(' ', '')
    return '-'.join([clean_key[i:i+4] for i in range(0, 32, 4)]).upper()

def get_license_status_text(license_info: Dict) -> str:
    """
    Retourne le statut textuel d'une licence.
    Note: Utilise des objets datetime "naïfs" (sans fuseau horaire),
    contrairement à la nouvelle version qui gère les fuseaux (aware).
    
    Args:
        license_info (dict): Informations de la licence.
        
    Returns:
        str: Statut textuel.
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
    Note: Utilise des objets datetime "naïfs".
    
    Args:
        license_info (dict): Informations de la licence.
        
    Returns:
        int: Nombre de jours avant expiration (négatif si expirée).
    """
    delta = license_info['expires_at'] - datetime.datetime.now()
    return delta.days





