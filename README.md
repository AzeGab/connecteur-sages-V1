# Connecteur SAGES

## Description
Le Connecteur SAGES est une application FastAPI qui sert d'interface entre différentes bases de données (SQL Server, PostgreSQL) et le service BatiSimply. Il permet la synchronisation des données de chantiers et des heures de travail entre ces différents systèmes.

## Prérequis

- Python 3.8+
- SQL Server (avec ODBC Driver 17)
- PostgreSQL
- Compte BatiSimply

## Installation

1. Cloner le repository :
```bash
git clone [URL_DU_REPO]
cd connecteur-sages-V1
```

2. Créer un environnement virtuel :
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

4. Configurer les variables d'environnement :

- Créer un fichier `.env` à la racine du projet
- Ajouter les variables nécessaires (voir section Configuration)

## Structure du Projet

```
app/
├── main.py              # Point d'entrée de l'application
├── routes/
│   └── form_routes.py   # Gestion des routes HTTP
├── services/
│   ├── connex.py        # Gestion des connexions aux bases de données
│   ├── chantier.py      # Gestion des chantiers
│   └── heures.py        # Gestion des heures
├── static/             # Fichiers statiques (CSS, JS)
└── templates/          # Templates HTML
```

## Fonctionnalités Détaillées

### 1. Gestion des Connexions (`services/connex.py`)

#### `connect_to_sqlserver(server, user, password, database)`

- **Description** : Établit une connexion à SQL Server
- **Paramètres** :

  - `server` : Nom ou adresse IP du serveur
  - `user` : Nom d'utilisateur
  - `password` : Mot de passe
  - `database` : Nom de la base de données
- **Retour** : Objet de connexion ou None en cas d'échec

#### `connect_to_postgres(host, user, password, database, port="5432")`

- **Description** : Établit une connexion à PostgreSQL
- **Paramètres** :

  - `host` : Nom d'hôte ou adresse IP
  - `user` : Nom d'utilisateur
  - `password` : Mot de passe
  - `database` : Nom de la base de données
  - `port` : Port de connexion (défaut: 5432)
- **Retour** : Objet de connexion ou None en cas d'échec

#### `recup_batisimply_token()`

- **Description** : Récupère le token d'authentification BatiSimply
- **Retour** : Token d'accès ou None en cas d'échec

### 2. Gestion des Chantiers (`services/chantier.py`)

#### `transfer_chantiers()`

- **Description** : Transfère les chantiers de SQL Server vers PostgreSQL
- **Processus** :

  1. Vérifie les identifiants de connexion
  2. Établit les connexions aux bases
  3. Récupère les chantiers depuis SQL Server
  4. Les insère dans PostgreSQL
  5. Gère les doublons avec ON CONFLICT
- **Retour** : (bool, str) - Succès et message

#### `transfer_chantiers_vers_batisimply()`

- **Description** : Transfère les chantiers vers BatiSimply
- **Processus** :

  1. Récupère le token d'authentification
  2. Vérifie les identifiants PostgreSQL
  3. Récupère les chantiers non synchronisés
  4. Les envoie à l'API BatiSimply
  5. Met à jour le statut de synchronisation
- **Retour** : bool - Succès ou échec

### 3. Gestion des Heures (`services/heures.py`)

#### `transfer_heures_to_postgres()`

- **Description** : Transfère les heures depuis BatiSimply vers PostgreSQL
- **Processus** :

  1. Récupère le token BatiSimply
  2. Établit la connexion PostgreSQL
  3. Récupère les heures depuis l'API
  4. Les insère dans PostgreSQL
- **Retour** : bool - Succès ou échec

#### `transfer_heures_to_sqlserver()`

- **Description** : Transfère les heures de PostgreSQL vers SQL Server
- **Processus** :

  1. Vérifie les connexions aux deux bases
  2. Récupère les heures validées non synchronisées
  3. Les transfère vers SQL Server
  4. Met à jour le statut de synchronisation
- **Retour** : bool - Succès ou échec

## Routes API (`routes/form_routes.py`)

### GET `/`

- **Description** : Page principale avec formulaire de connexion
- **Retour** : Template HTML avec statut des connexions

### POST `/connect-sqlserver`

- **Description** : Teste et sauvegarde la connexion SQL Server
- **Paramètres** : server, user, password, database
- **Retour** : Template HTML avec message de résultat

### POST `/connect-postgres`

- **Description** : Teste et sauvegarde la connexion PostgreSQL
- **Paramètres** : host, user, password, database, port
- **Retour** : Template HTML avec message de résultat

### POST `/transfer`

- **Description** : Lance le transfert des données
- **Retour** : Template HTML avec résultat du transfert

### POST `/transfer-batisimply`

- **Description** : Transfère les chantiers vers BatiSimply
- **Retour** : Template HTML avec résultat du transfert

### POST `/recup-heures`

- **Description** : Récupère les heures depuis BatiSimply
- **Retour** : Template HTML avec résultat de la récupération

### POST `/update-code-projet`

- **Description** : Met à jour les codes projet
- **Retour** : Template HTML avec résultat de la mise à jour

## Utilisation

1. Démarrer l'application :
```bash
uvicorn app.main:app --reload
```

2. Accéder à l'interface web :
```
http://localhost:8000
```

3. Suivre le processus de synchronisation :

   - Configurer les connexions aux bases de données
   - Lancer les transferts de données
   - Vérifier les résultats dans l'interface

## Sécurité

- Les identifiants sont stockés localement dans un fichier JSON
- Les connexions utilisent des certificats SSL
- Les tokens BatiSimply sont gérés de manière sécurisée

## Dépendances

Voir `requirements.txt` pour la liste complète des dépendances.

## Support

dev2@groupe-sages.fr - dev3@groupe-sages.fr

 