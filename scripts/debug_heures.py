import argparse
from datetime import datetime, timedelta
import os
import sys
from typing import Optional

import requests

# Assurer l'import du package app/ quand le script est appelé directement
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.services.connex import (
    load_credentials,
    connect_to_postgres,
    connect_to_sqlserver,
    recup_batisimply_token,
)
from app.services.chantier import update_code_projet_chantiers
from app.services.heures import transfer_heures_to_sqlserver


def iso_utc_start(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT00:00:00Z")


def iso_utc_end(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT23:59:59Z")


def print_header(title: str) -> None:
    print("\n" + "=" * 10 + f" {title} " + "=" * 10)


def fetch_batisimply_timeslots(start: datetime, end: datetime, verbose: bool = True):
    token = recup_batisimply_token()
    if not token:
        print("❌ Token BatiSimply manquant.")
        return []

    api_url = "https://api.staging.batisimply.fr/api/timeSlotManagement/allUsers"
    params = {"startDate": iso_utc_start(start), "endDate": iso_utc_end(end)}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    if verbose:
        print(f"🔎 Appel API BatiSimply: {api_url}")
        print(f"    startDate={params['startDate']}  endDate={params['endDate']}")

    resp = requests.get(api_url, headers=headers, params=params)
    if resp.status_code != 200:
        print(f"❌ Erreur API {resp.status_code}: {resp.text}")
        return []

    heures = resp.json()
    if verbose:
        print(f"📦 {len(heures)} créneau(x) retourné(s) par l'API")
    return heures


def check_postgres_presence(id_heure: str, verbose: bool = True) -> Optional[tuple]:
    creds = load_credentials()
    if not creds or "postgres" not in creds:
        print("❌ Informations Postgres manquantes dans credentials.json")
        return None
    pg = creds["postgres"]
    conn = connect_to_postgres(pg["host"], pg["user"], pg["password"], pg["database"], pg.get("port", "5432"))
    if not conn:
        print("❌ Connexion Postgres échouée")
        return None
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id_heure, date_debut, id_utilisateur, id_projet, code_projet,
               status_management, total_heure, panier, trajet, sync
        FROM batigest_heures
        WHERE id_heure = %s
        """,
        (id_heure,),
    )
    row = cur.fetchone()
    conn.close()
    if verbose:
        if row:
            print(
                f"✅ PG trouvé: id={row[0]} date_debut={row[1]} user={row[2]} id_proj={row[3]} code_proj={row[4]} "
                f"status={row[5]} total={row[6]} panier={row[7]} trajet={row[8]} sync={row[9]}"
            )
        else:
            print("⚠️ PG: aucune ligne trouvée pour id_heure", id_heure)
    return row


def check_sqlserver_presence(code_chantier: str, code_salarie: str, date_debut, verbose: bool = True) -> Optional[tuple]:
    creds = load_credentials()
    if not creds or "sqlserver" not in creds:
        print("❌ Infos SQL Server manquantes dans credentials.json")
        return None
    sql = creds["sqlserver"]
    conn = connect_to_sqlserver(sql["server"], sql["user"], sql["password"], sql["database"])
    if not conn:
        print("❌ Connexion SQL Server échouée")
        return None
    cur = conn.cursor()
    cur.execute(
        """
        SELECT [CodeChantier], [CodeSalarie], [Date], [NbH0], [NbH3], [NbH4]
        FROM SuiviMO
        WHERE [CodeChantier] = ? AND [CodeSalarie] = ? AND [Date] = ?
        """,
        (code_chantier, code_salarie, date_debut),
    )
    row = cur.fetchone()
    conn.close()
    if verbose:
        if row:
            print(f"✅ SuiviMO trouvé: {row}")
        else:
            print("ℹ️ SuiviMO: aucune ligne pour cette clé fonctionnelle")
    return row


def resolve_code_salarie_from_user(user_uuid: str, verbose: bool = True) -> Optional[str]:
    creds = load_credentials()
    if not creds or "sqlserver" not in creds:
        print("❌ Infos SQL Server manquantes")
        return None
    sql = creds["sqlserver"]
    conn = connect_to_sqlserver(sql["server"], sql["user"], sql["password"], sql["database"])
    if not conn:
        print("❌ Connexion SQL Server échouée")
        return None
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1 Code FROM Salarie WHERE codebs = ?
        """,
        (user_uuid,),
    )
    row = cur.fetchone()
    conn.close()
    if verbose:
        if row:
            print(f"✅ Mapping Salarie: codebs={user_uuid} → Code={row[0]}")
        else:
            print(f"⚠️ Aucun salarié trouvé avec codebs={user_uuid}")
    return row[0] if row else None


def main():
    parser = argparse.ArgumentParser(description="Debug synchro heures BatiSimply → PG → SQL Server")
    parser.add_argument("--days", type=int, default=7, help="Fenêtre de jours à remonter depuis aujourd'hui (défaut: 7)")
    parser.add_argument("--id-heure", type=str, help="Filtrer sur un id_heure précis (optionnel)")
    parser.add_argument("--update-codes", action="store_true", help="Exécuter update_code_projet_chantiers() avant vérifs")
    parser.add_argument("--apply", action="store_true", help="Appliquer la synchro PG → SQL Server (transfer_heures_to_sqlserver)")
    parser.add_argument("--verbose", action="store_true", help="Logs verbeux")
    args = parser.parse_args()

    start = datetime.utcnow() - timedelta(days=args.days)
    end = datetime.utcnow()

    print_header("Récupération BatiSimply")
    heures = fetch_batisimply_timeslots(start, end, verbose=args.verbose)
    if args.id_heure:
        heures = [h for h in heures if str(h.get("id")) == args.id_heure]
        print(f"🎯 Filtre id_heure={args.id_heure} → {len(heures)} résultat(s)")

    for h in heures:
        h_id = h.get("id")
        status = h.get("managementStatus")
        user_uuid = h.get("user", {}).get("id")
        proj_id = h.get("project", {}).get("id")
        start_date = h.get("startDate")
        end_date = h.get("endDate")
        total = h.get("totalTimeMinutes")
        print(f"\n🕒 Heure: id={h_id} status={status} user={user_uuid} proj={proj_id} start={start_date} end={end_date} total={total}")

        print_header("PostgreSQL → batigest_heures")
        row = check_postgres_presence(str(h_id), verbose=True)

        if args.update_codes:
            print("\n🔄 Mise à jour des codes projet (update_code_projet_chantiers)...")
            update_code_projet_chantiers()
            # Relire après MAJ
            row = check_postgres_presence(str(h_id), verbose=True)

        if row:
            _, date_debut, id_utilisateur, _, code_projet, status_mgmt, total_heure, panier, trajet, sync = row
            if status_mgmt != "VALIDATED":
                print("⏭️ Statut ≠ VALIDATED → non transféré vers SQL Server")
                continue
            if not code_projet:
                print("⏭️ code_projet manquant → non transféré")
                continue

            print_header("SQL Server → Résolution Salarie + SuiviMO")
            code_salarie = resolve_code_salarie_from_user(id_utilisateur, verbose=True)
            if not code_salarie:
                print("⏭️ Mapping salarié indisponible → non transféré")
                continue
            check_sqlserver_presence(code_projet, code_salarie, date_debut, verbose=True)

    if args.apply:
        print_header("Application synchro PG → SQL Server")
        count = transfer_heures_to_sqlserver()
        print(f"✅ Heures traitées: {count}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        print("❌ Erreur dans le script:", e)
        sys.exit(1)


