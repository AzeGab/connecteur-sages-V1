# Installation PostgreSQL pour le système de licences

## Prérequis

Le système de licences nécessite PostgreSQL pour stocker les informations des licences.

## Installation PostgreSQL sur Windows

### Option 1: Installation via l'installateur officiel

1. **Télécharger PostgreSQL**
   - Allez sur https://www.postgresql.org/download/windows/
   - Téléchargez la dernière version stable (ex: PostgreSQL 15.x)

2. **Installer PostgreSQL**
   - Exécutez l'installateur téléchargé
   - Choisissez le répertoire d'installation (par défaut: `C:\Program Files\PostgreSQL\15\`)
   - Définissez un mot de passe pour l'utilisateur `postgres` (à retenir !)
   - Gardez le port par défaut (5432)
   - Laissez les autres options par défaut

3. **Vérifier l'installation**
   - PostgreSQL devrait démarrer automatiquement
   - Vous pouvez vérifier dans les services Windows

### Option 2: Installation via Chocolatey (si installé)

```powershell
choco install postgresql
```

### Option 3: Installation via Docker

```bash
docker run --name postgres-licenses -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=connecteur_licenses -p 5432:5432 -d postgres:15
```

## Configuration après installation

### 1. Créer la base de données

Si vous n'avez pas utilisé Docker, créez la base de données :

```sql
-- Se connecter à PostgreSQL
psql -U postgres

-- Créer la base de données
CREATE DATABASE connecteur_licenses;

-- Vérifier que la base existe
\l

-- Quitter
\q
```

### 2. Configurer le projet

Exécutez le script de configuration :

```bash
python configure_postgresql.py
```

Le script vous demandera :
- **Host**: `localhost` (par défaut)
- **Port**: `5432` (par défaut)
- **Utilisateur**: `postgres` (par défaut)
- **Mot de passe**: Le mot de passe défini lors de l'installation
- **Base de données**: `connecteur_licenses`

### 3. Vérifier la configuration

Le script va automatiquement :
- Tester la connexion PostgreSQL
- Créer la table `licenses`
- Optionnellement créer une licence d'exemple

## Dépannage

### Erreur de connexion

Si vous obtenez une erreur de connexion :

1. **Vérifiez que PostgreSQL est démarré**
   ```powershell
   # Vérifier le service
   Get-Service postgresql*
   
   # Démarrer le service si nécessaire
   Start-Service postgresql*
   ```

2. **Vérifiez les identifiants**
   - Le mot de passe de l'utilisateur `postgres`
   - Le nom de la base de données

3. **Vérifiez le port**
   - Par défaut : 5432
   - Vérifiez qu'aucun autre service n'utilise ce port

### Erreur de permissions

Si vous obtenez une erreur de permissions :

```sql
-- Se connecter en tant qu'administrateur PostgreSQL
psql -U postgres

-- Donner tous les droits à l'utilisateur postgres sur la base
GRANT ALL PRIVILEGES ON DATABASE connecteur_licenses TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
```

## Test de la configuration

Après la configuration, testez le système :

```bash
# Démarrer l'application
python -m uvicorn app.main:app --reload

# Ouvrir dans le navigateur
http://localhost:8000/licenses/
```

## Ressources utiles

- [Documentation PostgreSQL](https://www.postgresql.org/docs/)
- [pgAdmin (interface graphique)](https://www.pgadmin.org/)
- [DBeaver (client universel)](https://dbeaver.io/) 