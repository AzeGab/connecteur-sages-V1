# WARP.md

Ce fichier fournit des instructions à WARP (warp.dev) pour travailler avec le code de ce dépôt.

## Commandes de développement essentielles

### Démarrage de l'application
```powershell
# Activer l'environnement virtuel
.\.venv\Scripts\Activate.ps1

# Démarrer en mode développement
uvicorn app.main:app --reload

# Démarrer sur un port spécifique
uvicorn app.main:app --reload --port 8001
```

### Installation et configuration
```powershell
# Créer l'environnement virtuel
python -m venv .venv

# Activer l'environnement virtuel
.\.venv\Scripts\Activate.ps1

# Installer les dépendances
pip install -r requirements.txt

# Tester la connexion Supabase
python test_supabase_connection.py

# Lancer les tests de l'application
python test_app.py
```

### Tests et debug
```powershell
# Debug du système de synchronisation des heures
python scripts/debug_heures.py

# Mode debug (active les logs détaillés)
$env:DEBUG_CONNECTEUR = "true"
uvicorn app.main:app --reload

# Test de la connexion aux bases de données
python -c "from app.services.connex import check_connection_status; print(check_connection_status())"
```

### Configuration
```powershell
# Créer le fichier de configuration des identifiants
# Le fichier app/services/credentials.json est créé automatiquement via l'interface web
# Accéder à l'interface de configuration : http://localhost:8000/configuration

# Variables d'environnement importantes (fichier .env)
# SUPABASE_URL=https://rxqveiaawggfyeukpvyz.supabase.co
# SUPABASE_KEY=votre_cle_supabase
# SESSION_SECRET=votre_secret_session
```

## Architecture du projet

### Structure générale
Le Connecteur SAGES est une application de synchronisation bidirectionnelle entre des logiciels de gestion (Batigest/Codial) et BatiSimply. Il utilise PostgreSQL comme base tampon pour orchestrer les synchronisations.

### Flux de données principaux

#### 1. Synchronisation des chantiers
- **Batigest → PostgreSQL → BatiSimply** : Synchronise les chantiers depuis SQL Server
- **Codial → PostgreSQL → BatiSimply** : Synchronise les chantiers depuis HFSQL
- **Direction unique** : Chantiers remontent vers BatiSimply uniquement

#### 2. Synchronisation des heures
- **BatiSimply → PostgreSQL → Batigest/Codial** : Synchronise les heures saisies
- **Direction unique** : Heures descendent depuis BatiSimply uniquement
- **Système incrémental** : Évite les doublons grâce aux tables de mapping

### Architecture des packages

#### app/services/batigest/
- `__init__.py` - Interface publique du package
- `sqlserver_to_batisimply.py` - Synchronisation SQL Server → BatiSimply  
- `batisimply_to_sqlserver.py` - Synchronisation BatiSimply → SQL Server
- `utils.py` - Initialisation des tables PostgreSQL

#### app/services/codial/  
- `__init__.py` - Interface publique du package
- `hfsql_to_batisimply.py` - Synchronisation HFSQL → BatiSimply
- `batisimply_to_hfsql.py` - Synchronisation BatiSimply → HFSQL  
- `utils.py` - Initialisation des tables PostgreSQL

### Système de licences
L'application utilise un système de licences centralisé via Supabase :
- **Validation en temps réel** via API Supabase
- **Clé de test** : "Cobalt" (uniquement en mode debug)
- **Middleware de sécurité** : Bloque l'accès aux routes protégées
- **Pages dédiées** : Interface de gestion des licences

### Base de données PostgreSQL (tampon)

#### Tables principales pour Batigest :
- `batigest_chantiers` - Cache des chantiers Batigest
- `batigest_heures` - Cache des heures depuis BatiSimply
- `batigest_devis` - Cache des devis Batigest  
- `batigest_heures_map` - Mapping pour éviter les doublons

#### Tables principales pour Codial :
- `codial_chantiers` - Cache des chantiers Codial
- `codial_heures` - Cache des heures depuis BatiSimply
- `codial_heures_map` - Mapping pour éviter les doublons

### Interface web
- **Page principale** (`/`) : Boutons de synchronisation et statut
- **Configuration** (`/configuration`) : Sidebar avec 5 sections
  - Licence : Gestion des clés de licence
  - Bases de données : Configuration SQL Server/HFSQL/PostgreSQL
  - Mode données : Choix chantier/devis  
  - Logiciel : Sélection Batigest/Codial
  - Système : Outils de maintenance et debug
- **Licence expirée** (`/license-expired`) : Interface dédiée aux licences invalides

### Middleware et sécurité
- **LicenseMiddleware** : Vérification automatique des licences
- **SessionMiddleware** : Gestion des sessions utilisateur
- **Authentification BatiSimply** : Gestion des tokens OAuth2

## Spécificités techniques importantes

### Gestion des connexions de bases de données
- **SQL Server** : Utilise pyodbc avec ODBC Driver 17
- **HFSQL** : Utilise pypyodbc avec le pilote PC SOFT
- **PostgreSQL** : Utilise psycopg2 avec encodage UTF-8
- **Stockage des identifiants** : `app/services/credentials.json` (généré automatiquement)

### Authentification BatiSimply
- **Grant types supportés** : `password` et `client_credentials`
- **Configuration** : Section dédiée dans l'interface web
- **Retry automatique** : Système de retry avec backoff
- **Gestion des tokens** : Cache et renouvellement automatique

### Mode debug
- **Activation** : Variable d'environnement `DEBUG_CONNECTEUR=true` ou interface web
- **Fonctionnalités** : Capture des logs détaillés, super-clé "Cobalt"
- **Sortie** : Affichage dans l'interface web avec détails techniques

### Système de synchronisation incrémentale
- **Tables de mapping** : Évitent les doublons lors des synchronisations
- **Fenêtre temporelle** : Synchronisation des 180 derniers jours par défaut
- **Gestion des conflits** : Priorité à la dernière modification

## Commandes de maintenance

### Initialisation des tables PostgreSQL
```powershell
# Via l'interface web : /configuration > Système > Boutons d'initialisation
# Ou via l'API :
curl -X POST http://localhost:8000/init-batigest-tables
curl -X POST http://localhost:8000/init-codial-tables
```

### Diagnostic et debug
```powershell
# Script de diagnostic des heures
python scripts/debug_heures.py

# Vérification des connexions
python -c "from app.services.connex import check_connection_status; print(check_connection_status())"

# Test des licences
python -c "from app.services.license import is_license_valid; print(is_license_valid())"
```

### Synchronisations manuelles
Les synchronisations peuvent être lancées :
1. **Interface web** : Boutons sur la page principale
2. **API REST** : Routes `/api/sync-*` pour intégration
3. **Routes HTML** : Routes `/sync-*` pour interface web classique

## Points d'attention pour le développement

### Fichiers sensibles exclus de Git
- `app/services/credentials.json` - Configuration locale des identifiants
- `.env` - Variables d'environnement avec clés Supabase
- Dossiers temporaires : `build/`, `dist/`, `__pycache__/`

### Gestion des erreurs
- **Messages utilisateur** : Formatage automatique des erreurs techniques
- **Logs détaillés** : Mode debug avec capture complète
- **Fallback** : Gestion gracieuse des échecs de connexion

### Compatibilité Windows
- **Encodage** : UTF-8 avec gestion du BOM
- **Chemins** : Utilisation de `app.utils.paths` pour la compatibilité PyInstaller
- **Services Windows** : Support pour installation comme service

### Structure des réponses API
```json
{
  "success": true/false,
  "message": "Message descriptif",
  "timestamp": "2025-09-29T13:13:35Z"
}
```

### Normes de code
- **Style** : PEP 8 avec tolérance pour les noms français
- **Commentaires** : Français pour la documentation métier
- **Docstrings** : Français avec descriptions détaillées des paramètres
- **Imports** : Organisation par packages avec imports explicites

Le projet suit une architecture modulaire permettant d'ajouter facilement de nouveaux flux ou logiciels. La base tampon PostgreSQL centralise toutes les opérations et garantit la cohérence des données entre les systèmes.