# Changelog - Connecteur SAGES

## [2.0.0] - 2025-06-24

### 🎉 Nouveautés majeures

#### Système de licences intégré
- **Validation en temps réel** via API Supabase
- **Middleware de protection** sur toutes les routes protégées
- **Interface de gestion des licences** moderne avec sidebar
- **Page de licence expirée** dédiée avec modal de revérification
- **Vérification automatique** au chargement des pages

#### Interface utilisateur améliorée
- **Sidebar de configuration** avec navigation entre sections
- **Section Licence** avec champ sécurisé et indicateur de validité
- **Notifications modernes** remplaçant les alertes
- **Overlay de chargement** élégant pour les vérifications
- **Design responsive** et cohérent

### 🔧 Améliorations techniques

#### Service de licence (`app/services/license.py`)
- Validation directe via API REST Supabase
- Gestion locale des informations de licence
- Logs détaillés pour le diagnostic
- Gestion des cas d'usage illimité (`max_usage = -1`)
- Vérification de tous les critères de validité

#### Middleware de licence (`app/middleware/license_middleware.py`)
- Vérification automatique sur les routes protégées
- Redirection intelligente selon le statut de la licence
- Affichage direct de la page de licence expirée
- Gestion des routes exclues

#### Routes API (`app/routes/form_routes.py`)
- `/check-license-status` : Vérification du statut
- `/get-license-key` : Récupération de la clé locale
- `/update-license` : Mise à jour de la clé
- `/refresh-license` : Rafraîchissement de la validation
- Logs détaillés pour le diagnostic

### 🎨 Interface utilisateur

#### Page de configuration (`app/templates/configuration.html`)
- **Sidebar de navigation** avec 4 sections :
  - Licence (gestion des clés)
  - Bases de données (connexions SQL)
  - Mode de données (chantier/devis)
  - Système (outils de maintenance)
- **Section Licence** avec :
  - Champ de saisie sécurisé
  - Indicateur de validité en temps réel
  - Bouton d'actualisation
  - Sauvegarde même des clés invalides

#### Page de licence expirée (`app/templates/license_expired.html`)
- **Interface dédiée** avec informations détaillées
- **Bouton de revérification** avec modal moderne
- **Rafraîchissement automatique** toutes les 5 minutes
- **Notifications élégantes** au lieu d'alertes
- **Overlay de chargement** de 1 seconde

#### Page principale (`app/templates/index.html`)
- **Vérification automatique** de la licence au chargement
- **Redirection automatique** si licence invalide

### 🔒 Sécurité

#### Protection des routes
- **Routes protégées** : `/`, `/transfer`, `/sync-*`, etc.
- **Routes exclues** : `/configuration`, `/license-expired`, etc.
- **Vérification automatique** à chaque requête

#### Stockage sécurisé
- **Fichier credentials.json** pour les informations locales
- **Aucune transmission** de clés en clair
- **Validation via API** sécurisée uniquement

### 📊 Fonctionnalités

#### Validation en temps réel
- **Critères de validation** :
  - `is_active = true`
  - `expires_at > now()`
  - `is_archived = false`
  - `usage_count < max_usage` (si applicable)

#### Gestion locale
- **Structure des données** :
  ```json
  {
    "license": {
      "key": "XXXX-XXXX-XXXX-XXXX",
      "client_name": "Client XXXXX",
      "expiry_date": "2027-06-23T09:46:12.23389+00:00",
      "features": ["chantier", "devis", "heures"],
      "updated_at": "2025-06-24T10:00:00",
      "valid": true,
      "usage_count": 0,
      "max_usage": -1,
      "is_active": true
    }
  }
  ```

### 🐛 Corrections

#### Logique de validation
- **Correction du bug** de vérification de l'usage count
- **Gestion correcte** des licences illimitées (`max_usage = -1`)
- **Sauvegarde des clés invalides** pour affichage persistant

#### Interface utilisateur
- **Correction de l'affichage** des clés dans la configuration
- **Amélioration des messages** d'erreur
- **Gestion des timeouts** et erreurs de connexion

### 📝 Documentation

#### Fichiers mis à jour
- **README.md** : Documentation complète avec système de licences
- **LICENSE_API_CONFIG.md** : Guide détaillé du système de licences
- **CHANGELOG.md** : Ce fichier

#### Nouveaux fichiers
- **test_supabase_connection.py** : Script de test de connexion
- **Documentation des routes** API

### 🔧 Configuration

#### Variables d'environnement
```env
SUPABASE_URL=https://rxqveiaawggfyeukpvyz.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Structure Supabase
- **Table `licenses`** avec tous les champs nécessaires
- **API REST** pour la validation
- **Clé anon** pour les requêtes client

### 🚀 Déploiement

#### Prérequis
- **Licence valide** requise pour l'utilisation
- **Accès Internet** pour la validation
- **Variables d'environnement** configurées

#### Installation
1. **Configuration de la licence** en premier
2. **Configuration des bases de données**
3. **Test de connexion** avec le script fourni

---

## [1.0.0] - 2025-06-23

### Version initiale
- Synchronisation Batigest ↔ Batisimply
- Interface web basique
- Gestion des connexions SQL
- Transfert de données

---

*Dernière mise à jour : 24/06/2025* 