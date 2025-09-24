# app/services/batigest/sync.py
# Module de synchronisation complète Batigest
# Ce fichier contient les fonctions de synchronisation complète
# entre Batigest, PostgreSQL et BatiSimply

from .chantiers import transfer_chantiers, transfer_chantiers_vers_batisimply, update_code_projet_chantiers
from .heures import transfer_heures_to_postgres, transfer_heures_to_sqlserver
from .devis import transfer_devis, transfer_devis_vers_batisimply
from app.services.connex import recup_batisimply_token, connexion

# ============================================================================
# SYNCHRONISATION DE BATIGEST VERS BATISIMPLY
# ============================================================================

def sync_batigest_to_batisimply():
    """
    Synchronise les données de Batigest vers Batisimply via PostgreSQL.
    - Étape 1 : Récupère les données depuis Batigest (SQL Server) vers PostgreSQL.
    - Étape 2 : Transfère les heures de Batigest vers PostgreSQL.
    - Étape 3 : Transfère les chantiers depuis PostgreSQL vers BatiSimply.
    
    Returns:
        tuple: (bool, str)
    """
    try:
        print("\n=== DÉBUT DE LA SYNCHRONISATION BATIGEST → BATISIMPLY ===")

        # 1. Récupération des credentials et du mode
        from app.services.connex import load_credentials
        creds = load_credentials()
        if not creds:
            return False, "❌ Impossible de charger les credentials."

        mode = creds.get("mode", "chantier")
        print(f"\n🔁 Mode de synchronisation : {mode}")

        # 2. Transfert des données Batigest → PostgreSQL
        print("\n🔄 Transfert des données Batigest vers PostgreSQL...")
        if mode == "devis":
            success, message = transfer_devis()
        else:
            success, message = transfer_chantiers()

        if not success:
            return False, f"❌ Échec du transfert SQL Server → PostgreSQL : {message}"
        print(f"✅ {message}")

        # 3. Transfert des données PostgreSQL → BatiSimply
        print("\n🔄 Transfert des données PostgreSQL → Batisimply...")
        if mode == "devis":
            success = transfer_devis_vers_batisimply()
        else:
            success = transfer_chantiers_vers_batisimply()

        if not success:
            return False, "❌ Échec du transfert PostgreSQL → BatiSimply"
        print("✅ Transfert vers BatiSimply terminé avec succès")

        print("\n=== SYNCHRONISATION TERMINÉE AVEC SUCCÈS ===")
        return True, "✅ Synchronisation complète Batigest → Batisimply réussie."

    except Exception as e:
        print(f"\n❌ Erreur inattendue : {e}")
        return False, f"❌ Erreur lors de la synchronisation : {e}"

# ============================================================================
# SYNCHRONISATION DE BATISIMPLY VERS BATIGEST
# ============================================================================

def sync_batisimply_to_batigest():
    """
    Synchronise les heures de Batisimply vers Batigest via PostgreSQL.
    
    Flux : Batisimply → PostgreSQL → Batigest (SQL Server)
    
    Returns:
        tuple: (bool, str)
            - bool: True si la synchronisation a réussi, False sinon
            - str: Message décrivant le résultat de l'opération
    """
    try:
        print("\n=== DÉBUT DE LA SYNCHRONISATION BATISIMPLY → BATIGEST ===")
        
        # Récupération du token Batisimply
        token = recup_batisimply_token()
        if not token:
            return False, "❌ Impossible de continuer sans token Batisimply"

        # Configuration de l'API BatiSimply
        API_URL = "https://api.staging.batisimply.fr/api/project"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        postgres_conn, sqlserver_conn = connexion()

        print("✅ Connexions aux bases de données établies")

        # 1. Synchronisation Batisimply → PostgreSQL
        print("\n🔄 Synchronisation Batisimply → PostgreSQL")
        
        # Récupération des heures depuis Batisimply et envoi vers PostgreSQL
        transfer_heures_to_postgres()
        update_code_projet_chantiers()
        
        # 2. Synchronisation PostgreSQL → Batigest
        heures_transferees = transfer_heures_to_sqlserver()

        # Fermeture des connexions
        postgres_conn.close()
        sqlserver_conn.close()

        print(f"\n✅ {heures_transferees} heure(s) synchronisée(s)")
        print("\n=== FIN DE LA SYNCHRONISATION BATISIMPLY → BATIGEST ===")
        return True, f"✅ Synchronisation complète Batisimply → Batigest réussie. {heures_transferees} heure(s) transférée(s)."

    except Exception as e:
        print(f"\n❌ Erreur lors de la synchronisation : {e}")
        return False, f"❌ Erreur lors de la synchronisation : {e}"
