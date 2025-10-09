## Synchronisation des heures – Incrémental sans doublon (avec mapping)

Ce document explique comment la synchro BatiSimply → PostgreSQL → SQL Server fonctionne désormais pour éviter les doublons et gérer les modifications d'heures.

### TL;DR
- Les heures sont importées depuis BatiSimply sur une fenêtre glissante (par défaut 180 jours) et converties en heure locale.
- PostgreSQL garde la table `batigest_heures` en upsert. Si les données changent, `sync` repasse à `false` pour resynchroniser uniquement les lignes modifiées.
- Une table de mapping `batigest_heures_map` associe chaque `id_heure` BatiSimply à la « clé » SQL Server: `(CodeChantier, CodeSalarie, Date)`.
- Lors de l’envoi vers SQL Server:
  - Si la clé change, on met à jour la ligne existante vers la nouvelle clé/valeurs (au lieu de créer un doublon).
  - Sinon, on met simplement à jour les valeurs ou on insère si la ligne n’existe pas encore.
- Seules les heures VALIDATED et `NOT sync` sont traitées; on ne refait pas tout à chaque synchro.

---

### Schéma global
1) BatiSimply → PostgreSQL (`transfer_heures_to_postgres`)
- API: `timeSlotManagement/allUsers` avec fenêtre: `startDate` → `endDate`.
- Conversion Fuseau: UTC → `Europe/Paris` par défaut; secondes normalisées à `:00`.
- Upsert dans `batigest_heures`. Si une valeur change, `sync` ← `false`.

2) Mise à jour des codes projet (`update_code_projet_chantiers`)
- Alimente `code_projet` dans `batigest_heures` via correspondances code ↔ id_projet.

3) PostgreSQL → SQL Server (`transfer_heures_to_sqlserver`)
- Filtre: `status_management = 'VALIDATED' AND NOT sync`.
- Résolution du salarié: `Salarie.codebs = id_utilisateur` (UUID BatiSimply).
- Mapping par `id_heure` dans `batigest_heures_map`:
  - Si la clé a changé (chantier/salarié/date), on met à jour l’ancienne ligne vers la nouvelle clé et les nouvelles valeurs dans `SuiviMO`.
  - Sinon, on met à jour les valeurs ou on insère si nécessaire.
- Upsert du mapping avec la clé courante.
- Marquage `sync = true` uniquement pour les `id_heure` traités.

---

### DDL PostgreSQL
Créer la table de mapping si nécessaire:
```sql
CREATE TABLE IF NOT EXISTS batigest_heures_map (
  id_heure VARCHAR PRIMARY KEY,
  code_chantier VARCHAR NOT NULL,
  code_salarie VARCHAR NOT NULL,
  date_sqlserver TIMESTAMP NOT NULL
);
```

> La table est également créée automatiquement par le code lors de la synchro.

---

### Paramètres utiles (`credentials.json`)
```json
{
  "heures_window_days": 180,
  "timezone": "Europe/Paris"
}
```
- `heures_window_days`: fenêtre d’import depuis aujourd’hui vers le passé (en jours).
- `timezone`: conversion de l’UTC de l’API vers l’heure locale.

---

### Debug / Recette
- Script dédié:
```powershell
.\n+venv\Scripts\python.exe scripts\debug_heures.py --days 7 --verbose
```
- Cibler une heure précise et appliquer la synchro PG → SQL Server:
```powershell
.
venv\Scripts\python.exe scripts\debug_heures.py --id-heure 12345 --update-codes --apply --verbose
```
- Requêtes utiles:
```sql
-- PostgreSQL: heures à (re)traiter
SELECT id_heure, date_debut, id_utilisateur, code_projet, total_heure, sync
FROM batigest_heures
WHERE status_management = 'VALIDATED' AND NOT sync
ORDER BY date_debut DESC
LIMIT 20;

-- Mapping
SELECT * FROM batigest_heures_map WHERE id_heure = '12345';

-- SQL Server: contrôle de la ligne
SELECT TOP 20 [CodeChantier], [CodeSalarie], [Date], [NbH0], [NbH3], [NbH4]
FROM SuiviMO
ORDER BY [Date] DESC;
```

---

### Pourquoi plus de doublons ?
- Sans mapping, une modification (ex.: décaler 09:00 → 10:00) change la « clé » SQL Server et provoque un INSERT.
- Avec `batigest_heures_map`, le connecteur sait que cet `id_heure` existe déjà et migre proprement l’ancienne ligne vers la nouvelle clé/valeurs.

---

### Points d’attention
- `Salarie.codebs` doit être renseigné avec l’UUID BatiSimply pour chaque salarié.
- `code_projet` doit être présent pour l’envoi dans `SuiviMO`.
- Si une ligne SQL Server est supprimée manuellement, le connecteur réinsèrera ou mettra à jour en se basant sur l’état PostgreSQL.

---

### Références code
- `app/services/batigest/heures.py`:
  - `transfer_heures_to_postgres()`
  - `transfer_heures_to_sqlserver()` (logique mapping et upsert SQL Server)
- `app/services/batigest/heures.py`:
  - `update_code_projet_chantiers()`
- Routes UI: `app/routes/form_routes.py`


