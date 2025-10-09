## Guide d’utilisation de l’exécutable Windows – `connecteur.exe`

Ce document explique, de manière complète et vulgarisée, le fonctionnement de l’exécutable `connecteur.exe`, son objectif, ses prérequis et toutes les étapes pour l’utiliser en production sur un poste Windows.

---

## 1) Qu’est-ce que c’est ?

`connecteur.exe` est une application serveur (FastAPI) packagée pour Windows. Elle fournit une interface web locale permettant de synchroniser des données entre:

- SQL Server (Batigest)
- PostgreSQL (base tampon locale ou distante)
- L’API BatiSimply (SSO Keycloak)

L’outil gère également une licence d’utilisation (validation via Supabase ou service de licence centralisé si configuré).

---

## 2) À quoi sert-il ? (Fonctionnalités)

- Synchroniser les chantiers de Batigest → PostgreSQL → BatiSimply
- Synchroniser les heures de BatiSimply → PostgreSQL → Batigest (table `SuiviMO`)
- Mode « chantier » et mode « devis » (au choix)
- Sélection du logiciel principal (Batigest ou Codial) pour adapter les textes de l’UI
- Gestion et validation des licences (clé fournie par SAGES)
- Interface web moderne (configuration, actions de synchronisation, état des connexions)

---

## 3) Prérequis (poste cible)

- Windows 10 ou plus récent
- Droits suffisants pour ouvrir un port local (8000 par défaut)
- Accès réseau aux bases (SQL Server & PostgreSQL) et à Internet (BatiSimply / Supabase)
- Pilotes:
  - ODBC Driver 17 for SQL Server (indispensable pour `pyodbc`)

Optionnel mais recommandé:
- `.env` pour variables sensibles (voir section 8)

---

## 4) Contenu du bundle

Après build, le dossier `dist/` contient:

- `connecteur.exe` (exécutable unique que vous pouvez copier sur le poste cible)
- Un ancien dossier `ConnecteurBatigest/` (sortie d’un build précédent en mode dossier). Vous pouvez l’ignorer si vous déployez uniquement `connecteur.exe`.

L’exécutable embarque les templates HTML et les fichiers statiques nécessaires. Les données (identifiants, licence, etc.) sont stockées à côté de l’exécutable (voir section 7).

---

## 5) Installation (poste cible)

1. Créez un dossier dédié, par exemple `C:\ConnecteurSages`.
2. Copiez-y `connecteur.exe`.
3. Créez le sous-dossier de données (pour stocker les paramètres) juste à côté de l’exécutable:
   - `app/services/`
4. (Optionnel) Copiez votre fichier `.env` dans le même dossier que `connecteur.exe`.

Pourquoi créer `app/services/` ? L’application enregistre les paramètres dans `app/services/credentials.json`. Le dossier doit exister pour que l’enregistrement fonctionne.

---

## 6) Démarrage & accès

1. Double-cliquez `connecteur.exe` (ou lancez via PowerShell/CMD)
2. Ouvrez votre navigateur sur:
   - `http://localhost:8000`
3. Vérification rapide:
   - Santé API: `http://localhost:8000/health` → doit répondre `{ "status": "healthy" }`

Astuce: Si un firewall Windows demande l’autorisation, acceptez l’accès sur le réseau privé.

---

## 7) Où sont stockés les paramètres ?

- Fichier: `app/services/credentials.json` (à côté de l’exécutable)
- Le fichier est créé/mis à jour via l’interface de configuration.
- Le format est JSON lisible (indenté). En cas de fichier vide/corrompu, l’appli continue de démarrer et vous pouvez reconfigurer.

Important:
- Veillez à ce que le dossier `app/services/` existe avant d’enregistrer.
- Évitez d’ouvrir/modifier le JSON à la main si vous n’êtes pas sûr de la syntaxe.

---

## 8) Variables d’environnement (`.env`)

Vous pouvez placer un fichier `.env` à côté de `connecteur.exe`. Il sera chargé automatiquement au démarrage.

Exemple minimal:
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

# (Optionnel) Service de licences centralisé
LICENSE_API_BASE_URL=
LICENSE_API_KEY=

# Réseau local
HOST=0.0.0.0
PORT=8000
```

---

## 9) Première configuration (interface web)

1. Accédez à `http://localhost:8000/login` puis connectez-vous (mot de passe simple, affiché dans l’UI si demandé).
2. Cliquez sur « Configuration »:
   - Licence: collez la clé fournie par SAGES (validation en temps réel)
   - Bases de données:
     - SQL Server (Batigest): serveur, utilisateur, mot de passe, base
     - PostgreSQL (tampon): hôte, port, utilisateur, mot de passe, base
   - Mode: `chantier` ou `devis`
   - Logiciel principal: `batigest` ou `codial`
3. Testez les connexions, puis enregistrez.

Tous les paramètres sont sauvegardés dans `app/services/credentials.json`.

---

## 10) Utilisation quotidienne

Sur la page d’accueil:
- « Batigest → BatiSimply »: transfère (selon le mode) chantiers/devis SQL Server → PostgreSQL → BatiSimply
- « BatiSimply → Batigest »: récupère les heures depuis BatiSimply → PostgreSQL → envoie vers Batigest (`SuiviMO`)

Vous pouvez également:
- Initialiser/mettre à jour la table PostgreSQL via le bouton dédié
- Voir l’état de licence (si expirée: page dédiée, rafraîchissement possible)

---

### Étape indispensable (une seule fois): mapping des salariés

Pour que les heures soient envoyées dans `SuiviMO`, chaque salarié doit être mappé à un utilisateur BatiSimply. Le champ `Salarie.codebs` doit contenir l'UUID BatiSimply du collaborateur correspondant.

Procédure (à l'installation):
1. Configurez l’onglet Batisimply (SSO/API) et testez la récupération du token.
2. Récupérez la liste des utilisateurs via l’API BatiSimply (id/email/nom).
3. Faites correspondre chaque utilisateur à un salarié (table `Salarie`).
4. Renseignez `Salarie.codebs` avec l’UUID BatiSimply.

Requêtes utiles (SQL Server):
```sql
SELECT TOP 50 Code, Nom, codebs FROM Salarie WHERE codebs IS NULL OR codebs = '' ORDER BY Nom;
-- Exemple de mise à jour
UPDATE Salarie SET codebs = 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx' WHERE Code = 'JP';
```

Sans ce mapping, la synchro « BatiSimply → Batigest » affichera « Aucun utilisateur trouvé » et 0 heure transférée.

---
## 11) Mise à jour de l’exécutable

1. Arrêtez l’ancien `connecteur.exe`
2. Remplacez par la nouvelle version
3. Relancez l’exécutable

Le fichier de paramètres `app/services/credentials.json` est conservé.

---

## 12) Lancer automatiquement au démarrage (optionnel)

Via le Planificateur de tâches Windows:
- Créez une tâche qui lance `connecteur.exe` au logon de la machine ou d’un utilisateur de service.
- Cochez « Exécuter avec les autorisations maximales » si nécessaire.

---

## 13) Sécurité & réseau

- Les identifiants DB sont stockés localement dans `credentials.json`
- Les requêtes API BatiSimply utilisent un token SSO récupéré via vos variables d’environnement
- La licence est validée via Supabase ou un service central (si configuré)
- Ouvrez le port 8000 localement si vos politiques de sécurité l’exigent

---

## 14) Dépannage (FAQ)

**La page d’accueil renvoie 500 au premier démarrage**
- Assurez-vous que le dossier `app/services/` existe à côté de l’exécutable
- Si un fichier `credentials.json` vide existe, supprimez-le; reconfigurez depuis l’UI

**Erreur ODBC / pyodbc**
- Installez « ODBC Driver 17 for SQL Server »
- Vérifiez les identifiants SQL Server et les droits

**Port 8000 occupé**
- Fermez l’autre application qui utilise le port
- Ou changez le port dans `.env` (ex: `PORT=8001`) et relancez `connecteur.exe`

**Licence invalide/expirée**
- Recollez la clé dans Configuration → Licence
- Vérifiez `SUPABASE_KEY` ou le service de licence central

**Rien ne s’affiche, mais le processus apparaît**
- Désactivez temporairement l’antivirus/EDR pour tester
- Ajoutez le dossier en exclusion si nécessaire

---

## 15) Références

- `docs/INSTALLATION_WINDOWS.md`: installation complète du projet
- `app/main.py`: point d’entrée FastAPI
- `app/routes/form_routes.py`: routes UI et actions
- `app/services/connex.py`: connexions DB, token BatiSimply, gestion `credentials.json`
- `app/services/license.py`: validation de licence

---

## 16) Support

- dev2@groupe-sages.fr
- dev3@groupe-sages.fr
- support@groupe-sages.fr (licences)


