# Connecteur SAGES - Batigest/Batisimply

## Description

Le Connecteur SAGES est une application de synchronisation entre Batigest et Batisimply, développée par le Groupe SAGES. Cette solution permet d'harmoniser automatiquement les données de chantiers et d'heures entre ces deux systèmes de gestion, facilitant ainsi le travail quotidien des équipes.

## Fonctionnalités

- Synchronisation des chantiers de Batigest vers Batisimply
- Synchronisation des heures de Batisimply vers Batigest
- Interface web intuitive avec sidebar de configuration
- Synchronisation en temps réel
- Gestion des conflits automatique
- Logs détaillés des opérations
- **Système de licences intégré avec validation Supabase**
- **Vérification automatique de la validité des licences**
- **Interface de gestion des licences moderne**

## Prérequis Système

- Windows 10 ou supérieur
- Python 3.11
- SQL Server (ODBC Driver 17)
- PostgreSQL 14+
- Accès Internet pour la connexion à Batisimply et validation des licences
- Accès aux bases de données Batigest et PostgreSQL
- **Licence valide du Groupe SAGES**

## Installation

### 1. Installation Automatisée (Recommandée)

1. Exécuter le fichier `installer.py`
2. Suivre les instructions à l'écran
3. L'installateur configurera automatiquement :
   - L'environnement Python
   - Les dépendances nécessaires
   - Les connexions aux bases de données
   - Le service Windows

### 2. Installation Manuelle

1. **Installation de Python 3.11**
   - Télécharger Python 3.11 depuis [python.org](https://www.python.org/downloads/)
   - Cocher "Add Python to PATH" lors de l'installation

2. **Installation des dépendances système**
   - Installer [ODBC Driver 17 pour SQL Server](https://learn.microsoft.com/fr-fr/sql/connect/odbc/download-odbc-driver-for-sql-server)
   - Installer [PostgreSQL 14+](https://www.postgresql.org/download/windows/)

3. **Configuration du projet**

   ```bash
   # Cloner le projet
   git clone [https://github.com/AzeGab/connecteur-sages-V1.git](https://github.com/AzeGab/connecteur-sages-V1.git)
   cd connecteur-sages-V1

   # Créer l'environnement virtuel
   python -m venv venv
   venv\Scripts\activate

   # Installer les dépendances
   pip install -r requirements.txt
   ```

## Configuration

### 1. Configuration des Licences

**IMPORTANT** : Une licence valide est requise pour utiliser l'application.

1. **Configuration de la licence**
   - Accéder à la page de configuration
   - Section "Licence" dans la sidebar
   - Saisir la clé de licence fournie par le Groupe SAGES
   - Cliquer sur "Enregistrer la licence"

2. **Validation automatique**
   - La licence est validée en temps réel auprès de Supabase
   - Vérification de l'expiration, du statut actif, et des limites d'usage
   - Actualisation automatique possible via le bouton "Actualiser"

### 2. Configuration des Bases de Données

1. **SQL Server (Batigest)**
   - Adresse du serveur
   - Nom d'utilisateur
   - Mot de passe
   - Nom de la base de données

2. **PostgreSQL**
   - Adresse du serveur
   - Nom d'utilisateur
   - Mot de passe
   - Nom de la base de données
   - Port (par défaut : 5432)

3. **Batisimply**
   - Identifiants API fournis par le Groupe SAGES

### 3. Configuration via l'Interface

1. Lancer l'application :
   ```bash
   uvicorn app.main:app --reload
   ```

2. Accéder à l'interface web :
   ```
   http://localhost:8000
   ```

3. Cliquer sur "Configuration" en haut à droite
4. **Configurer d'abord la licence** dans la section "Licence"
5. Remplir les informations de connexion aux bases de données
6. Sauvegarder la configuration

## Utilisation

### Interface Web

1. **Page d'accueil**
   - Vue d'ensemble de l'état de synchronisation
   - Boutons de synchronisation rapide
   - **Vérification automatique de la licence au chargement**

2. **Synchronisation**
   - Batigest → Batisimply : Synchronise les chantiers vers Batisimply
   - Batisimply → Batigest : Synchronise les heures vers Batigest

3. **Configuration (Nouvelle interface avec sidebar)**
   - **Section Licence** : Gestion des clés de licence
   - **Section Bases de données** : Gestion des connexions SQL
   - **Section Mode de données** : Choix entre chantier/devis
   - **Section Système** : Outils de maintenance

### Gestion des Licences

1. **Validation en temps réel**
   - Vérification automatique de la validité
   - Actualisation manuelle possible
   - Messages d'erreur détaillés

2. **Page de licence expirée**
   - Interface dédiée en cas de licence invalide
   - Bouton de revérification avec modal moderne
   - Rafraîchissement automatique toutes les 5 minutes
   - Informations détaillées sur la licence

3. **Sécurité**
   - Middleware de vérification sur toutes les routes protégées
   - Redirection automatique vers la page appropriée
   - Stockage sécurisé des clés dans les credentials

### Flux de Synchronisation

1. **Synchronisation des Chantiers**
   - Direction : Batigest → Batisimply uniquement
   - Fréquence : En temps réel ou selon planning configuré
   - Données synchronisées : Informations des chantiers et heures vendues

2. **Synchronisation des Heures**
   - Direction : Batisimply → Batigest uniquement
   - Fréquence : En temps réel ou selon planning configuré
   - Données synchronisées : Heures réalisées saisies dans Batisimply

### Synchronisation Automatique

Le connecteur peut être configuré pour synchroniser automatiquement les données à intervalles réguliers. La configuration se fait via l'interface web.

## Dépannage

### Problèmes Courants

1. **Erreur de licence**
   - Vérifier que la clé de licence est correcte
   - Vérifier que la licence n'a pas expiré
   - Utiliser le bouton "Actualiser" pour revérifier
   - Contacter le support si le problème persiste

2. **Erreur de connexion SQL Server**
   - Vérifier que le serveur est accessible
   - Vérifier les identifiants
   - Vérifier que l'ODBC Driver 17 est installé

3. **Erreur de connexion PostgreSQL**
   - Vérifier que le serveur est accessible
   - Vérifier les identifiants
   - Vérifier que le port est correct

4. **Erreur de synchronisation**
   - Vérifier les logs dans l'interface
   - Vérifier la connexion Internet
   - Vérifier les droits d'accès aux bases

### Logs

Les logs sont accessibles via l'interface web dans la section "Configuration". Ils permettent de :

- Suivre les opérations de synchronisation
- Identifier les erreurs
- Vérifier l'état des connexions
- **Diagnostiquer les problèmes de licence**

## Support

Pour toute assistance :

- Support technique : [dev2@groupe-sages.fr](mailto:dev2@groupe-sages.fr)
- Support développement : [dev3@groupe-sages.fr](mailto:dev3@groupe-sages.fr)
- **Support licences : [support@groupe-sages.fr](mailto:support@groupe-sages.fr)**

## Mises à Jour

Les mises à jour sont gérées automatiquement via l'interface web. Une notification apparaît lorsqu'une mise à jour est disponible.

## Sécurité

- Les identifiants sont stockés localement de manière sécurisée
- Les connexions aux bases de données sont chiffrées
- Les accès API sont protégés par token
- Aucune donnée sensible n'est stockée en clair
- **Validation des licences via API sécurisée Supabase**
- **Vérification automatique de la validité des licences**

## Licence

Propriété du Groupe SAGES. Tous droits réservés.

**Système de licences :**
- Validation en temps réel via Supabase
- Vérification automatique de l'expiration
- Gestion des limites d'usage
- Interface de gestion intégrée

---

### Dernière mise à jour : 24/06/2025

## Routes principales

- **GET /** : Page principale (formulaire de connexion, boutons d'action)
- **GET /configuration** : Page de configuration avec sidebar
- **GET /license-expired** : Page de licence expirée
- **POST /update-license** : Mise à jour de la clé de licence
- **POST /refresh-license** : Rafraîchissement de la validation de licence
- **GET /check-license-status** : Vérification du statut de la licence
- **GET /get-license-key** : Récupération de la clé de licence locale
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

# Licence Manager - Système de Gestion des Licences

## Description
Service web dédié à la gestion des licences pour le connecteur Sages (Batigest ↔ Batisimply).
Ce service centralisé permet de créer, valider et gérer les licences pour tous les clients.

## Architecture
- **Backend** : FastAPI avec Supabase
- **Frontend** : Templates HTML avec Tailwind CSS
- **Base de données** : Supabase (PostgreSQL)

## Fonctionnalités
- ✅ Création de licences
- ✅ Validation de licences (API)
- ✅ Tableau de bord de gestion
- ✅ Désactivation/Réactivation
- ✅ Prolongation de licences
- ✅ Interface web complète

## Installation

### 1. Prérequis
- Python 3.8+
- Compte Supabase
- Variables d'environnement configurées

### 2. Configuration
```bash
# Cloner le projet
git clone <repository>
cd licence-manager

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos clés Supabase
```

### 3. Base de données
Exécuter le script SQL dans Supabase :
```sql
-- Voir la fonction create_licenses_table() dans le code
```

### 4. Lancement
```bash
python main.py
# Ou
uvicorn app.main:app --reload
```

## API Endpoints

### Validation de Licence (pour les clients)
```
POST /api/validate
Content-Type: application/json

{
    "license_key": "XXXX-XXXX-XXXX-XXXX"
}
```

### Gestion Web (pour l'administrateur)
- `GET /` - Tableau de bord
- `GET /licenses/create` - Créer une licence
- `GET /licenses/details/{key}` - Détails d'une licence

## Structure du Projet
```
licence-manager/
├── app/
│   ├── services/
│   │   └── supabase_licences.py    # Logique métier
│   ├── routes/
│   │   └── license_routes.py       # Routes web et API
│   ├── templates/                  # Interface web
│   └── main.py                     # Point d'entrée
├── requirements.txt
├── .env.example
└── README.md
```

## Sécurité
- Clés Supabase sécurisées
- Validation côté serveur
- Gestion des fuseaux horaires
- Logs d'utilisation

## Déploiement
Ce service doit être déployé sur vos serveurs pour rester sous votre contrôle.
Les clients utiliseront uniquement l'endpoint de validation. 