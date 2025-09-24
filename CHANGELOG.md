# ChangeLog - Connecteur Sages V1

Ce fichier documente toutes les modifications importantes apportées au projet Connecteur Sages. Il est mis à jour à chaque modification significative et synchronisé avec Git.

---

## [24-09-2025] - Restructuration complète de l'architecture des services

### 🏗️ **Refactorisation majeure de l'organisation du code**

**Contexte :** Le code était organisé en fichiers monolithiques difficiles à maintenir. Nous avons restructuré l'architecture pour une meilleure organisation et maintenabilité.

### **Modifications apportées :**

#### **1. Renommage et réorganisation des fichiers**
- **`app/services/chantier.py` → `app/services/batigest/`** (package complet)
- **`app/services/codial.py` → `app/services/codial/`** (package complet)
- **Suppression des anciens fichiers monolithiques**

#### **2. Création de packages modulaires**

**Package Batigest (`app/services/batigest/`) :**
- `__init__.py` - Exports publics et interface du package
- `chantiers.py` - Gestion des chantiers (SQL Server ↔ PostgreSQL ↔ BatiSimply)
- `heures.py` - Gestion des heures (BatiSimply ↔ PostgreSQL ↔ SQL Server)
- `devis.py` - Gestion des devis (SQL Server ↔ PostgreSQL ↔ BatiSimply)
- `sync.py` - Synchronisations complètes entre systèmes
- `utils.py` - Utilitaires (initialisation des tables, etc.)

**Package Codial (`app/services/codial/`) :**
- `__init__.py` - Exports publics et interface du package
- `chantiers.py` - Gestion des chantiers (HFSQL ↔ PostgreSQL ↔ BatiSimply)
- `heures.py` - Gestion des heures (BatiSimply ↔ HFSQL)
- `sync.py` - Synchronisations complètes entre systèmes
- `utils.py` - Utilitaires (initialisation des tables, etc.)

#### **3. Mise à jour des imports**
- **`app/routes/form_routes.py`** - Imports mis à jour pour utiliser les nouveaux packages
- **`scripts/debug_heures.py`** - Imports mis à jour
- **Documentation** - Toutes les références mises à jour

#### **4. Améliorations techniques**
- **Installation de `pytz`** - Gestion des fuseaux horaires pour les heures
- **Séparation des responsabilités** - Chaque fichier a un rôle spécifique
- **Interface cohérente** - Même structure pour Batigest et Codial

### **Avantages de cette restructuration :**

✅ **Maintenabilité** - Plus facile de déboguer et modifier le code  
✅ **Lisibilité** - Code organisé par flux métier  
✅ **Évolutivité** - Facile d'ajouter de nouveaux flux ou logiciels  
✅ **Réutilisabilité** - Fonctions importables individuellement  
✅ **Séparation claire** - Batigest et Codial dans des packages distincts  

### **Impact pour les utilisateurs :**
- **Aucun impact** - L'interface utilisateur reste identique
- **Performance** - Code plus optimisé et organisé
- **Fiabilité** - Meilleure gestion des erreurs et du debugging

---

## [22-09-2025] - Amélioration de la synchronisation des heures

### 🔄 **Système de synchronisation incrémentale des heures**

**Contexte :** Le système de synchronisation des heures entre BatiSimply et SQL Server créait des doublons et ne gérait pas correctement les modifications.

### **Modifications apportées :**

#### **1. Système de mapping PostgreSQL**
- **Table `batigest_heures_map`** - Mapping persistant entre BatiSimply et SQL Server
- **Logique UPSERT** - Insertion ou mise à jour intelligente des heures
- **Gestion des doublons** - Élimination des enregistrements dupliqués

#### **2. Amélioration de la gestion des fuseaux horaires**
- **Conversion UTC → Europe/Paris** - Correction du décalage de 2 heures
- **Normalisation des dates** - Arrondi à la minute pour éviter les microsecondes
- **Configuration flexible** - Fuseau horaire configurable via `credentials.json`

#### **3. Fenêtre de synchronisation optimisée**
- **Période de 180 jours** - Synchronisation des X derniers jours (configurable)
- **Performance améliorée** - Moins de données à traiter
- **Logique incrémentale** - Seules les heures modifiées sont synchronisées

#### **4. Gestion robuste des erreurs**
- **Filtrage des heures NULL** - Évite les erreurs SQL Server
- **Vérification des salariés** - Mapping BatiSimply → SQL Server
- **Messages d'erreur détaillés** - Debugging facilité

### **Impact pour les utilisateurs :**
- **Synchronisation plus rapide** - Moins de données à traiter
- **Pas de doublons** - Heures uniques dans SQL Server
- **Heures correctes** - Fuseau horaire respecté
- **Fiabilité** - Gestion d'erreurs améliorée

---

## [22-09-2025] - Amélioration de la validation des licences

### 🔐 **Système de validation des licences robuste**

**Contexte :** Le système de validation des licences était fragile et difficile à déboguer.

### **Modifications apportées :**

#### **1. Clé de test "Cobalt"**
- **Super mot de passe** - Clé "Cobalt" pour les tests en mode debug
- **Bypass de validation** - Contournement pour le développement
- **Sécurité** - Uniquement actif en mode debug

#### **2. Amélioration de la validation Supabase**
- **Requêtes optimisées** - Filtres explicites pour les performances
- **Gestion d'erreurs** - Fallback vers les informations locales
- **Debug amélioré** - Logs détaillés pour le troubleshooting

#### **3. Persistance des informations**
- **Sauvegarde locale** - Informations de licence dans `credentials.json`
- **Récupération d'erreur** - Utilisation des données locales en cas d'échec
- **Cohérence** - Synchronisation entre Supabase et local

### **Impact pour les utilisateurs :**
- **Tests facilités** - Clé "Cobalt" pour le développement
- **Validation fiable** - Moins d'échecs de validation
- **Debug simplifié** - Logs clairs pour les problèmes de licence

---

## [22-09-2025] - Documentation et scripts de debug

### 📚 **Outils de diagnostic et documentation**

**Contexte :** Manque d'outils pour diagnostiquer les problèmes de synchronisation.

### **Modifications apportées :**

#### **1. Script de debug des heures**
- **`scripts/debug_heures.py`** - Diagnostic complet du pipeline des heures
- **Filtres configurables** - Par période, par ID d'heure, etc.
- **Mise à jour des codes** - Fonction pour corriger les mappings
- **Application des synchronisations** - Test des transferts

#### **2. Documentation technique**
- **`docs/SYNCHRO_HEURES_MAPPING.md`** - Explication du système de synchronisation
- **`docs/INSTALLATION_WINDOWS.md`** - Guide d'installation complet
- **`docs/EXECUTABLE_CONNECTEUR.md`** - Documentation de l'exécutable

#### **3. Requêtes SQL de diagnostic**
- **Création de tables** - Scripts pour `batigest_devis` et `batigest_heures_map`
- **Requêtes de vérification** - Diagnostic des données
- **Mapping des salariés** - Initialisation des correspondances

### **Impact pour les utilisateurs :**
- **Diagnostic facilité** - Outils pour identifier les problèmes
- **Documentation complète** - Guides d'installation et d'utilisation
- **Maintenance simplifiée** - Scripts de diagnostic automatisés

---

## [11-09-2025] - Amélioration de l'interface utilisateur

### 🎨 **Interface de configuration modernisée**

**Contexte :** L'interface de configuration manquait de clarté et de fonctionnalités de debug.

### **Modifications apportées :**

#### **1. Badges de statut des connexions**
- **Indicateurs visuels** - Pastilles colorées pour chaque base de données
- **Statut en temps réel** - Connexion réussie/échouée
- **Localisation** - Badges dans l'onglet "Bases de données"

#### **2. Mode debug intégré**
- **Switch activable/désactivable** - Contrôle du mode debug
- **Persistence** - Sauvegarde dans `credentials.json`
- **Logs détaillés** - Affichage des opérations en temps réel
- **Localisation** - Panel debug dans l'onglet "Bases de données"

#### **3. Support multi-logiciels**
- **Batigest** - Interface SQL Server
- **Codial** - Interface HFSQL avec champs adaptés
- **Changement dynamique** - Interface qui s'adapte au logiciel sélectionné

#### **4. Configuration BatiSimply**
- **Nouvel onglet** - Configuration des paramètres API
- **Sauvegarde sécurisée** - Données stockées dans `credentials.json`
- **Champs complets** - SSO URL, Client ID, Secret, etc.

#### **5. Amélioration des messages d'erreur**
- **Messages dynamiques** - Titre et style adaptés au type de message
- **Détails techniques** - Section collapsible pour le debugging
- **Formatage propre** - Suppression des caractères d'échappement
- **Bouton de fermeture** - Messages fermables par l'utilisateur

### **Impact pour les utilisateurs :**
- **Interface plus claire** - Statut des connexions visible
- **Debug facilité** - Mode debug intégré et persistant
- **Support Codial** - Interface adaptée pour HFSQL
- **Messages d'erreur lisibles** - Debugging simplifié

---

## [03-09-2025] - Corrections techniques diverses

### 🔧 **Améliorations techniques et corrections de bugs**

#### **1. Gestion des connexions HFSQL**
- **Support DSN** - Connexion via DSN pour Codial
- **Pilotes multiples** - Fallback sur différents pilotes HFSQL
- **Champs optionnels** - Mot de passe et port configurables
- **Gestion d'erreurs** - Messages d'erreur détaillés pour HFSQL

#### **2. Amélioration de la configuration**
- **Sauvegarde persistante** - Toutes les configurations dans `credentials.json`
- **Validation des données** - Vérification des champs requis
- **Interface adaptative** - Changement dynamique selon le logiciel

#### **3. Optimisation des performances**
- **Requêtes optimisées** - Amélioration des requêtes SQL
- **Gestion mémoire** - Fermeture propre des connexions
- **Logs structurés** - Messages de debug organisés

### **Impact pour les utilisateurs :**
- **Connexion HFSQL fiable** - Support complet de Codial
- **Configuration persistante** - Paramètres sauvegardés
- **Performance améliorée** - Synchronisations plus rapides

---

## Notes de version

### **Version actuelle :** 1.0.0
### **Dernière mise à jour :** 24-09-2025
### **Prochaine version prévue :** 1.1.0 (Fonctionnalités Codial complètes)

---

## Comment contribuer

Pour toute modification importante :
1. Mettre à jour ce ChangeLog
2. Commiter avec un message descriptif
3. Tester les modifications
4. Documenter les nouvelles fonctionnalités

---

*Ce ChangeLog est maintenu à jour avec chaque modification significative du projet.*