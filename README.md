# Connecteur SAGES

## Description

Le Connecteur SAGES est une application FastAPI permettant la synchronisation bidirectionnelle des données de chantiers et d'heures entre Batigest (SQL Server), PostgreSQL (base tampon) et BatiSimply (API). Il facilite la gestion, le suivi et la cohérence des données entre ces systèmes métiers du bâtiment.

## Architecture

- **FastAPI** : Serveur web et API
- **SQL Server** : Base de données Batigest (source principale des chantiers et heures vendues)
- **PostgreSQL** : Base tampon pour la synchronisation et le suivi des modifications
- **BatiSimply** : Plateforme SaaS, synchronisation via API REST

## Flux de synchronisation

- **Batigest → PostgreSQL → BatiSimply** :
  - Les chantiers et leurs heures vendues (issues des devis) sont extraits de Batigest, stockés dans PostgreSQL, puis synchronisés vers BatiSimply.
- **BatiSimply → PostgreSQL → Batigest** :
  - Les modifications de chantiers dans BatiSimply sont récupérées via l'API, stockées dans PostgreSQL, puis répercutées dans Batigest.
- **Heures réalisées** :
  - Les heures saisies dans BatiSimply peuvent être importées dans Batigest via la table `batigest_heures` (flux optionnel, non activé par défaut).

## Structure du projet

```
app/
├── main.py                # Point d'entrée FastAPI
├── requirements.txt       # Dépendances Python
├── services/              # Logique métier (transferts, connexions, synchronisation)
│   ├── chantier.py        # Fonctions de synchronisation des chantiers
│   ├── heures.py          # Fonctions de synchronisation des heures
│   └── connex.py          # Connexions et gestion des identifiants
├── routes/                # Définition des routes FastAPI
├── templates/             # Templates HTML (interface utilisateur)
├── static/                # Fichiers statiques (logo, CSS, JS)
└── ...
```

## Prérequis

- Python 3.8+
- SQL Server (ODBC Driver 17)
- PostgreSQL 14+
- Accès API BatiSimply (identifiants fournis)
- Git

## Installation

1. **Cloner le dépôt**

   ```bash
   git clone <URL_DU_REPO>
   cd connecteur-sages-V1
   ```

2. **Créer un environnement virtuel**

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Installer les dépendances**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configurer les accès aux bases**

   - Renseigner les identifiants SQL Server et PostgreSQL dans le fichier `app/services/credentials.json` (créé automatiquement via l'interface ou à la main).

## Configuration

- **Fichier `app/services/credentials.json`**

  ```json
  {
    "sqlserver": {
      "server": "<ADRESSE_SQL_SERVER>",
      "user": "<UTILISATEUR>",
      "password": "<MOT_DE_PASSE>",
      "database": "<NOM_BDD>"
    },
    "postgres": {
      "host": "<ADRESSE_POSTGRES>",
      "user": "<UTILISATEUR>",
      "password": "<MOT_DE_PASSE>",
      "database": "<NOM_BDD>",
      "port": "5432"
    }
  }
  ```

- **Variables d'environnement** (optionnel) : pour surcharger les accès ou sécuriser les secrets.

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

## Principales fonctions

Voir le fichier [`fonctions.md`](./fonctions.md) pour la liste complète et la description de toutes les fonctions métier.

## Sécurité

- Les identifiants de connexion sont stockés dans un fichier local non versionné (`.gitignore`).
- Les accès API BatiSimply sont protégés par token OAuth2.
- Les routes critiques sont protégées côté interface (pas d'API publique exposée).

## FAQ

- **Q : Les heures vendues ne remontent pas dans BatiSimply ?**
  - Vérifier la requête SQL dans `transfer_chantiers` et la présence de la colonne `TempsMO` dans les devis.
- **Q : J'ai une erreur de colonne `sync` ?**
  - Cette colonne ne doit être utilisée que pour l'import des heures de BatiSimply vers Batigest.
- **Q : Comment ajouter un nouveau flux de synchronisation ?**
  - Ajouter une fonction dans `services/`, puis une route dans `routes/` et un bouton dans `templates/form.html`.

## Bonnes pratiques

- Toujours tester la synchronisation sur une base de test avant la production.
- Ne jamais modifier la structure des tables Batigest sans sauvegarde préalable.
- Utiliser des logs pour tracer chaque étape de synchronisation.
- Garder le fichier `requirements.txt` à jour.
- Documenter toute nouvelle fonction dans `fonctions.md`.

## Auteurs & Contact

- Développement : jp.amar & équipe
- Contact technique : [votre.email@domaine.fr]

---

*Dernière mise à jour : {date du jour}*

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

 