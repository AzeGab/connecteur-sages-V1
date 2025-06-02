# Connecteur SAGES - Batigest/Batisimply

## Description

Le Connecteur SAGES est une application de synchronisation entre Batigest et Batisimply, développée par le Groupe SAGES. Cette solution permet d'harmoniser automatiquement les données de chantiers et d'heures entre ces deux systèmes de gestion, facilitant ainsi le travail quotidien des équipes.

## Fonctionnalités

- Synchronisation des chantiers de Batigest vers Batisimply
- Synchronisation des heures de Batisimply vers Batigest
- Interface web intuitive
- Synchronisation en temps réel
- Gestion des conflits automatique
- Logs détaillés des opérations

## Prérequis Système

- Windows 10 ou supérieur
- Python 3.11
- SQL Server (ODBC Driver 17)
- PostgreSQL 14+
- Accès Internet pour la connexion à Batisimply
- Accès aux bases de données Batigest et PostgreSQL

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

### 1. Configuration des Bases de Données

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

### 2. Configuration via l'Interface

1. Lancer l'application :
   ```bash
   uvicorn app.main:app --reload
   ```

2. Accéder à l'interface web :
   ```
   http://localhost:8000
   ```

3. Cliquer sur "Configuration" en haut à droite
4. Remplir les informations de connexion
5. Sauvegarder la configuration

## Utilisation

### Interface Web

1. **Page d'accueil**
   - Vue d'ensemble de l'état de synchronisation
   - Boutons de synchronisation rapide

2. **Synchronisation**
   - Batigest → Batisimply : Synchronise les chantiers vers Batisimply
   - Batisimply → Batigest : Synchronise les heures vers Batigest

3. **Configuration**
   - Gestion des connexions
   - Paramètres de synchronisation
   - Logs et historique

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

1. **Erreur de connexion SQL Server**
   - Vérifier que le serveur est accessible
   - Vérifier les identifiants
   - Vérifier que l'ODBC Driver 17 est installé

2. **Erreur de connexion PostgreSQL**
   - Vérifier que le serveur est accessible
   - Vérifier les identifiants
   - Vérifier que le port est correct

3. **Erreur de synchronisation**
   - Vérifier les logs dans l'interface
   - Vérifier la connexion Internet
   - Vérifier les droits d'accès aux bases

### Logs

Les logs sont accessibles via l'interface web dans la section "Configuration". Ils permettent de :

- Suivre les opérations de synchronisation
- Identifier les erreurs
- Vérifier l'état des connexions

## Support

Pour toute assistance :

- Support technique : [dev2@groupe-sages.fr](mailto:dev2@groupe-sages.fr)
- Support développement : [dev3@groupe-sages.fr](mailto:dev3@groupe-sages.fr)

## Mises à Jour

Les mises à jour sont gérées automatiquement via l'interface web. Une notification apparaît lorsqu'une mise à jour est disponible.

## Sécurité

- Les identifiants sont stockés localement de manière sécurisée
- Les connexions aux bases de données sont chiffrées
- Les accès API sont protégés par token
- Aucune donnée sensible n'est stockée en clair

## Licence

Propriété du Groupe SAGES. Tous droits réservés.

---

### Dernière mise à jour : {date du jour}

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

 