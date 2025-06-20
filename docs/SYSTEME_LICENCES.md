# Système de Gestion des Licences

## Vue d'ensemble

Le système de gestion des licences permet de contrôler l'accès à l'application Connecteur Sages en utilisant des clés de licence uniques par client. Chaque licence est stockée dans une base de données PostgreSQL et peut être configurée avec des limites de durée et d'utilisation.

## Fonctionnalités

### 🔑 Génération de Licences
- Génération automatique de clés de licence uniques basées sur les informations du client
- Format standardisé : `XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX`
- Clés cryptographiquement sécurisées utilisant SHA-256

### 📊 Gestion des Licences
- **Durée de validité** : Configurable en jours (1 à 3650 jours)
- **Limite d'utilisation** : Nombre maximum d'utilisations (-1 pour illimité)
- **Statut** : Active, Désactivée, Expirée, Limite atteinte
- **Suivi d'utilisation** : Compteur d'utilisations et dernière utilisation

### 🛡️ Validation Sécurisée
- Validation en temps réel des licences
- Vérification de l'expiration
- Contrôle des limites d'utilisation
- Protection contre les clés invalides

### 📈 Interface d'Administration
- Tableau de bord complet avec statistiques
- Création de nouvelles licences
- Gestion des licences existantes
- Désactivation/réactivation des licences

## Structure de la Base de Données

### Table `licenses`

```sql
CREATE TABLE licenses (
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
```

## Installation et Configuration

### 1. Configuration PostgreSQL

Assurez-vous que votre fichier `app/services/credentials.json` contient la configuration PostgreSQL :

```json
{
  "postgresql": {
    "host": "localhost",
    "user": "votre_utilisateur",
    "password": "votre_mot_de_passe",
    "database": "votre_base_de_donnees",
    "port": "5432"
  }
}
```

### 2. Création de la Table

La table `licenses` sera automatiquement créée lors de la première utilisation du système.

### 3. Test du Système

Exécutez le script de test pour vérifier que tout fonctionne :

```bash
python test_licenses.py
```

## Utilisation

### Interface Web

1. **Accès au tableau de bord** : `http://localhost:8000/licenses/`
2. **Création d'une licence** : `http://localhost:8000/licenses/create`
3. **Détails d'une licence** : `http://localhost:8000/licenses/{license_key}`

### API REST

#### Créer une Licence

```bash
POST /licenses/api/create
Content-Type: application/json

{
  "client_name": "Jean Dupont",
  "client_email": "jean.dupont@entreprise.com",
  "company_name": "Entreprise ABC",
  "duration_days": 365,
  "max_usage": -1,
  "notes": "Licence annuelle"
}
```

#### Valider une Licence

```bash
POST /licenses/api/validate
Content-Type: application/json

{
  "license_key": "A1B2-C3D4-E5F6-7890-ABCD-EF12-3456-7890"
}
```

#### Désactiver une Licence

```bash
POST /licenses/api/deactivate/{license_key}
```

#### Lister toutes les Licences

```bash
GET /licenses/api/list
```

### Intégration dans l'Application

#### Protection par Middleware

Pour protéger toute l'application, ajoutez le middleware dans `app/main.py` :

```python
from app.middleware.license_middleware import LicenseMiddleware

# Ajouter le middleware
app.add_middleware(LicenseMiddleware, app)
```

#### Protection de Routes Spécifiques

Pour protéger une route spécifique :

```python
from app.middleware.license_middleware import validate_license_for_request

@app.get("/protected-route")
async def protected_route(request: Request):
    license_key = request.headers.get("X-License-Key")
    if not license_key:
        raise HTTPException(status_code=401, detail="Licence requise")
    
    is_valid, message, license_info = validate_license_for_request(license_key)
    if not is_valid:
        raise HTTPException(status_code=403, detail=message)
    
    # Route protégée...
```

## Fourniture de Licences aux Clients

### Méthodes d'Authentification

Les clients peuvent fournir leur clé de licence de trois façons :

1. **En-tête HTTP** : `X-License-Key: YOUR_LICENSE_KEY`
2. **Cookie** : `license_key=YOUR_LICENSE_KEY`
3. **Paramètre de requête** : `?license_key=YOUR_LICENSE_KEY`

### Exemple d'Utilisation Client

```python
import requests

# Configuration
license_key = "A1B2-C3D4-E5F6-7890-ABCD-EF12-3456-7890"
base_url = "http://localhost:8000"

# Requête avec en-tête
headers = {"X-License-Key": license_key}
response = requests.get(f"{base_url}/api/protected-endpoint", headers=headers)

# Ou avec paramètre de requête
response = requests.get(f"{base_url}/api/protected-endpoint?license_key={license_key}")
```

## Sécurité

### Clés de Licence
- Générées avec SHA-256 pour la sécurité cryptographique
- Basées sur les informations du client pour l'unicité
- Format standardisé pour faciliter la validation

### Validation
- Vérification en temps réel à chaque requête
- Protection contre les clés expirées ou désactivées
- Suivi des tentatives d'utilisation

### Recommandations
- Changez la `SECRET_KEY` en production
- Utilisez HTTPS en production
- Surveillez régulièrement les logs d'utilisation
- Sauvegardez régulièrement la base de données

## Maintenance

### Tâches Régulières

1. **Surveillance des licences expirées** : Vérifiez régulièrement les licences qui expirent bientôt
2. **Nettoyage des licences inactives** : Supprimez les anciennes licences désactivées
3. **Sauvegarde de la base** : Sauvegardez régulièrement la table `licenses`

### Scripts Utilitaires

#### Licences Expirées

```sql
SELECT * FROM licenses 
WHERE expires_at < CURRENT_TIMESTAMP 
AND is_active = TRUE;
```

#### Licences Expirant Bientôt

```sql
SELECT * FROM licenses 
WHERE expires_at BETWEEN CURRENT_TIMESTAMP 
AND CURRENT_TIMESTAMP + INTERVAL '30 days'
AND is_active = TRUE;
```

#### Statistiques d'Utilisation

```sql
SELECT 
    COUNT(*) as total_licenses,
    COUNT(CASE WHEN is_active THEN 1 END) as active_licenses,
    COUNT(CASE WHEN expires_at < CURRENT_TIMESTAMP THEN 1 END) as expired_licenses,
    AVG(usage_count) as avg_usage
FROM licenses;
```

## Dépannage

### Problèmes Courants

1. **Erreur de connexion PostgreSQL**
   - Vérifiez la configuration dans `credentials.json`
   - Assurez-vous que PostgreSQL est démarré

2. **Licence non trouvée**
   - Vérifiez le format de la clé
   - Assurez-vous que la clé existe dans la base

3. **Licence expirée**
   - Prolongez la licence ou créez-en une nouvelle
   - Vérifiez la date d'expiration

4. **Limite d'utilisation atteinte**
   - Augmentez la limite ou créez une nouvelle licence
   - Vérifiez le compteur d'utilisation

### Logs et Debug

Activez les logs détaillés en modifiant le niveau de log dans l'application.

## Support

Pour toute question ou problème avec le système de licences, consultez :
- Les logs de l'application
- La documentation de l'API
- Les tests unitaires dans `test_licenses.py` 