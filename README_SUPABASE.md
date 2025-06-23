# Connecteur SAGES - Version Supabase

Ce projet utilise **Supabase** comme base de données pour le système de licences, offrant une solution cloud moderne et scalable.

## 🚀 Démarrage Rapide

### 1. Installation des dépendances

```bash
# Installer les dépendances Supabase
pip install supabase python-dotenv

# Ou utiliser le script de configuration
python setup_supabase.py
```

### 2. Configuration Supabase

1. **Créer un compte** sur [supabase.com](https://supabase.com)
2. **Créer un projet** et récupérer vos clés API
3. **Configurer les variables d'environnement** :

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

### 3. Créer la table de licences

Exécutez ce script SQL dans l'interface Supabase :

```sql
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

-- Index pour les performances
CREATE INDEX IF NOT EXISTS idx_licenses_license_key ON licenses(license_key);
CREATE INDEX IF NOT EXISTS idx_licenses_is_active ON licenses(is_active);
CREATE INDEX IF NOT EXISTS idx_licenses_expires_at ON licenses(expires_at);

-- Sécurité RLS
ALTER TABLE licenses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access" ON licenses FOR SELECT USING (true);
CREATE POLICY "Allow public insert" ON licenses FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update" ON licenses FOR UPDATE USING (true);
```

### 4. Lancer l'application

```bash
# Démarrer l'application
python -m uvicorn app.main:app --reload

# Ou utiliser le script principal
python app/main.py
```

## 📊 Interface de Gestion

Accédez à l'interface de gestion des licences :
- **URL** : http://localhost:8000/licenses/
- **Création** : http://localhost:8000/licenses/create
- **Configuration** : http://localhost:8000/licenses/setup

## 🔧 Scripts Utiles

### Configuration automatique

```bash
# Configuration complète
python setup_supabase.py

# Options disponibles :
# 1. Installer les dépendances
# 2. Créer un fichier .env
# 3. Configurer Supabase
# 4. Configuration complète
```

### Tests

```bash
# Tests complets
python test_supabase.py

# Test de connexion uniquement
python -c "from app.services.supabase_licences import get_supabase_client; print('✅ OK' if get_supabase_client() else '❌ Erreur')"
```

### Migration depuis PostgreSQL

```bash
# Migrer les données existantes
python migrate_to_supabase.py

# Options disponibles :
# 1. Créer une sauvegarde PostgreSQL
# 2. Migrer toutes les licences
# 3. Vérifier la migration
# 4. Migration complète
```

## 🔐 API REST

### Créer une licence

```bash
curl -X POST "http://localhost:8000/licenses/api/create" \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Client Test",
    "client_email": "test@example.com",
    "company_name": "Entreprise Test",
    "duration_days": 365,
    "max_usage": 1000
  }'
```

### Valider une licence

```bash
curl "http://localhost:8000/licenses/api/validate/YOUR-LICENSE-KEY"
```

### Lister toutes les licences

```bash
curl "http://localhost:8000/licenses/api/list"
```

### Informations d'une licence

```bash
curl "http://localhost:8000/licenses/api/info/YOUR-LICENSE-KEY"
```

### Désactiver une licence

```bash
curl -X POST "http://localhost:8000/licenses/api/deactivate/YOUR-LICENSE-KEY"
```

## 🛡️ Middleware de Sécurité

Le middleware valide automatiquement les licences. Pour l'activer :

```python
# Dans app/main.py, décommentez cette ligne :
add_license_middleware(app)
```

### Méthodes d'authentification

Le middleware accepte les clés de licence via :

1. **Paramètres de requête** : `?license_key=VOTRE_CLE`
2. **Headers HTTP** : `X-License-Key: VOTRE_CLE`
3. **Cookies** : `license_key=VOTRE_CLE`

### Chemins exclus

Les chemins suivants sont exclus de la validation :
- `/licenses/` (interface de gestion)
- `/static/` (fichiers statiques)
- `/docs/` (documentation FastAPI)
- `/health` (endpoint de santé)

## 📈 Avantages de Supabase

### ✅ Avantages

- **Hébergement cloud** : Pas de serveur à gérer
- **Interface web** : Gestion intuitive des données
- **API automatique** : REST API générée automatiquement
- **Authentification** : Système d'auth intégré (optionnel)
- **Sauvegarde** : Sauvegardes automatiques
- **Scalabilité** : Mise à l'échelle automatique
- **Gratuit** : Plan gratuit généreux
- **PostgreSQL** : Base de données robuste

### ⚠️ Limitations

- **Dépendance internet** : Nécessite une connexion
- **Limites gratuites** : 500MB de base, 2GB de bande passante
- **Latence** : Légère latence réseau
- **Vendor lock-in** : Dépendance à Supabase

## 🔧 Dépannage

### Erreur de connexion

```bash
# Vérifier les variables d'environnement
echo $SUPABASE_URL
echo $SUPABASE_KEY

# Tester la connexion
python -c "from app.services.supabase_licences import get_supabase_client; print(get_supabase_client())"
```

### Erreur de table

```sql
-- Vérifier que la table existe
SELECT * FROM licenses LIMIT 1;

-- Recréer si nécessaire
DROP TABLE IF EXISTS licenses;
-- Puis exécuter le script de création
```

### Erreur de permissions

```sql
-- Vérifier les politiques RLS
SELECT * FROM pg_policies WHERE tablename = 'licenses';

-- Recréer les politiques
DROP POLICY IF EXISTS "Allow public read access" ON licenses;
-- Puis recréer
```

## 📚 Documentation

- **Supabase** : [supabase.com/docs](https://supabase.com/docs)
- **Migration** : [docs/MIGRATION_SUPABASE.md](docs/MIGRATION_SUPABASE.md)
- **Système de licences** : [docs/SYSTEME_LICENCES.md](docs/SYSTEME_LICENCES.md)

## 🤝 Support

- **Issues** : Créez une issue sur GitHub
- **Documentation** : Consultez les fichiers dans `docs/`
- **Tests** : Utilisez `python test_supabase.py`

## 🔄 Migration depuis PostgreSQL

Si vous migrez depuis PostgreSQL local :

1. **Sauvegarder** : `python migrate_to_supabase.py`
2. **Configurer** : Variables d'environnement Supabase
3. **Migrer** : Exécuter la migration
4. **Tester** : Vérifier le fonctionnement
5. **Basculer** : Utiliser Supabase en production

## 📊 Monitoring

### Interface Supabase

- **Table Editor** : Visualiser les données
- **Logs** : Voir les requêtes
- **Analytics** : Statistiques d'utilisation

### Application

```python
# Vérifier le statut
from app.services.supabase_licences import get_all_licenses

licenses = get_all_licenses()
active = [l for l in licenses if l['is_active']]
print(f"Licences actives : {len(active)}/{len(licenses)}")
```

---

**🎉 Votre système de licences est maintenant opérationnel avec Supabase !** 