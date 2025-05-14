# Connecteur SAGES V1

Application de connexion et de synchronisation avec les bases de données SAGES.

## Fonctionnement

L'application fournit une interface web pour :

1. **Connexion SQL Server** :
   - Saisie du serveur
   - Nom d'utilisateur
   - Mot de passe
   - Base de données

2. **Connexion PostgreSQL** :
   - Adresse du serveur
   - Nom d'utilisateur
   - Mot de passe
   - Base de données
   - Port (par défaut : 5432)

3. **Transfert des données** :
   - Une fois les connexions établies, vous pouvez lancer le transfert des données

Les identifiants sont stockés temporairement pendant la session pour permettre le transfert des données.

## Sécurité

- Les identifiants sont stockés temporairement dans `credentials.json`
- Ce fichier est automatiquement exclu du versionnement Git
- Il est recommandé de supprimer ce fichier après utilisation

## Configuration des identifiants

Pour utiliser l'application, vous devez configurer vos identifiants de connexion :

1. Copiez le fichier exemple des identifiants :
   ```bash
   copy app/services/credentials.json.example app/services/credentials.json
   ```

2. Modifiez le fichier `app/services/credentials.json` avec vos identifiants :
   ```json
   {
       "sqlserver": {
           "server": "votre_serveur_sql",
           "user": "votre_utilisateur",
           "password": "votre_mot_de_passe",
           "database": "votre_base_de_donnees"
       },
       "postgres": {
           "host": "votre_serveur_postgres",
           "user": "votre_utilisateur",
           "password": "votre_mot_de_passe",
           "database": "votre_base_de_donnees",
           "port": "5432"
       }
   }
   ```

⚠️ Note : Le fichier `credentials.json` contient des informations sensibles et n'est pas versionné dans Git. 