#!/usr/bin/env python3
# Script de test simple pour vérifier que l'application fonctionne

import requests
import time


def test_application():
    """Teste que l'application fonctionne correctement."""
    print("[TEST] Application Connecteur SAGES...")

    # Attendre que l'application démarre
    print("[TEST] Attente du démarrage de l'application...")
    time.sleep(3)

    try:
        # Accueil
        print("[TEST] GET /")
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code != 200:
            print(f"[ERR] Accueil: {response.status_code}")
            return False
        print("[OK] Accueil accessible")

        # Configuration
        print("[TEST] GET /configuration")
        response = requests.get("http://localhost:8000/configuration", timeout=5)
        if response.status_code != 200:
            print(f"[ERR] Configuration: {response.status_code}")
            return False
        print("[OK] Configuration accessible")

        # Licence expirée (toujours servi)
        print("[TEST] GET /license-expired")
        response = requests.get("http://localhost:8000/license-expired", timeout=5)
        if response.status_code != 200:
            print(f"[ERR] Licence expirée: {response.status_code}")
            return False
        print("[OK] Licence expirée accessible")

        # Santé
        print("[TEST] GET /health")
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print(f"[ERR] Health: {response.status_code}")
            return False
        print("[OK] Health accessible")

        print("\n[OK] Tous les tests sont passés !")
        print("\n[INFO] Accès rapide :")
        print("   - Accueil: http://localhost:8000/")
        print("   - Configuration: http://localhost:8000/configuration")
        print("   - Licence expirée: http://localhost:8000/license-expired")
        return True

    except requests.exceptions.ConnectionError:
        print("[ERR] Impossible de se connecter à l'application")
        print("[TIP] Démarrez l'application avec:")
        print("   python -m uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"[ERR] Erreur lors du test: {e}")
        return False


if __name__ == "__main__":
    test_application()

