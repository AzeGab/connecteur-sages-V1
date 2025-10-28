# app/services/batigest/sqlserver_to_batisimply.py
# Module de gestion du flux SQL Server -> PostgreSQL -> BatiSimply
# Ce fichier contient les fonctions pour transférer les données depuis Batigest (SQL Server) vers BatiSimply

import psycopg2
import requests
import json
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Iterable, Optional
from app.services.connex import connect_to_sqlserver, connect_to_postgres, load_credentials, recup_batisimply_token


def _record_from_row(columns: Iterable[str], row) -> Dict[str, object]:
    """
    Construit un dictionnaire {colonne: valeur} à partir d'un résultat SQL Server.
    Les noms de colonnes sont normalisés en minuscules pour simplifier les accès.
    """
    return {columns[idx].lower(): row[idx] for idx in range(len(columns))}


def _pick(record: Dict[str, object], keys: Iterable[str], fallback_contains: Optional[Iterable[str]] = None):
    """
    Recherche la première valeur non vide correspondant à une liste de clés.
    Peut également utiliser des sous-chaînes pour trouver une colonne alternative.
    """
    for key in keys:
        value = record.get(key.lower())
        if value not in (None, ""):
            return value
    if fallback_contains:
        for column, value in record.items():
            if value in (None, ""):
                continue
            if any(token in column for token in fallback_contains):
                return value
    return None


def _normalize_date(value):
    """
    Convertit une valeur SQL Server en date (datetime.date) compatible PostgreSQL.
    """
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%d/%m/%Y %H:%M:%S"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    return None


def _normalize_float(value):
    """
    Convertit les valeurs numériques (Decimal, int, str) en float.
    """
    if value is None:
        return None
    if isinstance(value, float):
        return value
    if isinstance(value, (int, Decimal)):
        return float(value)
    if isinstance(value, str):
        candidate = value.replace(",", ".").strip()
        if not candidate:
            return None
        try:
            return float(candidate)
        except ValueError:
            return None
    return None


def _clean_str(value):
    """
    Nettoie les chaînes (trim) et retourne None pour les chaînes vides.
    """
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    return str(value)

# ============================================================================
# TRANSFERT DES CHANTIERS SQL SERVER -> POSTGRESQL -> BATISIMPLY
# ============================================================================

def transfer_chantiers_sqlserver_to_postgres():
    """
    Transfère les chantiers depuis SQL Server (Batigest) vers PostgreSQL.
    """
    try:
        # Vérification des identifiants
        creds = load_credentials()
        if not creds or "sqlserver" not in creds or "postgres" not in creds:
            return False, "❌ Informations de connexion manquantes"

        # Établissement des connexions
        sqlserver_conn = connect_to_sqlserver(
            creds["sqlserver"]["server"],
            creds["sqlserver"]["user"],
            creds["sqlserver"]["password"],
            creds["sqlserver"]["database"]
        )
        postgres_conn = connect_to_postgres(
            creds["postgres"]["host"],
            creds["postgres"]["user"],
            creds["postgres"]["password"],
            creds["postgres"]["database"],
            creds["postgres"].get("port", "5432")
        )
        
        if not sqlserver_conn or not postgres_conn:
            return False, "❌ Connexion aux bases échouée"

        # Création des curseurs
        sqlserver_cursor = sqlserver_conn.cursor()
        postgres_cursor = postgres_conn.cursor()

        # Requête pour récupérer les chantiers depuis SQL Server
        query_sqlserver = """
        SELECT *
        FROM dbo.ChantierDef
        WHERE Etat = 'E'
        """
        
        try:
            sqlserver_cursor.execute(query_sqlserver)
            chantiers_rows = sqlserver_cursor.fetchall()
            columns = [col[0] for col in sqlserver_cursor.description]
        except Exception as sql_error:
            return False, f"❌ Erreur SQL Server - Table 'Chantier' introuvable. Vérifiez le nom de la table dans votre base de données. Erreur: {str(sql_error)}"

        # Insertion dans PostgreSQL avec gestion des conflits
        inserted_rows = 0
        for chantier_row in chantiers_rows:
            record = _record_from_row(columns, chantier_row)
            code = _clean_str(record.get("code"))
            if not code:
                continue

            date_debut = _normalize_date(record.get("datedebut"))
            date_fin = _normalize_date(record.get("datefin"))

            nom_client = _clean_str(
                _pick(record, ["nomclient", "client", "nom"], fallback_contains=["client"])
            ) or f"Chantier {code}"

            description = _clean_str(
                _pick(record, ["description", "libelle", "nom", "objet"], fallback_contains=["lib"])
            ) or nom_client

            adr_chantier = _clean_str(
                _pick(
                    record,
                    ["adrchantier", "adressechantier", "adresse1", "adresse"],
                    fallback_contains=["adr", "adresse"]
                )
            )
            cp_chantier = _clean_str(
                _pick(
                    record,
                    ["cpchantier", "codepostalchantier", "cp", "codepostal"],
                    fallback_contains=["cp", "postal"]
                )
            )
            ville_chantier = _clean_str(
                _pick(
                    record,
                    ["villechantier", "ville"],
                    fallback_contains=["ville", "city"]
                )
            )
            total_mo = _normalize_float(
                _pick(
                    record,
                    ["totalmo", "tempsmo", "montantmo", "totmo"],
                    fallback_contains=["mo"]
                )
            )

            now_utc = datetime.utcnow()

            query_postgres = """
            INSERT INTO batigest_chantiers (
                code,
                date_debut,
                date_fin,
                nom_client,
                description,
                adr_chantier,
                cp_chantier,
                ville_chantier,
                total_mo,
                sync,
                sync_date,
                last_modified_batigest
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE, %s, %s)
            ON CONFLICT (code) DO UPDATE SET
                date_debut = EXCLUDED.date_debut,
                date_fin = EXCLUDED.date_fin,
                nom_client = EXCLUDED.nom_client,
                description = EXCLUDED.description,
                adr_chantier = EXCLUDED.adr_chantier,
                cp_chantier = EXCLUDED.cp_chantier,
                ville_chantier = EXCLUDED.ville_chantier,
                total_mo = EXCLUDED.total_mo,
                sync = FALSE,
                sync_date = EXCLUDED.sync_date,
                last_modified_batigest = EXCLUDED.last_modified_batigest
            """
            
            postgres_cursor.execute(
                query_postgres,
                (
                    code,
                    date_debut,
                    date_fin,
                    nom_client,
                    description,
                    adr_chantier,
                    cp_chantier,
                    ville_chantier,
                    total_mo,
                    now_utc,
                    now_utc,
                )
            )
            inserted_rows += 1

        postgres_conn.commit()
        message_success = f"✅ {inserted_rows} chantier(s) transféré(s) depuis SQL Server vers PostgreSQL"
        
        # Fermeture des connexions
        sqlserver_cursor.close()
        postgres_cursor.close()
        sqlserver_conn.close()
        postgres_conn.close()

        return True, message_success

    except Exception as e:
        return False, f"❌ Erreur lors du transfert SQL Server -> PostgreSQL : {str(e)}"

def transfer_chantiers_postgres_to_batisimply():
    """
    Transfère les chantiers depuis PostgreSQL vers BatiSimply.
    """
    try:
        # Vérification des identifiants
        creds = load_credentials()
        if not creds or "postgres" not in creds:
            return False, "❌ Informations de connexion manquantes"

        # Récupération du token BatiSimply
        token = recup_batisimply_token()
        if not token:
            return False, "❌ Impossible de récupérer le token BatiSimply"

        # Connexion PostgreSQL
        postgres_conn = connect_to_postgres(
            creds["postgres"]["host"],
            creds["postgres"]["user"],
            creds["postgres"]["password"],
            creds["postgres"]["database"],
            creds["postgres"].get("port", "5432")
        )
        if not postgres_conn:
            return False, "❌ Connexion PostgreSQL échouée"

        postgres_cursor = postgres_conn.cursor()

        # Récupération des chantiers non synchronisés
        query = "SELECT * FROM batigest_chantiers WHERE sync = FALSE"
        postgres_cursor.execute(query)
        chantiers = postgres_cursor.fetchall()

        # Envoi vers BatiSimply
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        for chantier in chantiers:
            # Structure: id, code, date_debut, date_fin, nom_client, description, adr_chantier, cp_chantier, ville_chantier, sync_date, sync, total_mo, last_modified_batisimply, last_modified_batigest
            id, code, date_debut, date_fin, nom_client, description, adr_chantier, cp_chantier, ville_chantier, sync_date, sync, total_mo, last_modified_batisimply, last_modified_batigest = chantier
            
            # Préparation des données pour BatiSimply (format qui fonctionnait)
            # Formatage de l'adresse : "rue, code postal, ville, France"
            adresse_complete = f"{adr_chantier or ''}, {cp_chantier or ''}, {ville_chantier or ''}, France"
            # Nettoyage des virgules multiples et espaces
            adresse_complete = ", ".join([part.strip() for part in adresse_complete.split(",") if part.strip()])
            
            data = {
                "address": {
                    "city": ville_chantier or "",
                    "countryCode": "FR",
                    "geoPoint": {
                        "xLon": 3.8777,
                        "yLat": 43.6119
                    },
                    "googleFormattedAddress": adresse_complete,
                    "postalCode": cp_chantier or "",
                    "street": adr_chantier or ""
                },
                "budget": {
                    "amount": 500000.0,
                    "currency": "EUR"
                },
                "endEstimated": date_fin.strftime("%Y-%m-%d") if date_fin else None,
                "headQuarter": {
                    "id": 33
                },
                "hoursSold": float(total_mo) if total_mo is not None else 0,
                "projectCode": code,
                "comment": description or f"Chantier {code}",
                "projectName": nom_client or f"Chantier {code}",
                "customerName": nom_client or f"Chantier {code}",
                "projectManager": "DEFINIR",
                "startEstimated": date_debut.strftime("%Y-%m-%d") if date_debut else None,
                "isArchived": False,
                "isFinished": False,
                "projectColor": "#9b1ff1"
            }

            # Envoi vers l'API BatiSimply
            response = requests.post(
                'https://api.staging.batisimply.fr/api/project',
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code in [200, 201]:
                # Marquer comme synchronisé
                update_query = "UPDATE batigest_chantiers SET sync = TRUE WHERE code = %s"
                postgres_cursor.execute(update_query, (code,))
            else:
                print(f"⚠️ Erreur lors de l'envoi du chantier {code}: {response.status_code}")

        postgres_conn.commit()
        postgres_cursor.close()
        postgres_conn.close()

        return True, f"✅ {len(chantiers)} chantier(s) envoyé(s) vers BatiSimply"

    except Exception as e:
        return False, f"❌ Erreur lors du transfert PostgreSQL -> BatiSimply : {str(e)}"

# ============================================================================
# TRANSFERT DES HEURES SQL SERVER -> POSTGRESQL -> BATISIMPLY
# ============================================================================

def transfer_heures_sqlserver_to_postgres():
    """
    Transfère les heures depuis SQL Server (Batigest) vers PostgreSQL.
    """
    try:
        # Vérification des identifiants
        creds = load_credentials()
        if not creds or "sqlserver" not in creds or "postgres" not in creds:
            return False, "❌ Informations de connexion manquantes"

        # Établissement des connexions
        sqlserver_conn = connect_to_sqlserver(
            creds["sqlserver"]["server"],
            creds["sqlserver"]["user"],
            creds["sqlserver"]["password"],
            creds["sqlserver"]["database"]
        )
        postgres_conn = connect_to_postgres(
            creds["postgres"]["host"],
            creds["postgres"]["user"],
            creds["postgres"]["password"],
            creds["postgres"]["database"],
            creds["postgres"].get("port", "5432")
        )
        
        if not sqlserver_conn or not postgres_conn:
            return False, "❌ Connexion aux bases échouée"

        # Création des curseurs
        sqlserver_cursor = sqlserver_conn.cursor()
        postgres_cursor = postgres_conn.cursor()

        # Requête pour récupérer les heures depuis SQL Server
        query_sqlserver = """
        SELECT CodeChantier, CodeSalarie, Date, Heures, Commentaire
        FROM dbo.SuiviMO
        WHERE Date >= DATEADD(day, -30, GETDATE())
        """
        
        sqlserver_cursor.execute(query_sqlserver)
        heures = sqlserver_cursor.fetchall()

        # Insertion dans PostgreSQL avec gestion des conflits
        for heure in heures:
            code_chantier, code_salarie, date_heure, heures, commentaire = heure
            
            query_postgres = """
            INSERT INTO batigest_heures (code_chantier, code_salarie, date_heure, heures, commentaire, sync)
            VALUES (%s, %s, %s, %s, %s, FALSE)
            ON CONFLICT (code_chantier, code_salarie, date_heure) DO UPDATE SET
                heures = EXCLUDED.heures,
                commentaire = EXCLUDED.commentaire,
                sync = FALSE
            """
            
            postgres_cursor.execute(query_postgres, (code_chantier, code_salarie, date_heure, heures, commentaire))

        postgres_conn.commit()
        
        # Fermeture des connexions
        sqlserver_cursor.close()
        postgres_cursor.close()
        sqlserver_conn.close()
        postgres_conn.close()

        return True, f"✅ {len(heures)} heure(s) transférée(s) depuis SQL Server vers PostgreSQL"

    except Exception as e:
        return False, f"❌ Erreur lors du transfert SQL Server -> PostgreSQL : {str(e)}"

def transfer_heures_postgres_to_batisimply():
    """
    Transfère les heures depuis PostgreSQL vers BatiSimply.
    """
    try:
        # Vérification des identifiants
        creds = load_credentials()
        if not creds or "postgres" not in creds:
            return False, "❌ Informations de connexion manquantes"

        # Récupération du token BatiSimply
        token = recup_batisimply_token()
        if not token:
            return False, "❌ Impossible de récupérer le token BatiSimply"

        # Connexion PostgreSQL
        postgres_conn = connect_to_postgres(
            creds["postgres"]["host"],
            creds["postgres"]["user"],
            creds["postgres"]["password"],
            creds["postgres"]["database"],
            creds["postgres"].get("port", "5432")
        )
        if not postgres_conn:
            return False, "❌ Connexion PostgreSQL échouée"

        postgres_cursor = postgres_conn.cursor()

        # Récupération des heures non synchronisées
        query = "SELECT * FROM batigest_heures WHERE sync = FALSE"
        postgres_cursor.execute(query)
        heures = postgres_cursor.fetchall()

        # Envoi vers BatiSimply
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        for heure in heures:
            code_chantier, code_salarie, date_heure, heures, commentaire, sync = heure
            
            # Préparation des données pour BatiSimply
            data = {
                "projectId": code_chantier,
                "userId": code_salarie,
                "date": date_heure.isoformat(),
                "hours": float(heures),
                "comment": commentaire
            }

            # Envoi vers l'API BatiSimply
            response = requests.post(
                'https://api.staging.batisimply.fr/api/timeSlotManagement',
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code in [200, 201]:
                # Marquer comme synchronisé
                update_query = "UPDATE batigest_heures SET sync = TRUE WHERE code_chantier = %s AND code_salarie = %s AND date_heure = %s"
                postgres_cursor.execute(update_query, (code_chantier, code_salarie, date_heure))
            else:
                print(f"⚠️ Erreur lors de l'envoi de l'heure {code_chantier}-{code_salarie}: {response.status_code}")

        postgres_conn.commit()
        postgres_cursor.close()
        postgres_conn.close()

        return True, f"✅ {len(heures)} heure(s) envoyée(s) vers BatiSimply"

    except Exception as e:
        return False, f"❌ Erreur lors du transfert PostgreSQL -> BatiSimply : {str(e)}"

# ============================================================================
# TRANSFERT DES DEVIS SQL SERVER -> POSTGRESQL -> BATISIMPLY
# ============================================================================

def transfer_devis_sqlserver_to_postgres():
    """
    Transfère les devis depuis SQL Server (Batigest) vers PostgreSQL.
    """
    try:
        # Vérification des identifiants
        creds = load_credentials()
        if not creds or "sqlserver" not in creds or "postgres" not in creds:
            return False, "❌ Informations de connexion manquantes"

        # Établissement des connexions
        sqlserver_conn = connect_to_sqlserver(
            creds["sqlserver"]["server"],
            creds["sqlserver"]["user"],
            creds["sqlserver"]["password"],
            creds["sqlserver"]["database"]
        )
        postgres_conn = connect_to_postgres(
            creds["postgres"]["host"],
            creds["postgres"]["user"],
            creds["postgres"]["password"],
            creds["postgres"]["database"],
            creds["postgres"].get("port", "5432")
        )
        
        if not sqlserver_conn or not postgres_conn:
            return False, "❌ Connexion aux bases échouée"

        # Création des curseurs
        sqlserver_cursor = sqlserver_conn.cursor()
        postgres_cursor = postgres_conn.cursor()

        # Requête pour récupérer les devis depuis SQL Server
        query_sqlserver = """
        SELECT *
        FROM dbo.Devis
        WHERE Etat IN (0, 3, 4)
        """
        
        sqlserver_cursor.execute(query_sqlserver)
        devis_rows = sqlserver_cursor.fetchall()
        devis_columns = [col[0] for col in sqlserver_cursor.description]

        inserted_rows = 0

        # Insertion dans PostgreSQL avec gestion des conflits
        for devi in devis_rows:
            record = _record_from_row(devis_columns, devi)
            code = _clean_str(record.get("code"))
            if not code:
                continue

            date_devis = _normalize_date(
                _pick(record, ["date", "datecreation", "datedevis", "dateemission"])
            )
            nom = _clean_str(
                _pick(record, ["nom", "libelle", "intitule", "description"], fallback_contains=["nom"])
            ) or f"Devis {code}"
            adr = _clean_str(
                _pick(
                    record,
                    ["adr", "adresse", "adressechantier", "adresseclient", "adressefact"],
                    fallback_contains=["adr", "adresse"]
                )
            )
            cp = _clean_str(
                _pick(
                    record,
                    ["cp", "codepostal", "codepostalchantier", "codepostalclient", "codepostalfact"],
                    fallback_contains=["cp", "postal"]
                )
            )
            ville = _clean_str(
                _pick(
                    record,
                    ["ville", "villechantier", "villeclient", "villefact"],
                    fallback_contains=["ville", "city"]
                )
            )
            sujet = _clean_str(
                _pick(record, ["sujet", "description", "libelle"], fallback_contains=["sujet"])
            ) or nom
            date_concretisation = _normalize_date(
                _pick(
                    record,
                    ["dateconcretis", "datevalidation", "dateacceptation", "dateconclusion"]
                )
            )
            temps_mo = _normalize_float(
                _pick(record, ["tempsmo", "totalmo", "montantmo", "totmo", "heuresmo"], fallback_contains=["mo"])
            )

            now_utc = datetime.utcnow()

            query_postgres = """
            INSERT INTO batigest_devis (
                code,
                date,
                nom,
                adr,
                cp,
                ville,
                sujet,
                dateconcretis,
                tempsmo,
                sync_date,
                sync
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE)
            ON CONFLICT (code) DO UPDATE SET
                date = EXCLUDED.date,
                nom = EXCLUDED.nom,
                adr = EXCLUDED.adr,
                cp = EXCLUDED.cp,
                ville = EXCLUDED.ville,
                sujet = EXCLUDED.sujet,
                dateconcretis = EXCLUDED.dateconcretis,
                tempsmo = EXCLUDED.tempsmo,
                sync_date = EXCLUDED.sync_date,
                sync = FALSE
            """
            
            postgres_cursor.execute(
                query_postgres,
                (
                    code,
                    date_devis,
                    nom,
                    adr,
                    cp,
                    ville,
                    sujet,
                    date_concretisation,
                    temps_mo,
                    now_utc,
                )
            )
            inserted_rows += 1

        postgres_conn.commit()
        message_success = f"✅ {inserted_rows} devis transféré(s) depuis SQL Server vers PostgreSQL"
        
        # Fermeture des connexions
        sqlserver_cursor.close()
        postgres_cursor.close()
        sqlserver_conn.close()
        postgres_conn.close()

        return True, message_success

    except Exception as e:
        return False, f"❌ Erreur lors du transfert SQL Server -> PostgreSQL : {str(e)}"

def transfer_devis_postgres_to_batisimply():
    """
    Transfère les devis depuis PostgreSQL vers BatiSimply.
    """
    try:
        # Vérification des identifiants
        creds = load_credentials()
        if not creds or "postgres" not in creds:
            return False, "❌ Informations de connexion manquantes"

        # Récupération du token BatiSimply
        token = recup_batisimply_token()
        if not token:
            return False, "❌ Impossible de récupérer le token BatiSimply"

        # Connexion PostgreSQL
        postgres_conn = connect_to_postgres(
            creds["postgres"]["host"],
            creds["postgres"]["user"],
            creds["postgres"]["password"],
            creds["postgres"]["database"],
            creds["postgres"].get("port", "5432")
        )
        if not postgres_conn:
            return False, "❌ Connexion PostgreSQL échouée"

        postgres_cursor = postgres_conn.cursor()

        # Récupération des devis non synchronisés
        query = "SELECT * FROM batigest_devis WHERE sync = FALSE"
        postgres_cursor.execute(query)
        devis = postgres_cursor.fetchall()

        # Envoi vers BatiSimply
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        for devi in devis:
            # Structure: code, date, nom, adr, cp, ville, sujet, dateconcretis, tempsmo, sync_date, sync
            code, date, nom, adr, cp, ville, sujet, dateconcretis, tempsmo, sync_date, sync = devi
            
            # Préparation des données pour BatiSimply
            data = {
                "name": nom,
                "creationDate": date.isoformat() if date else None,
                "amount": float(tempsmo) if tempsmo else 0,
                "status": "En cours",
                "clientCode": code
            }

            # Envoi vers l'API BatiSimply
            response = requests.post(
                'https://api.staging.batisimply.fr/api/quote',
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code in [200, 201]:
                # Marquer comme synchronisé
                update_query = "UPDATE batigest_devis SET sync = TRUE WHERE code = %s"
                postgres_cursor.execute(update_query, (code,))
            else:
                print(f"⚠️ Erreur lors de l'envoi du devis {code}: {response.status_code}")

        postgres_conn.commit()
        postgres_cursor.close()
        postgres_conn.close()

        return True, f"✅ {len(devis)} devi(s) envoyé(s) vers BatiSimply"

    except Exception as e:
        return False, f"❌ Erreur lors du transfert PostgreSQL -> BatiSimply : {str(e)}"

# ============================================================================
# FONCTIONS DE SYNCHRONISATION COMPLÈTE
# ============================================================================

def sync_sqlserver_to_batisimply():
    """
    Synchronisation complète SQL Server -> PostgreSQL -> BatiSimply.
    """
    print("=== DÉBUT DE LA SYNCHRONISATION SQL SERVER → BATISIMPLY ===")
    messages = []
    overall_success = True
    
    try:
        # 1. Transfert des chantiers
        print("🔄 Synchronisation des chantiers...")
        success, message = transfer_chantiers_sqlserver_to_postgres()
        print(message)
        messages.append(message)
        
        if success:
            success, message = transfer_chantiers_postgres_to_batisimply()
            print(message)
            messages.append(message)
            if not success:
                overall_success = False
        else:
            overall_success = False
        
        # 2. Transfert des devis
        print("🔄 Synchronisation des devis...")
        success, message = transfer_devis_sqlserver_to_postgres()
        print(message)
        messages.append(message)
        
        if success:
            success, message = transfer_devis_postgres_to_batisimply()
            print(message)
            messages.append(message)
            if not success:
                overall_success = False
        else:
            overall_success = False
        
        print("=== FIN DE LA SYNCHRONISATION SQL SERVER → BATISIMPLY ===")
        
        if overall_success:
            return True, "✅ Synchronisation SQL Server → BatiSimply terminée avec succès"
        else:
            return False, "⚠️ Synchronisation SQL Server → BatiSimply terminée avec des erreurs"
            
    except Exception as e:
        error_msg = f"❌ Erreur lors de la synchronisation SQL Server → BatiSimply : {str(e)}"
        print(error_msg)
        return False, error_msg
