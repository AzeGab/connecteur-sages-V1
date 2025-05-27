# Liste des fonctions du projet

## app/services/chantier.py
- `transfer_chantiers()` : Transfère les données des chantiers depuis SQL Server vers PostgreSQL.
- `transfer_chantiers_vers_batisimply()` : Transfère les chantiers depuis PostgreSQL vers BatiSimply.
- `recup_chantiers_batisimply()` : Récupère les chantiers depuis BatiSimply via l'API.
- `recup_chantiers_postgres()` : Récupère les chantiers depuis Batigest (PostgreSQL).
- `check_batigest_heures_content()` : Vérifie le contenu de la table batigest_heures pour déboguer.
- `update_code_projet_chantiers()` : Met à jour les codes projet des chantiers dans PostgreSQL.
- `sync_batigest_to_batisimply()` : Synchronise les chantiers de Batigest vers BatiSimply via PostgreSQL.
- `sync_batisimply_to_batigest()` : Synchronise les chantiers de Batisimply vers Batigest via PostgreSQL.
- `init_postgres_table()` : Initialise la table PostgreSQL avec les colonnes nécessaires pour le suivi des modifications.

## app/services/heures.py
- `transfer_heures_to_postgres()` : Transfère les heures depuis BatiSimply vers PostgreSQL pour une période allant d'aujourd'hui à +5 ans.
- `transfer_heures_to_sqlserver()` : Transfère les heures validées de PostgreSQL vers SQL Server.

## app/services/connex.py
- `connect_to_sqlserver(server, user, password, database)` : Établit une connexion à une base SQL Server.
- `connect_to_postgres(host, user, password, database, port="5432")` : Établit une connexion à une base PostgreSQL.
- `save_credentials(data)` : Sauvegarde les identifiants de connexion dans un fichier JSON.
- `load_credentials()` : Charge les identifiants de connexion depuis le fichier JSON.
- `recup_batisimply_token()` : Récupère le token d'authentification pour l'API BatiSimply.
- `check_connection_status()` : Vérifie l'état des connexions aux bases de données. 