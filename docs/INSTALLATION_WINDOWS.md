## Guide d'installation complète (Windows) – Connecteur SAGES

Ce guide explique pas à pas comment installer et configurer l'application Connecteur SAGES sur un nouveau poste Windows. Il est volontairement détaillé et vulgarisé pour convenir à tous les profils.

### Public visé
- Administrateurs système et techniciens
- Chefs de projet / MOA
- Développeurs

---

## 1) Pré-requis système

- **Système**: Windows 10 ou plus récent
- **Droits**: Compte avec droits administrateur (pour pilotes et services)
- **Réseau**: Accès Internet (API BatiSimply, validation des licences)
- **Bases**:
  - SQL Server (Batigest) accessible et identifiants valides
  - PostgreSQL 14+ (base tampon) accessible et identifiants valides

### Logiciels et composants requis
- **Python 3.11.x** (Windows x64)
- **ODBC Driver 17 for SQL Server** (indispensable pour pyodbc)
- **Git** (facultatif, si vous déployez depuis GitHub)

Liens utiles (à ouvrir dans votre navigateur):
- Microsoft - ODBC Driver 17: `https://learn.microsoft.com/fr-fr/sql/connect/odbc/download-odbc-driver-for-sql-server`
- Python 3.11: `https://www.python.org/downloads/windows/`

---

## 2) Récupération du projet

### Option A – Cloner depuis Git (recommandé)
```powershell
git clone https://github.com/AzeGab/connecteur-sages-V1.git
cd connecteur-sages-V1
```

### Option B – Archive ZIP
1. Télécharger l'archive du dépôt GitHub
2. Extraire l'archive dans un dossier, par exemple `C:\ConnecteurSages`

---

## 3) Création de l'environnement Python (venv)

Dans le dossier du projet:
```powershell
python -m venv venv
".\venv\Scripts\Activate.ps1"
```

Si l'activation est bloquée, lancer PowerShell en administrateur et exécuter:
```powershell
Set-ExecutionPolicy RemoteSigned
```

---

## 4) Installation des dépendances

Avec l'environnement activé:
```powershell
pip install --upgrade pip
pip install -r requirements.txt
pip install -r app\requirements.txt
```

Vérifier que `uvicorn`, `fastapi`, `pyodbc`, `psycopg2` sont bien installés:
```powershell
pip list
```

### Problèmes fréquents
- Erreur ODBC: installez "ODBC Driver 17 for SQL Server" (lien plus haut)
- Erreur Visual C++: installez les **Microsoft Build Tools** si nécessaire

---

## 5) Variables d'environnement (.env)

Créez un fichier `.env` à la racine du projet (copiez `env.example` si disponible) et complétez:

```dotenv
# BatiSimply (SSO Keycloak)
BATISIMPLY_SSO_URL=https://sso.staging.batisimply.fr/auth/realms/jhipster/protocol/openid-connect/token
BATISIMPLY_CLIENT_ID=...       
BATISIMPLY_CLIENT_SECRET=...
BATISIMPLY_USERNAME=...
BATISIMPLY_PASSWORD=...
BATISIMPLY_GRANT_TYPE=password

# Supabase (validation des licences)
SUPABASE_URL=https://rxqveiaawggfyeukpvyz.supabase.co
SUPABASE_KEY=...

# Licence manager (optionnel – service centralisé)
LICENSE_API_BASE_URL=
LICENSE_API_KEY=
LICENSE_HEARTBEAT_ENABLED=false

# App
HOST=0.0.0.0
PORT=8000
SESSION_SECRET=change-me
```

> Important: conservez ce fichier **privé** (ne pas le versionner).

---

## 6) Démarrage de l'application

Toujours dans le répertoire du projet, venv activé:
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Puis ouvrez le navigateur: `http://localhost:8000`

### Vérifications rapides
- Santé API: `http://localhost:8000/health` doit retourner `{"status":"healthy"}`
- Statique chargé: la page d'accueil s'affiche

---

## 7) Configuration dans l'interface

1. Accéder à `http://localhost:8000/login`
   - Mot de passe par défaut affiché dans l'UI (ex: "gumgum")

2. Aller dans "Configuration"
   - **Licence**: collez la clé fournie par le Groupe SAGES
     - La clé est validée en temps réel (Supabase ou service central si configuré)
   - **Bases de données**:
     - SQL Server (Batigest): serveur, utilisateur, mot de passe, base
     - PostgreSQL (tampon): host, port, utilisateur, mot de passe, base
   - **Mode de données**: `chantier` ou `devis`
   - **Logiciel principal**: `batigest` ou `codial`

3. Tester les connexions via les boutons dédiés
4. Sauvegarder

> Astuce: les paramètres sont enregistrés localement dans `app/services/credentials.json` (non versionné).

---

## 8) Premières synchronisations

Depuis la page d'accueil:
- Bouton "Batigest → Batisimply":
  - Si mode "chantier": transfère chantiers SQL Server → PostgreSQL → BatiSimply
  - Si mode "devis": transfère devis SQL Server → PostgreSQL → BatiSimply

- Bouton "Batisimply → Batigest":
  - Récupère les heures depuis BatiSimply → PostgreSQL
  - Met à jour les codes projets
  - Envoie les heures validées vers Batigest (table `SuiviMO`)

### Endpoints utiles (via UI ou API)
- POST `/transfer` : SQL Server → PostgreSQL (chantiers)
- POST `/transfer-batisimply` : PostgreSQL → BatiSimply (chantiers)
- POST `/recup-heures` : BatiSimply → PostgreSQL (heures)
- POST `/transfer-heure-batigest` : PostgreSQL → Batigest (heures)
- POST `/sync-batigest-to-batisimply`
- POST `/sync-batisimply-to-batigest`
- POST `/init-table` : initialise la table PostgreSQL (colonne `sync`, etc.)

---

### 8.1) Initialiser le mapping des salariés (obligatoire pour la synchro des heures)

Pour que l'envoi des heures vers Batigest (SQL Server) fonctionne, le connecteur doit retrouver dans la table `Salarie` le salarié correspondant à l'utilisateur BatiSimply. Le champ utilisé est `Salarie.codebs`, qui doit contenir l'UUID BatiSimply de l'utilisateur.

Sans ce mapping, aucune heure ne sera insérée dans `SuiviMO`.

Étapes recommandées (one-shot à l'installation):

1. Vérifier que la configuration BatiSimply est renseignée (onglet Configuration → Batisimply) et que le token est récupérable.
2. Récupérer la liste des utilisateurs depuis l'API BatiSimply (consultez la documentation de l'API pour l'endpoint « users/employees »; vous avez besoin a minima de l'`id` et éventuellement de l'`email`/nom).
3. Faire correspondre chaque utilisateur BatiSimply à un salarié côté Batigest (table `Salarie`) via l'email ou le nom.
4. Renseigner `Salarie.codebs` avec l'UUID BatiSimply correspondant.

Requêtes utiles (SQL Server):

```sql
-- Vérifier les salariés non mappés
SELECT TOP 50 Code, Nom, codebs
FROM Salarie
WHERE codebs IS NULL OR codebs = ''
ORDER BY Nom;

-- Exemple de mise à jour manuelle (remplacez par vos valeurs)
UPDATE Salarie
SET codebs = 'd7b4ba33-33db-4a1c-80db-e7645828795b'
WHERE Code = 'JP';
```

Conseils:
- Gérez les homonymes avec prudence (privilégier l'email si disponible).
- Conservez un export (CSV) des correspondances réalisées.
- Cette étape est à faire une seule fois; mettez-la à jour lors d'une arrivée/départ.

Note: Une automatisation de ce mapping (appel API BatiSimply → mise à jour `Salarie.codebs`) pourra être ajoutée ultérieurement sous forme d'outil/endpoint dédié.

---

## 9) Déploiement simplifié (installateur automatisé)

Le script `installer.py` peut automatiser l’installation (Windows):
1. Installe PostgreSQL (mode silencieux) dans `C:\ConnecteurBuffer\PostgreSQL`
2. Configure un Python embarqué
3. Initialise la base (script `install_assets/initdb.sql` si présent)
4. Copie l’application et installe les dépendances
5. Crée un raccourci de démarrage

Exécution:
```powershell
python installer.py
```

> Remarque: nécessite des droits administrateur et les fichiers dans `install_assets/`.

---

## 10) Bonnes pratiques & maintenance

- Conserver `.env` et `credentials.json` en sécurité
- Sauvegarder la base PostgreSQL tampon si elle stocke des historiques utiles
- Mettre à jour régulièrement:
  ```powershell
  git pull
  pip install -r requirements.txt
  pip install -r app\requirements.txt
  ```
- Les logs s’affichent dans la console Uvicorn

---

## 11) Dépannage (FAQ)

- "No module named uvicorn"
  - Refaire `pip install -r requirements.txt` et `app/requirements.txt`
  - Vérifier que le venv est bien activé

- "Data source name not found" (ODBC)
  - Installer l’ODBC Driver 17 pour SQL Server

- "Connection refused" vers SQL Server / PostgreSQL
  - Vérifier le host, le port, le firewall Windows et les identifiants

- Licence invalide / expirée
  - Vérifier `SUPABASE_KEY` ou le service de licence
  - Réessayer via le bouton "Actualiser" dans la configuration

- Problèmes de droits PowerShell
  - `Set-ExecutionPolicy RemoteSigned` (en admin)

---

## 12) Désinstallation

- Arrêter Uvicorn (CTRL+C)
- Supprimer le dossier du projet si installé manuellement
- Si installateur utilisé, supprimer `C:\ConnecteurBuffer` (et PostgreSQL si dédié)

---

## 13) Références utiles

- README du projet
- `docs/MIGRATION_SUPABASE.md` et `SUPABASE_SETUP.md`
- `docs/INSTALLATION_BATISIMPLY.md`
- `app/services/connex.py` (connexions + credentials + token BatiSimply)
- `app/routes/form_routes.py` (routes UI + configuration)

---

## 14) Support

En cas de blocage, contactez le support SAGES:
- dev2@groupe-sages.fr
- dev3@groupe-sages.fr
- support@groupe-sages.fr (licences)


