# Configuration du Système de Licences - Connecteur SAGES

## Vue d'ensemble

Le Connecteur SAGES intègre un système de licences robuste basé sur Supabase pour la validation en temps réel. Ce système garantit que seuls les utilisateurs autorisés peuvent accéder aux fonctionnalités de l'application.

## Architecture

### Composants principaux

1. **Service de licence** (`app/services/license.py`)
   - Validation des clés via API Supabase
   - Gestion locale des informations de licence
   - Vérification automatique de la validité

2. **Middleware de licence** (`app/middleware/license_middleware.py`)
   - Vérification automatique sur toutes les routes protégées
   - Redirection vers la page appropriée selon le statut
   - Affichage direct de la page de licence expirée

3. **Interface utilisateur**
   - Page de configuration avec section licence
   - Page de licence expirée avec modal de revérification
   - Notifications modernes et overlay de chargement

## Configuration Supabase

### Variables d'environnement

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key_here
```

### Structure de la table `licenses`

```sql
CREATE TABLE licenses (
    id SERIAL PRIMARY KEY,
    license_key VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    last_used TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER DEFAULT 0,
    max_usage INTEGER DEFAULT -1, -- -1 = illimité
    notes TEXT,
    is_archived BOOLEAN DEFAULT false,
    client_id UUID
);
```

## Fonctionnalités

### 1. Validation en temps réel

- **Vérification automatique** : À chaque requête sur les routes protégées
- **Validation Supabase** : Interrogation directe de l'API REST
- **Critères de validation** :
  - `is_active = true`
  - `expires_at > now()`
  - `is_archived = false`
  - `usage_count < max_usage` (si max_usage > 0)

### 2. Gestion locale

- **Stockage sécurisé** : Dans `app/services/credentials.json`
- **Structure locale** :
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

### 3. Interface utilisateur

#### Page de configuration

- **Section Licence** dans la sidebar
- **Champ sécurisé** pour la clé de licence
- **Indicateur de validité** en temps réel
- **Bouton d'actualisation** pour revérifier
- **Sauvegarde automatique** même pour les clés invalides

#### Page de licence expirée

- **Interface dédiée** avec informations détaillées
- **Bouton de revérification** avec modal moderne
- **Rafraîchissement automatique** toutes les 5 minutes
- **Notifications élégantes** au lieu d'alertes

### 4. Sécurité

#### Middleware de protection

```python
# Routes protégées
protected_routes = [
    "/", "/transfer", "/transfer-batisimply",
    "/recup-heures", "/update-code-projet",
    "/transfer-heure-batigest", "/sync-batigest-to-batisimply",
    "/sync-batisimply-to-batigest"
]

# Routes exclues
excluded_routes = [
    "/login", "/configuration", "/static",
    "/favicon.ico", "/license-expired",
    "/update-license", "/refresh-license"
]
```

#### Vérification automatique

- **Au chargement des pages** : JavaScript vérifie le statut
- **Sur les routes protégées** : Middleware bloque l'accès
- **Redirection intelligente** : Configuration ou licence expirée

## API Endpoints

### Routes de licence

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/check-license-status` | Vérification du statut de la licence |
| `GET` | `/get-license-key` | Récupération de la clé locale |
| `POST` | `/update-license` | Mise à jour de la clé de licence |
| `POST` | `/refresh-license` | Rafraîchissement de la validation |
| `GET` | `/license-expired` | Page de licence expirée |

### Réponses JSON

#### `/check-license-status`

```json
{
  "valid": true,
  "message": "Licence valide"
}
```

#### `/get-license-key`

```json
{
  "license_key": "XXXX-XXXX-XXXX-XXXX",
  "found": true
}
```

#### `/refresh-license`

```json
{
  "success": true,
  "message": "Licence validée avec succès",
  "expires_at": "2027-06-23T09:46:12.23389+00:00",
  "client_name": "Client XXXXX"
}
```

## Utilisation

### Configuration initiale

1. **Accéder à la configuration**
   ```
   http://localhost:8000/configuration
   ```

2. **Section Licence**
   - Saisir la clé de licence fournie
   - Cliquer sur "Enregistrer la licence"
   - Vérifier l'indicateur de validité

3. **Validation automatique**
   - La licence est validée en temps réel
   - Les informations sont sauvegardées localement
   - L'accès aux fonctionnalités est débloqué

### Gestion quotidienne

#### Actualisation manuelle

- Utiliser le bouton "Actualiser" dans la configuration
- Modal de chargement de 1 seconde
- Notification du résultat

#### Vérification automatique

- **Middleware** : À chaque requête sur les routes protégées
- **JavaScript** : Au chargement des pages principales
- **Page expirée** : Rafraîchissement toutes les 5 minutes

### Dépannage

#### Licence invalide

1. **Vérifier la clé** dans la configuration
2. **Utiliser "Actualiser"** pour revérifier
3. **Contacter le support** si le problème persiste

#### Erreurs de connexion

1. **Vérifier l'accès Internet**
2. **Vérifier les variables d'environnement Supabase**
3. **Consulter les logs** pour plus de détails

## Logs et diagnostic

### Logs détaillés

Le système génère des logs détaillés pour le diagnostic :

```
🔍 Validation de la clé: 5F59-1AF...
🌐 URL de requête: https://your-project.supabase.co/rest/v1/licenses?license_key=eq.XXXX
📡 Statut de la réponse: 200
📊 Données reçues: 1 licences trouvées
📋 Licence trouvée: ID 5
✅ is_active: True
📅 expires_at: 2027-06-23T09:46:12.23389+00:00
🕐 Maintenant: 2025-06-24 09:06:03.502717+00:00
🕐 Expire le: 2027-06-23 09:46:12.233890+00:00
✅ Licence non expirée
📊 usage_count: 0, max_usage: -1
✅ Usage illimité
📦 is_archived: False
✅ Licence valide
```

### Test de connexion

Utiliser le script de test :
```bash
python test_supabase_connection.py
```

## Sécurité et bonnes pratiques

### Stockage sécurisé

- Les clés sont stockées localement dans `credentials.json`
- Aucune transmission de clés en clair
- Validation via API sécurisée uniquement

### Validation robuste

- Vérification de tous les critères de validité
- Gestion des cas d'erreur et timeouts
- Logs détaillés pour le diagnostic

### Interface utilisateur

- Feedback visuel en temps réel
- Messages d'erreur explicites
- Expérience utilisateur fluide

## Support

Pour toute question concernant les licences :
- **Email** : support@groupe-sages.fr
- **Téléphone** : +33 04 67 34 01 01

---

*Dernière mise à jour : 24/06/2025*