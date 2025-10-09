# Migration vers Supabase - Système de Licences

Ce document explique comment migrer le système de licences de PostgreSQL local vers Supabase.

## 🚀 Pourquoi Supabase ?

Supabase est une alternative moderne à PostgreSQL qui offre :

- **Base de données PostgreSQL** en arrière-plan
- **Interface web intuitive** pour gérer les données
- **API REST automatique** pour toutes les tables
- **Authentification intégrée** (optionnel)
- **Hébergement cloud** sans configuration serveur
- **Gratuit** pour les petits projets
- **Scalabilité** automatique

## 📋 Prérequis

1. **Compte Supabase** : Créez un compte sur [supabase.com](https://supabase.com)
2. **Projet Supabase** : Créez un nouveau projet
3. **Python 3.8+** : Assurez-vous d'avoir Python installé

## 🔧 Installation

### 1. Installer les dépendances

```bash
# Installer les nouvelles dépendances
pip install supabase python-dotenv

# Ou utiliser le script de configuration
python setup_supabase.py
```

### 2. Configuration des variables d'environnement

Créez un fichier `.env` à la racine du projet :

```env
# Configuration Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Autres variables
SECRET_KEY=connecteur-sages-v1-secret-key-2024
```

**Comment obtenir vos clés Supabase :**
1. Allez dans votre projet Supabase
2. Cliquez sur "Settings" → "API"
3. Copiez l'URL et la clé "anon public"

### 3. Créer la table dans Supabase

Exécutez ce script SQL dans l'interface SQL de Supabase :

```sql
-- Créer la table licenses
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

-- Créer les index pour les performances
CREATE INDEX IF NOT EXISTS idx_licenses_license_key ON licenses(license_key);
CREATE INDEX IF NOT EXISTS idx_licenses_is_active ON licenses(is_active);
CREATE INDEX IF NOT EXISTS idx_licenses_expires_at ON licenses(expires_at);

-- Activer Row Level Security (RLS) pour la sécurité
ALTER TABLE licenses ENABLE ROW LEVEL SECURITY;

-- Créer les politiques d'accès
CREATE POLICY "Allow public read access" ON licenses
    FOR SELECT USING (true);

CREATE POLICY "Allow public insert" ON licenses
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public update" ON licenses
    FOR UPDATE USING (true);
```

## 🔄 Migration des données

### Option 1 : Migration automatique (recommandée)

Utilisez le script de migration :

```bash
python migrate_to_supabase.py
```

### Option 2 : Migration manuelle

1. **Exporter les données PostgreSQL** :
```sql
COPY licenses TO '/tmp/licenses.csv' WITH CSV HEADER;
```

2. **Importer dans Supabase** :
   - Allez dans l'interface Supabase
   - Cliquez sur "Table Editor" → "licenses"
   - Cliquez sur "Import" et sélectionnez votre fichier CSV

## 🧪 Tests

### Test de connexion

```bash
python test_supabase.py
```

### Test complet

```bash
# Option 1 : Tests complets
python test_supabase.py

# Option 2 : Test de connexion uniquement
python -c "from app.services.supabase_licences import get_supabase_client; print('✅ Connexion OK' if get_supabase_client() else '❌ Échec connexion')"
```

## 📊 Différences avec PostgreSQL local

| Fonctionnalité | PostgreSQL Local | Supabase |
|----------------|------------------|----------|
| **Installation** | Complexe | Simple |
| **Hébergement** | Local/serveur | Cloud |
| **Interface** | pgAdmin/psql | Interface web |
| **API** | Manuel | Automatique |
| **Authentification** | Manuel | Intégrée |
| **Sauvegarde** | Manuel | Automatique |
| **Coût** | Serveur | Gratuit (limité) |
| **Scalabilité** | Manuel | Automatique |

## 🔐 Sécurité

### Row Level Security (RLS)

Supabase utilise RLS pour sécuriser les données. Les politiques créées permettent :

- **Lecture publique** : Toutes les licences peuvent être lues
- **Insertion publique** : Nouvelles licences peuvent être créées
- **Mise à jour publique** : Licences peuvent être modifiées

### Variables d'environnement

⚠️ **Important** : Ne committez jamais vos clés Supabase dans Git !

```bash
# ✅ Bon : Utiliser un fichier .env (dans .gitignore)
SUPABASE_KEY=your-secret-key

# ❌ Mauvais : Clés en dur dans le code
SUPABASE_KEY = "your-secret-key"
```

## 🚀 Utilisation

### Interface web

Accédez à l'interface de gestion :
```
http://localhost:8000/licenses/
```

### API REST

```bash
# Créer une licence
curl -X POST "http://localhost:8000/licenses/api/create" \
  -H "Content-Type: application/json" \
  -d '{"client_name":"Test","client_email":"test@example.com"}'

# Valider une licence
curl "http://localhost:8000/licenses/api/validate/YOUR-LICENSE-KEY"

# Lister toutes les licences
curl "http://localhost:8000/licenses/api/list"
```

### Middleware

Le middleware valide automatiquement les licences :

```python
# Dans votre application FastAPI
from app.middleware.license_middleware import add_license_middleware

app = FastAPI()
add_license_middleware(app)
```

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

-- Recréer la table si nécessaire
DROP TABLE IF EXISTS licenses;
-- Puis exécuter le script de création
```

### Erreur de permissions

```sql
-- Vérifier les politiques RLS
SELECT * FROM pg_policies WHERE tablename = 'licenses';

-- Recréer les politiques si nécessaire
DROP POLICY IF EXISTS "Allow public read access" ON licenses;
-- Puis recréer les politiques
```

## 📈 Monitoring

### Interface Supabase

- **Table Editor** : Visualiser et modifier les données
- **Logs** : Voir les requêtes et erreurs
- **Analytics** : Statistiques d'utilisation

### Application

```python
# Vérifier le statut des licences
from app.services.supabase_licences import get_all_licenses

licenses = get_all_licenses()
active_licenses = [l for l in licenses if l['is_active']]
print(f"Licences actives : {len(active_licenses)}")
```

## 🔄 Rollback

Si vous devez revenir à PostgreSQL local :

1. **Sauvegarder les données Supabase** :
```sql
COPY licenses TO '/tmp/supabase_licenses.csv' WITH CSV HEADER;
```

2. **Restaurer dans PostgreSQL local** :
```sql
COPY licenses FROM '/tmp/supabase_licenses.csv' WITH CSV HEADER;
```

3. **Modifier les imports** dans le code pour utiliser `app.services.licences` au lieu de `app.services.supabase_licences`

## 📞 Support

- **Documentation Supabase** : [supabase.com/docs](https://supabase.com/docs)
- **Community** : [github.com/supabase/supabase](https://github.com/supabase/supabase)
- **Discord** : [discord.supabase.com](https://discord.supabase.com)

## ✅ Checklist de migration

- [ ] Compte Supabase créé
- [ ] Projet Supabase créé
- [ ] Variables d'environnement configurées
- [ ] Table `licenses` créée
- [ ] Politiques RLS configurées
- [ ] Dépendances installées
- [ ] Tests passés
- [ ] Données migrées (si applicable)
- [ ] Application testée
- [ ] Documentation mise à jour 