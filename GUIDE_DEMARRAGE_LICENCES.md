# 🚀 Guide de Démarrage Rapide - Système de Licences

## 📋 Prérequis

1. **PostgreSQL** installé et démarré
2. **Python 3.8+** avec les dépendances installées
3. **Base de données** créée pour le projet

## 🔧 Configuration en 3 Étapes

### Étape 1: Créer le fichier de configuration

Créez le fichier `app/services/credentials.json` avec le contenu suivant :

```json
{
  "postgresql": {
    "host": "localhost",
    "user": "postgres",
    "password": "votre_mot_de_passe",
    "database": "connecteur_sages",
    "port": "5432"
  }
}
```

**Remplacez** :
- `postgres` par votre utilisateur PostgreSQL
- `votre_mot_de_passe` par votre mot de passe PostgreSQL
- `connecteur_sages` par le nom de votre base de données

### Étape 2: Configuration automatique

Exécutez le script de configuration :

```bash
python setup_licenses.py
```

Ce script va :
- ✅ Tester la connexion PostgreSQL
- ✅ Créer la table `licenses`
- ✅ Créer une licence d'exemple (optionnel)

### Étape 3: Démarrer l'application

```bash
python -m uvicorn app.main:app --reload
```

## 🎯 Test du Système

### Test automatique
```bash
python test_licenses.py
```

### Test manuel
1. Ouvrez votre navigateur
2. Allez sur `http://localhost:8000/licenses/`
3. Vous devriez voir le tableau de bord des licences

## 📱 Interface Web

### URLs principales :
- **Tableau de bord** : `http://localhost:8000/licenses/`
- **Créer une licence** : `http://localhost:8000/licenses/create`
- **Détails d'une licence** : `http://localhost:8000/licenses/{license_key}`

### Fonctionnalités disponibles :
- ✅ Création de nouvelles licences
- ✅ Visualisation de toutes les licences
- ✅ Détails complets d'une licence
- ✅ Désactivation de licences
- ✅ Statistiques d'utilisation

## 🔌 API REST

### Endpoints disponibles :

```bash
# Créer une licence
POST /licenses/api/create
{
  "client_name": "Jean Dupont",
  "client_email": "jean@entreprise.com",
  "duration_days": 365,
  "max_usage": -1
}

# Valider une licence
POST /licenses/api/validate
{
  "license_key": "A1B2-C3D4-E5F6-7890-ABCD-EF12-3456-7890"
}

# Lister toutes les licences
GET /licenses/api/list

# Désactiver une licence
POST /licenses/api/deactivate/{license_key}
```

## 🛡️ Protection de l'Application

### Option 1: Protection globale (recommandé)

Ajoutez dans `app/main.py` :

```python
from app.middleware.license_middleware import LicenseMiddleware

# Ajouter le middleware (après la création de l'app)
app.add_middleware(LicenseMiddleware, app)
```

### Option 2: Protection de routes spécifiques

```python
from app.middleware.license_middleware import validate_license_for_request

@app.get("/protected-route")
async def protected_route(request: Request):
    license_key = request.headers.get("X-License-Key")
    if not license_key:
        raise HTTPException(status_code=401, detail="Licence requise")
    
    is_valid, message, info = validate_license_for_request(license_key)
    if not is_valid:
        raise HTTPException(status_code=403, detail=message)
    
    # Votre logique ici...
```

## 🔐 Authentification Client

Les clients peuvent fournir leur licence de 3 façons :

1. **En-tête HTTP** : `X-License-Key: YOUR_LICENSE_KEY`
2. **Cookie** : `license_key=YOUR_LICENSE_KEY`
3. **Paramètre** : `?license_key=YOUR_LICENSE_KEY`

### Exemple d'utilisation client :

```python
import requests

# Configuration
license_key = "A1B2-C3D4-E5F6-7890-ABCD-EF12-3456-7890"
base_url = "http://localhost:8000"

# Requête avec en-tête
headers = {"X-License-Key": license_key}
response = requests.get(f"{base_url}/api/protected-endpoint", headers=headers)

# Ou avec paramètre
response = requests.get(f"{base_url}/api/protected-endpoint?license_key={license_key}")
```

## 🐛 Dépannage

### Problèmes courants :

| Problème | Solution |
|----------|----------|
| `ModuleNotFoundError: pypyodbc` | `pip install pypyodbc` |
| Erreur PostgreSQL | Vérifiez `credentials.json` |
| Table non trouvée | Exécutez `python setup_licenses.py` |
| Licence non valide | Vérifiez le format de la clé |

### Logs utiles :

```bash
# Vérifier les dépendances
pip list | grep -E "(psycopg2|pypyodbc|fastapi)"

# Tester la connexion PostgreSQL
python -c "from app.services.connex import connect_to_postgres, load_credentials; print('OK' if connect_to_postgres(**load_credentials()['postgresql']) else 'ERREUR')"
```

## 📚 Documentation Complète

- [Documentation détaillée](docs/SYSTEME_LICENCES.md)
- [README principal](README_LICENCES.md)
- [Tests unitaires](test_licenses.py)

## 🆘 Support

Si vous rencontrez des problèmes :

1. Vérifiez que PostgreSQL est démarré
2. Testez la connexion avec `python setup_licenses.py`
3. Consultez les logs de l'application
4. Exécutez les tests avec `python test_licenses.py`

---

**🎉 Votre système de licences est maintenant prêt !** 