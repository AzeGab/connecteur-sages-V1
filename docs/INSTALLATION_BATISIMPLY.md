# Guide d'Installation - Connecteur BATISIMPLY

Ce guide vous accompagne dans l'installation du connecteur BATISIMPLY sur votre poste de travail.

## Prérequis

- Windows 10 ou supérieur
- Python 3.8 ou supérieur
- Git (optionnel, pour la mise à jour du logiciel)
- Accès à Internet pour l'installation des dépendances
- PostgreSQL 14 ou supérieur
- SQL Server (pour la connexion à Batigest)

## Étapes d'installation

### 1. Installation de Python

1. Téléchargez Python depuis [python.org](https://www.python.org/downloads/)
2. Lors de l'installation, **IMPORTANT** : cochez la case "Add Python to PATH"
3. Cliquez sur "Install Now"
4. Vérifiez l'installation en ouvrant un terminal (PowerShell) et en tapant :
   ```bash
   python --version
   ```

### 2. Installation de PostgreSQL

1. Téléchargez PostgreSQL depuis [postgresql.org](https://www.postgresql.org/download/windows/)
2. Lancez l'installateur et suivez les étapes :
   - Choisissez le port par défaut (5432)
   - Définissez un mot de passe pour l'utilisateur 'postgres'
   - **IMPORTANT** : Notez ce mot de passe, il sera nécessaire pour la configuration
3. Une fois l'installation terminée, vérifiez que le service PostgreSQL est en cours d'exécution :
   - Ouvrez les Services Windows (services.msc)
   - Recherchez "PostgreSQL"
   - Assurez-vous que le service est "En cours d'exécution"
   - Si non, démarrez-le manuellement

[... Le reste du contenu du fichier INSTALLATION.md ...] 