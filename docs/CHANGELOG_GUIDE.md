# Guide de maintenance du ChangeLog

Ce guide explique comment maintenir le fichier `ChangeLog.md` à jour avec les modifications du projet.

## 📋 **Quand mettre à jour le ChangeLog ?**

### ✅ **Modifications à documenter :**
- Nouvelles fonctionnalités
- Corrections de bugs importantes
- Changements d'architecture
- Modifications de l'interface utilisateur
- Améliorations de performance
- Changements de configuration
- Ajout de nouvelles dépendances
- Modifications de la documentation

### ❌ **Modifications à ne PAS documenter :**
- Corrections de typos mineures
- Reformulation de commentaires
- Changements de formatage uniquement
- Tests unitaires
- Modifications temporaires de debug

## 📝 **Format du ChangeLog**

### **Structure d'une entrée :**

```markdown
## [DD-MM-YYYY] - Titre de la modification

### 🎯 **Sous-titre descriptif**

**Contexte :** Explication du problème ou du besoin

### **Modifications apportées :**

#### **1. Nom de la modification**
- **Détail 1** - Description claire
- **Détail 2** - Description claire

#### **2. Autre modification**
- **Détail 1** - Description claire

### **Impact pour les utilisateurs :**
- **Bénéfice 1** - Explication claire
- **Bénéfice 2** - Explication claire
```

## 🎨 **Émojis à utiliser**

- 🏗️ **Architecture** - Refactorisation, restructuration
- 🎨 **Interface** - Modifications UI/UX
- 🔧 **Technique** - Corrections, optimisations
- 🔐 **Sécurité** - Authentification, licences
- 📚 **Documentation** - Guides, scripts
- 🔄 **Synchronisation** - Flux de données
- ⚡ **Performance** - Optimisations
- 🐛 **Bug** - Corrections de bugs

## 📋 **Processus de mise à jour**

### **1. Avant de commiter :**
```bash
# Vérifier les modifications
git status
git diff

# Mettre à jour le ChangeLog
# Ajouter la nouvelle entrée en haut (après le titre)
```

### **2. Structure de l'entrée :**
- **Date** : Format DD-MM-YYYY
- **Titre** : Résumé en une phrase
- **Contexte** : Pourquoi cette modification ?
- **Modifications** : Qu'est-ce qui a changé ?
- **Impact** : Qu'est-ce que ça apporte ?

### **3. Après la mise à jour :**
```bash
# Ajouter le ChangeLog
git add ChangeLog.md

# Commiter avec un message descriptif
git commit -m "feat: Description de la modification

- Détail 1
- Détail 2
- Mise à jour du ChangeLog.md"
```

## 📖 **Exemples d'entrées**

### **Nouvelle fonctionnalité :**
```markdown
## [24-01-2025] - Ajout de la synchronisation automatique

### 🔄 **Synchronisation programmée des heures**

**Contexte :** Les utilisateurs demandaient une synchronisation automatique des heures sans intervention manuelle.

### **Modifications apportées :**

#### **1. Planificateur de tâches**
- **Cron job** - Exécution automatique toutes les heures
- **Configuration** - Paramètres dans l'interface utilisateur
- **Logs** - Historique des synchronisations

### **Impact pour les utilisateurs :**
- **Automatisation** - Plus besoin de synchroniser manuellement
- **Temps gagné** - Synchronisation en arrière-plan
- **Fiabilité** - Synchronisation régulière et fiable
```

### **Correction de bug :**
```markdown
## [24-01-2025] - Correction du décalage horaire

### 🐛 **Gestion des fuseaux horaires**

**Contexte :** Les heures étaient décalées de 2 heures à cause d'un problème de conversion de timezone.

### **Modifications apportées :**

#### **1. Conversion de timezone**
- **UTC → Europe/Paris** - Conversion correcte des dates
- **Normalisation** - Arrondi à la minute
- **Configuration** - Fuseau horaire configurable

### **Impact pour les utilisateurs :**
- **Heures correctes** - Plus de décalage de 2 heures
- **Précision** - Synchronisation exacte des créneaux
- **Flexibilité** - Fuseau horaire configurable
```

## 🔄 **Maintenance régulière**

### **À faire à chaque release :**
1. Vérifier que toutes les modifications importantes sont documentées
2. Mettre à jour la version dans les "Notes de version"
3. Vérifier la cohérence du format
4. Relire pour la clarté et la compréhension

### **À faire mensuellement :**
1. Vérifier que le ChangeLog est à jour
2. Nettoyer les entrées obsolètes si nécessaire
3. Améliorer la documentation des modifications complexes

## 📚 **Bonnes pratiques**

### **Rédaction :**
- **Langage simple** - Accessible à tous les niveaux
- **Contexte clair** - Expliquer le "pourquoi"
- **Impact concret** - Ce que ça apporte à l'utilisateur
- **Détails techniques** - Pour les développeurs

### **Organisation :**
- **Chronologique** - Les plus récentes en premier
- **Groupement** - Modifications liées ensemble
- **Hiérarchie** - Titres et sous-titres clairs

### **Maintenance :**
- **Mise à jour immédiate** - Ne pas attendre
- **Validation** - Vérifier avant de commiter
- **Cohérence** - Respecter le format établi

---

*Ce guide doit être suivi pour maintenir un ChangeLog de qualité et utile pour tous les utilisateurs du projet.*
