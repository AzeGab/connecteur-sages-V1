# app/services/codial/heures.py
# Module de gestion du transfert des heures Codial
# Ce fichier contient les fonctions nécessaires pour transférer les heures
# entre BatiSimply et HFSQL (Codial)

from app.services.connex import connect_to_hfsql, load_credentials, recup_batisimply_token
import requests

# ============================================================================
# TRANSFERT BATISIMPLY VERS HFSQL (CODIAL)
# ============================================================================

def transfer_heures_batisimply_to_hfsql():
    """
    Transfère les heures depuis BatiSimply vers HFSQL (Codial).
    
    Cette fonction :
    1. Récupère les heures depuis BatiSimply via l'API
    2. Les traite et les insère dans HFSQL
    3. Gère les mises à jour et les nouveaux enregistrements
    
    Returns:
        tuple: (bool, str)
    """
    try:
        # Récupération du token
        token = recup_batisimply_token()
        if not token:
            return False, "❌ Impossible de continuer sans token Batisimply"

        # Connexion à HFSQL
        creds = load_credentials()
        if not creds or "hfsql" not in creds:
            return False, "❌ Informations HFSQL manquantes"

        hfsql_conn = connect_to_hfsql(
            creds["hfsql"]["host"],
            creds["hfsql"]["user"],
            creds["hfsql"].get("password", ""),
            creds["hfsql"]["database"],
            creds["hfsql"].get("port", "4900"),
            creds["hfsql"].get("dsn", "")
        )

        if not hfsql_conn:
            return False, "❌ Connexion à HFSQL échouée"

        # Configuration de l'API BatiSimply
        API_URL = "https://api.staging.batisimply.fr/api/timeSlotManagement/allUsers"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Récupération des heures depuis BatiSimply
        response = requests.get(API_URL, headers=headers)
        if response.status_code != 200:
            return False, f"❌ Erreur API BatiSimply : {response.status_code}"

        heures_data = response.json()
        heures_count = 0

        hfsql_cursor = hfsql_conn.cursor()

        # Traitement de chaque heure
        for heure in heures_data:
            try:
                # TODO: Adapter selon la structure de la table HFSQL
                # Exemple de structure à adapter :
                hfsql_cursor.execute("""
                    INSERT INTO SuiviMO 
                    (CodeChantier, CodeSalarie, Date, Heures, Commentaire)
                    VALUES (?, ?, ?, ?, ?)
                    ON DUPLICATE KEY UPDATE
                    Heures = VALUES(Heures),
                    Commentaire = VALUES(Commentaire)
                """, (
                    heure.get('projectCode'),
                    heure.get('userId'),
                    heure.get('date'),
                    heure.get('hours'),
                    heure.get('comment', '')
                ))
                heures_count += 1

            except Exception as e:
                print(f"❌ Erreur lors du traitement de l'heure {heure.get('id')} : {e}")
                continue

        # Validation des modifications
        hfsql_conn.commit()
        hfsql_cursor.close()
        hfsql_conn.close()

        return True, f"✅ {heures_count} heure(s) transférée(s) vers HFSQL"

    except Exception as e:
        return False, f"❌ Erreur lors du transfert vers HFSQL : {e}"
