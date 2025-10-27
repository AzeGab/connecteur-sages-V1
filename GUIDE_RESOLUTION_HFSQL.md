# Guide de Résolution des Problèmes HFSQL

## Problème Identifié

Vous rencontrez l'erreur suivante :
```
Erreur HFSQL (pilote/DSN): ('08001', '[08001] Erreur renvoyée par le serveur <PC-JEAN-PIERRE:4900> :
Cette fonction nécessite une couche cliente plus récente.

Informations de débogage :
IEWDHFSRV=13.63
Module=<WDHFSRV>
Version=<30.0.367.0>
```

## Analyse du Problème

- **Version client détectée** : IEWDHFSRV=13.63
- **Serveur cible** : PC-JEAN-PIERRE:4900
- **Base de données** : DATA_DEMO
- **Cause principale** : Incompatibilité de version entre le client HFSQL et le serveur

## Solutions par Ordre de Priorité

### 1. Mise à Jour du Client HFSQL (RECOMMANDÉ)

**Étapes :**
1. Télécharger la dernière version depuis : https://www.pcsoft.fr/telechargements/
2. Installer HFSQL Client/Server (version 64-bit si Python 64-bit)
3. Redémarrer l'ordinateur après installation
4. Tester la connexion

**Vérification :**
```bash
python test_hfsql_connection.py
```

### 2. Création d'un DSN Windows (SOLUTION ALTERNATIVE)

Si la mise à jour n'est pas possible :

**Étapes manuelles :**
1. Ouvrir "Sources de données ODBC" (`odbcad32.exe`)
2. Aller dans l'onglet "DSN système"
3. Cliquer "Ajouter"
4. Sélectionner "HFSQL Client/Server"
5. Configurer :
   - **Nom du serveur** : PC-JEAN-PIERRE
   - **Port** : 4900
   - **Base de données** : DATA_DEMO
   - **Utilisateur** : admin
6. Tester la connexion
7. Utiliser `DSN=NomDuDSN` dans votre configuration

**Script automatique :**
```bash
# Exécuter en tant qu'administrateur
create_hfsql_dsn.bat
```

### 3. Vérification de la Compatibilité

**Points à vérifier :**
- Version du serveur HFSQL
- Paramètres de pare-feu
- Connectivité réseau : `telnet PC-JEAN-PIERRE 4900`
- Permissions utilisateur

## Scripts de Diagnostic

### Diagnostic Rapide
```bash
python test_hfsql_connection.py
```

### Diagnostic Avancé
```bash
python debug_hfsql_advanced.py
```

### Diagnostic Original
```bash
python debug_hfsql.py
```

## Configuration dans le Code

### Utilisation avec DSN
```python
# Dans votre configuration
host = "DSN=HFSQL_DEMO"  # Nom de votre DSN
user = "admin"
password = ""
database = "DATA_DEMO"
port = "4900"
```

### Utilisation Directe (après mise à jour)
```python
# Configuration directe
host = "PC-JEAN-PIERRE"
user = "admin"
password = ""
database = "DATA_DEMO"
port = "4900"
```

## Améliorations Apportées

### Fonction `connect_to_hfsql` Améliorée

La fonction a été améliorée pour :
- Tester plusieurs drivers HFSQL
- Essayer différents formats de chaîne de connexion
- Gérer les erreurs de version de manière détaillée
- Proposer des solutions automatiques
- Supporter les connexions DSN et directes

### Drivers Testés

1. HFSQL Client/Server (Unicode)
2. HFSQL Client/Server
3. HFSQL (Unicode)
4. HFSQL
5. HFSQL Client/Server Unicode
6. HFSQL Unicode Client/Server
7. HFSQL Client/Server 64-bit
8. HFSQL Client/Server 32-bit

### Formats de Connexion Testés

1. Format pypyodbc
2. Format pyodbc
3. Format alternatif
4. Connexion sans base spécifiée
5. Connexion avec host:port

## Messages d'Erreur Courants

### "Cette fonction nécessite une couche cliente plus récente"
- **Solution** : Mettre à jour le client HFSQL

### "Driver not found"
- **Solution** : Installer le pilote ODBC HFSQL

### "Connection timeout"
- **Solution** : Vérifier la connectivité réseau et les paramètres de pare-feu

### "Invalid DSN"
- **Solution** : Créer ou corriger le DSN Windows

## Support Technique

Si les solutions proposées ne fonctionnent pas :

1. Exécuter le diagnostic avancé
2. Collecter les logs d'erreur
3. Contacter l'administrateur du serveur HFSQL
4. Vérifier la documentation PC SOFT

## Fichiers Créés

- `debug_hfsql_advanced.py` : Diagnostic avancé
- `test_hfsql_connection.py` : Test rapide
- `create_hfsql_dsn.bat` : Script de création DSN
- `GUIDE_RESOLUTION_HFSQL.md` : Ce guide

## Prochaines Étapes

1. Exécuter `python test_hfsql_connection.py`
2. Si échec, exécuter `python debug_hfsql_advanced.py`
3. Suivre les recommandations du diagnostic
4. Mettre à jour le client HFSQL si possible
5. Créer un DSN Windows en alternative
