# 🗝️ Système de Gestion des Licences - Connecteur Sages

## 📋 Résumé

Ce système permet de gérer les licences d'utilisation de l'application Connecteur Sages avec des clés de série uniques par client. Chaque licence est stockée dans PostgreSQL et peut être configurée avec des limites de durée et d'utilisation.

## ✨ Fonctionnalités Principales

### 🔑 Génération de Licences
- **Clés uniques** : Génération automatique basée sur les informations client
- **Format sécurisé** : `XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX`
- **Cryptographie** : Utilisation de SHA-256 pour la sécurité

### 📊 Gestion Complète
- **Durée configurable** : 1 à 3650 jours
- **Limites d'usage** : Nombre maximum d'utilisations ou illimité
- **Statuts multiples** : Active, Désactivée, Expirée, Limite atteinte
- **Suivi détaillé** : Compteur d'utilisations et historique

### 🛡️ Sécurité
- **Validation temps réel** : À chaque requête
- **Protection complète** : Contre les clés invalides/expirées
- **Middleware intégré** : Protection automatique des routes

### 🎛️ Interface d'Administration
- **Tableau de bord** : Vue d'ensemble avec statistiques
- **Gestion CRUD** : Création, lecture, mise à jour, suppression
- **API REST** : Intégration facile avec d'autres systèmes

## 🚀 Installation Rapide

### 1. Configuration PostgreSQL
```json
// app/services/credentials.json
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

### 2. Test du Système
```bash
python test_licenses.py
```

### 3. Accès à l'Interface
- **Tableau de bord** : `http://localhost:8000/licenses/`
- **Création** : `http://localhost:8000/licenses/create`

## 📖 Utilisation

### Interface Web
1. **Accédez au tableau de bord** pour voir toutes les licences
2. **Créez une nouvelle licence** avec les informations du client
3. **Gérez les licences existantes** (désactivation, prolongation, etc.)

### API REST
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
```

### Protection d'Application
```python
# Middleware global
from app.middleware.license_middleware import LicenseMiddleware
app.add_middleware(LicenseMiddleware, app)

# Protection de route spécifique
@app.get("/protected")
async def protected_route(request: Request):
    license_key = request.headers.get("X-License-Key")
    is_valid, message, info = validate_license_for_request(license_key)
    # ... logique de la route
```

## 🔧 Configuration Avancée

### Variables d'Environnement
```python
# app/services/licences.py
SECRET_KEY = "votre_cle_secrete_production"  # À changer en production
DEFAULT_LICENSE_DURATION = 365  # Durée par défaut en jours
```

### Middleware Personnalisé
```python
# Chemins exclus de la validation
exclude_paths = [
    "/",
    "/licenses/",
    "/static/",
    "/docs"
]
```

## 📊 Structure de Base de Données

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

## 🔐 Sécurité

### Recommandations
- ✅ Changez la `SECRET_KEY` en production
- ✅ Utilisez HTTPS en production
- ✅ Surveillez les logs d'utilisation
- ✅ Sauvegardez régulièrement la base

### Méthodes d'Authentification Client
1. **En-tête HTTP** : `X-License-Key: YOUR_KEY`
2. **Cookie** : `license_key=YOUR_KEY`
3. **Paramètre** : `?license_key=YOUR_KEY`

## 🧪 Tests

### Tests Automatiques
```bash
python test_licenses.py
```

### Tests Manuels
1. Créez une licence via l'interface web
2. Testez la validation via l'API
3. Vérifiez les statistiques d'utilisation
4. Testez la désactivation

## 📈 Monitoring

### Requêtes Utiles
```sql
-- Licences expirées
SELECT * FROM licenses WHERE expires_at < NOW() AND is_active = TRUE;

-- Licences expirant bientôt
SELECT * FROM licenses 
WHERE expires_at BETWEEN NOW() AND NOW() + INTERVAL '30 days'
AND is_active = TRUE;

-- Statistiques
SELECT 
    COUNT(*) as total,
    COUNT(CASE WHEN is_active THEN 1 END) as active,
    AVG(usage_count) as avg_usage
FROM licenses;
```

## 🐛 Dépannage

### Problèmes Courants

| Problème | Solution |
|----------|----------|
| Erreur PostgreSQL | Vérifiez `credentials.json` |
| Licence non trouvée | Vérifiez le format de la clé |
| Licence expirée | Prolongez ou créez une nouvelle |
| Limite atteinte | Augmentez la limite ou nouvelle licence |

### Logs
- Vérifiez les logs de l'application
- Utilisez le script de test pour diagnostiquer
- Consultez la documentation complète

## 📚 Documentation Complète

Pour plus de détails, consultez :
- [Documentation complète](docs/SYSTEME_LICENCES.md)
- [API Reference](docs/API_LICENCES.md)
- [Guide d'installation](docs/INSTALLATION_LICENCES.md)

## 🤝 Support

- **Tests** : `test_licenses.py`
- **Documentation** : `docs/SYSTEME_LICENCES.md`
- **Issues** : Créez une issue sur le repository

---

**Version** : 1.0.0  
**Dernière mise à jour** : Décembre 2024  
**Auteur** : Équipe Connecteur Sages 