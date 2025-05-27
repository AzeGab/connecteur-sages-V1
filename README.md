# Connecteur SAGES

## Description
Le Connecteur SAGES est une application FastAPI qui sert d'interface entre SQL Server (Batigest), PostgreSQL (buffer) et l'API BatiSimply. Il permet la synchronisation bidirectionnelle des données de chantiers et des heures de travail entre ces différents systèmes.

## Prérequis
- Python 3.8+
- SQL Server (avec ODBC Driver 17)
- PostgreSQL 14+
- Compte BatiSimply (accès API)

## Installation

1. Cloner le repository :
```bash
git clone [URL_DU_REPO]
cd connecteur-sages-V1
```

2. Créer un environnement virtuel :
```bash
python -m venv venv
# Linux/Mac
source venv/bin/activate
# Windows
venv\Scripts\activate
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

4. (Optionnel) Configurer un fichier `.env` si besoin de variables d'environnement spécifiques.

## Structure du Projet

```
app/
├── main.py              # Point d'entrée FastAPI
├── routes/
│   └── form_routes.py   # Routes HTTP et synchronisation
├── services/
│   ├── connex.py        # Connexions aux bases de données
│   ├── chantier.py      # Logique métier chantiers & synchronisation
│   └── heures.py        # Logique métier heures
├── static/              # Fichiers statiques (logo, CSS)
└── templates/           # Templates HTML (interface utilisateur)
```

## Fonctionnalités principales
- Connexion et test aux bases SQL Server et PostgreSQL
- Synchronisation bidirectionnelle des chantiers entre Batigest, PostgreSQL et BatiSimply
- Transfert des heures entre BatiSimply, PostgreSQL et Batigest
- Interface web moderne (Bootstrap) pour piloter les synchronisations
- Initialisation automatique de la table PostgreSQL (ajout des colonnes de suivi)
- Gestion des erreurs et logs détaillés

## Routes principales

- **GET /** : Page principale (formulaire de connexion, boutons d'action)
- **POST /connect-sqlserver** : Connexion à SQL Server
- **POST /connect-postgres** : Connexion à PostgreSQL
- **POST /transfer** : Transfert des chantiers SQL Server → PostgreSQL
- **POST /transfer-batisimply** : Transfert des chantiers PostgreSQL → BatiSimply
- **POST /recup-heures** : Récupération des heures depuis BatiSimply
- **POST /update-code-projet** : Mise à jour des codes projet dans PostgreSQL
- **POST /transfer-heure-batigest** : Envoi des heures PostgreSQL → Batigest
- **POST /sync-batigest-to-batisimply** : Synchronisation Batigest → PostgreSQL → BatiSimply
- **POST /sync-batisimply-to-batigest** : Synchronisation BatiSimply → PostgreSQL → Batigest
- **POST /init-table** : Initialisation de la table PostgreSQL

## Synchronisation bidirectionnelle

- **Batigest → PostgreSQL → BatiSimply** :
  - Les modifications dans SQL Server sont propagées vers PostgreSQL puis vers BatiSimply.
  - Les dates de dernière modification sont suivies pour éviter les conflits.
- **Batisimply → PostgreSQL → Batigest** :
  - Les modifications dans BatiSimply sont récupérées via l'API, stockées dans PostgreSQL, puis envoyées vers Batigest.
  - Les conflits sont gérés par la date de modification la plus récente.

## Utilisation

1. Lancer l'application :
```bash
uvicorn app.main:app --reload
```
2. Accéder à l'interface :
```
http://localhost:8000
```
3. Configurer les connexions aux bases de données
4. Utiliser les boutons pour transférer ou synchroniser les données

## Bonnes pratiques
- Toujours initialiser la table PostgreSQL après une première installation ou migration (bouton dédié)
- Vérifier les logs pour tout problème de connexion ou de synchronisation
- Les identifiants de connexion sont stockés localement dans `app/services/credentials.json` (ajouté au `.gitignore`)

## Dépendances
Voir `requirements.txt` pour la liste complète.

## Support
Pour toute question ou bug, contactez :
- dev2@groupe-sages.fr
- dev3@groupe-sages.fr

 