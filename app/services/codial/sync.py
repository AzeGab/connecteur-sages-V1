# app/services/codial/sync.py
# Module de synchronisation complète Codial
# Ce fichier contient les fonctions de synchronisation complète
# entre Codial, PostgreSQL et BatiSimply

from .chantiers import transfer_chantiers_codial, transfer_chantiers_codial_vers_batisimply
from .heures import transfer_heures_batisimply_to_hfsql
from app.services.connex import recup_batisimply_token

# ============================================================================
# SYNCHRONISATION CODIAL VERS BATISIMPLY
# ============================================================================

def sync_codial_to_batisimply():
    """
    Synchronise les données de Codial vers BatiSimply via PostgreSQL.
    - Étape 1 : Récupère les données depuis Codial (HFSQL) vers PostgreSQL.
    - Étape 2 : Transfère les chantiers depuis PostgreSQL vers BatiSimply.
    
    Returns:
        tuple: (bool, str)
    """
    try:
        print("\n=== DÉBUT DE LA SYNCHRONISATION CODIAL → BATISIMPLY ===")

        # 1. Transfert des données Codial → PostgreSQL
        print("\n🔄 Transfert des données Codial vers PostgreSQL...")
        success, message = transfer_chantiers_codial()

        if not success:
            return False, f"❌ Échec du transfert HFSQL → PostgreSQL : {message}"
        print(f"✅ {message}")

        # 2. Transfert des chantiers PostgreSQL → BatiSimply
        print("\n🔄 Transfert des chantiers PostgreSQL → BatiSimply...")
        success = transfer_chantiers_codial_vers_batisimply()

        if not success:
            return False, "❌ Échec du transfert PostgreSQL → BatiSimply"
        print("✅ Transfert vers BatiSimply terminé avec succès")

        print("\n=== SYNCHRONISATION CODIAL TERMINÉE AVEC SUCCÈS ===")
        return True, "✅ Synchronisation complète Codial → BatiSimply réussie."

    except Exception as e:
        print(f"\n❌ Erreur inattendue : {e}")
        return False, f"❌ Erreur lors de la synchronisation : {e}"

# ============================================================================
# SYNCHRONISATION BATISIMPLY VERS CODIAL
# ============================================================================

def sync_batisimply_to_codial():
    """
    Synchronise les heures de BatiSimply vers Codial via HFSQL.
    
    Flux : BatiSimply → HFSQL (Codial)
    
    Returns:
        tuple: (bool, str)
            - bool: True si la synchronisation a réussi, False sinon
            - str: Message décrivant le résultat de l'opération
    """
    try:
        print("\n=== DÉBUT DE LA SYNCHRONISATION BATISIMPLY → CODIAL ===")
        
        # Récupération du token Batisimply
        token = recup_batisimply_token()
        if not token:
            return False, "❌ Impossible de continuer sans token Batisimply"

        print("✅ Token récupéré")

        # Synchronisation BatiSimply → HFSQL
        print("\n🔄 Synchronisation BatiSimply → HFSQL")
        success, message = transfer_heures_batisimply_to_hfsql()

        if not success:
            return False, f"❌ Échec du transfert vers HFSQL : {message}"
        print(f"✅ {message}")

        print("\n=== FIN DE LA SYNCHRONISATION BATISIMPLY → CODIAL ===")
        return True, "✅ Synchronisation complète BatiSimply → Codial réussie."

    except Exception as e:
        print(f"\n❌ Erreur lors de la synchronisation : {e}")
        return False, f"❌ Erreur lors de la synchronisation : {e}"
