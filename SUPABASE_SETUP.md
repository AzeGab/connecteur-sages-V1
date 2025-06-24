# Configuration Supabase pour les Licences

## 1. Création de la Table `licenses`

Dans votre projet Supabase, créez une nouvelle table avec le nom `licenses` :

### Structure de la Table

```sql
CREATE TABLE licenses (
    id SERIAL PRIMARY KEY,
    license_key VARCHAR(255) UNIQUE NOT NULL,
    client_name VARCHAR(255) NOT NULL,
    expiry_date DATE NOT NULL,
    features TEXT[] DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Colonnes Requises

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | SERIAL | Identifiant unique auto-incrémenté |
| `license_key` | VARCHAR(255) | Clé de licence unique |
| `client_name` | VARCHAR(255) | Nom du client |
| `expiry_date` | DATE | Date d'expiration de la licence |
| `features` | TEXT[] | Tableau des fonctionnalités autorisées |
| `status` | VARCHAR(50) | Statut de la licence (active, suspended, etc.) |
| `created_at` | TIMESTAMP | Date de création |
| `updated_at` | TIMESTAMP | Date de dernière modification |

## 2. Configuration des Permissions RLS (Row Level Security)

### Activer RLS
```sql
ALTER TABLE licenses ENABLE ROW LEVEL SECURITY;
```

### Politique pour la Lecture (Lecture seule pour les clients)
```sql
CREATE POLICY "Enable read access for all users" ON licenses
    FOR SELECT USING (true);
```

### Politique pour l'Administration (Optionnel)
```sql
-- Seulement pour les administrateurs (si vous avez une table users)
CREATE POLICY "Enable admin access" ON licenses
    FOR ALL USING (auth.role() = 'admin');
```

## 3. Insertion de Données de Test

### Exemple d'Insertion
```sql
INSERT INTO licenses (license_key, client_name, expiry_date, features, status) VALUES
('EVIDENCE-2024-XXXX-YYYY', 'Client Test', '2024-12-31', ARRAY['chantier', 'devis', 'heures'], 'active'),
('EVIDENCE-2024-ABCD-EFGH', 'Client Production', '2025-06-30', ARRAY['chantier', 'devis', 'heures', 'sync'], 'active'),
('EVIDENCE-2024-EXPIRED', 'Client Expiré', '2023-12-31', ARRAY['chantier'], 'expired');
```

## 4. Test de la Configuration

### Exécuter le Script de Test
```bash
python test_supabase_connection.py
```

Ce script va :
1. Tester la connexion à Supabase
2. Vérifier l'accès à la table `licenses`
3. Tester la validation d'une clé de licence

### Test Manuel avec curl
```bash
# Récupérer toutes les licences
curl "https://rxqveiaawggfyeukpvyz.supabase.co/rest/v1/licenses" \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ4cXZlaWFhd2dnZnlldWtwdnl6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA2NjQzMjAsImV4cCI6MjA2NjI0MDMyMH0.vYrxDe41M_a8XDcbHwmaiVfy8rKMsyNroiHvNHq5FAM" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ4cXZlaWFhd2dnZnlldWtwdnl6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA2NjQzMjAsImV4cCI6MjA2NjI0MDMyMH0.vYrxDe41M_a8XDcbHwmaiVfy8rKMsyNroiHvNHq5FAM"

# Tester une clé spécifique
curl "https://rxqveiaawggfyeukpvyz.supabase.co/rest/v1/licenses?license_key=eq.EVIDENCE-2024-XXXX-YYYY" \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ4cXZlaWFhd2dnZnlldWtwdnl6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA2NjQzMjAsImV4cCI6MjA2NjI0MDMyMH0.vYrxDe41M_a8XDcbHwmaiVfy8rKMsyNroiHvNHq5FAM" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ4cXZlaWFhd2dnZnlldWtwdnl6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA2NjQzMjAsImV4cCI6MjA2NjI0MDMyMH0.vYrxDe41M_a8XDcbHwmaiVfy8rKMsyNroiHvNHq5FAM"
```

## 5. Variables d'Environnement

Assurez-vous que votre fichier `.env` contient :

```env
SUPABASE_URL=https://rxqveiaawggfyeukpvyz.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ4cXZlaWFhd2dnZnlldWtwdnl6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA2NjQzMjAsImV4cCI6MjA2NjI0MDMyMH0.vYrxDe41M_a8XDcbHwmaiVfy8rKMsyNroiHvNHq5FAM
```

## 6. Sécurité

### Clé Anon vs Service Key
- **Clé Anon** : Utilisée dans l'application cliente (lecture seule)
- **Clé Service** : Utilisée côté serveur pour les opérations d'administration

### Permissions Recommandées
- L'application cliente ne doit avoir accès qu'en lecture
- Les opérations d'administration (création, modification, suppression) doivent être faites via une interface séparée

## 7. Monitoring et Logs

### Activer les Logs dans Supabase
1. Allez dans votre dashboard Supabase
2. Section "Logs" > "API"
3. Surveillez les requêtes vers la table `licenses`

### Métriques à Surveiller
- Nombre de validations de licences
- Erreurs d'accès à la base de données
- Temps de réponse des requêtes

## 8. Dépannage

### Erreurs Courantes

**Erreur 404 - Table non trouvée**
- Vérifiez que la table `licenses` existe
- Vérifiez l'orthographe du nom de la table

**Erreur 401 - Non autorisé**
- Vérifiez que la clé API est correcte
- Vérifiez les politiques RLS

**Erreur 403 - Accès refusé**
- Vérifiez les permissions de la clé anon
- Vérifiez les politiques RLS

### Test de Connexion
```python
import requests

url = "https://rxqveiaawggfyeukpvyz.supabase.co/rest/v1/licenses"
headers = {
    "apikey": "votre_clé_anon",
    "Authorization": "Bearer votre_clé_anon"
}

response = requests.get(url, headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
``` 