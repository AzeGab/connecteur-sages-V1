import psycopg2
import requests
import json
from datetime import date
from app.services.connex import connect_to_sqlserver, connect_to_postgres, load_credentials, recup_batisimply_token, connexion


def transfer_devis():
    try:
        # Vérification des identifiants
        creds = load_credentials()
        if not creds or "sqlserver" not in creds or "postgres" not in creds:
            return False, "❌ Informations de connexion manquantes"

        # Établissement des connexions
        postgres_conn, sqlserver_conn = connexion()
        if not sqlserver_conn or not postgres_conn:
            return False, "❌ Connexion aux bases échouée"

        # Création des curseurs pour l'exécution des requêtes
        sqlserver_cursor = sqlserver_conn.cursor()
        postgres_cursor = postgres_conn.cursor()     

        sqlserver_cursor.execute("""
        select Code, Date, Nom, Adr, CP, Ville, Sujet, DateConcretis, TempsMO from Devis WHERE Etat = 3;
        """)   
    
        batigest_devis = sqlserver_cursor.fetchall()
        print(f"📊 {len(batigest_devis)} devis récupérés depuis Batigest")

        for row in batigest_devis:
            Code, Date, Nom, Adr, CP, Ville, Sujet, DateConcretis, TempsMO = row
            # Utilisation de ON CONFLICT pour éviter les doublons
            postgres_cursor.execute(
                """
                INSERT INTO batigest_devis 
                (code, date, nom, Adr, CP, ville, sujet, dateconcretis, tempsmo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (code) DO UPDATE SET 
                date = EXCLUDED.date,
                dateconcretis = EXCLUDED.dateconcretis,
                nom = EXCLUDED.nom,
                adr = EXCLUDED.adr,
                cp = EXCLUDED.cp,
                ville = EXCLUDED.ville,
                sujet = EXCLUDED.sujet,
                tempsmo = EXCLUDED.tempsmo,
                sync = False
                """,
                (Code, Date, Nom, Adr, CP, Ville, Sujet, DateConcretis, TempsMO)
            )

        # Validation des modifications dans PostgreSQL
        postgres_conn.commit()

        # Fermeture propre des connexions
        sqlserver_cursor.close()
        postgres_cursor.close()
        sqlserver_conn.close()
        postgres_conn.close()

        return True, "✅ Transfert terminé avec succès"

    except Exception as e:
        # En cas d'erreur, on retourne le message d'erreur
        return False, f"❌ Erreur lors du transfert : {e}"



def transfer_devis_vers_batisimply():
    """
    Transfère les devis depuis PostgreSQL vers BatiSimply.
    
    Cette fonction :
    1. Récupère le token d'authentification
    2. Vérifie les identifiants PostgreSQL
    3. Récupère les devis non synchronisés
    4. Les envoie à l'API BatiSimply (POST pour nouveaux, PUT pour existants)
    5. Met à jour le statut de synchronisation
    
    Returns:
        bool: True si au moins un chantier a été transféré avec succès, False sinon
    """
    # Récupération du token
    token = recup_batisimply_token()
    if not token:
        print("Impossible de continuer sans token.")
        return False

    # Vérification des identifiants PostgreSQL
    creds = load_credentials()
    if not creds or "postgres" not in creds:
        print("❌ Informations Postgres manquantes.")
        return False

    # Connexion à PostgreSQL
    pg = creds["postgres"]
    postgres_conn = connect_to_postgres(
        pg["host"], pg["user"], pg["password"], pg["database"], pg.get("port", "5432")
    )

    if not postgres_conn:
        print("❌ Connexion à la base Postgres échouée.")
        return False

    # Configuration de l'API BatiSimply
    API_URL = "https://api.staging.batisimply.fr/api/project"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Récupération des chantiers non synchronisés
    postgres_cursor = postgres_conn.cursor()
    postgres_cursor.execute("""
        select code, date, nom, adr, cp, ville, sujet, dateconcretis, tempsmo 
        from batigest_devis
        where sync = false
    """)

    rows = postgres_cursor.fetchall()
    success = False

    # Récupération des chantiers existants dans BatiSimply
    existing_projects = {}
    response = requests.get(API_URL, headers=headers)
    if response.status_code == 200:
        projects = response.json().get("elements", [])
        for project in projects:
            existing_projects[project.get('projectCode')] = project.get('id')

    # Traitement de chaque chantier
    for row in rows:
        code, date, nom, adr, cp, ville, sujet, dateconcretis, tempsmo  = row

        # Préparation des données pour l'API
        data = {
            "address": {
                "city": ville,
                "countryCode": "FR",
                "geoPoint": {
                    "xLon": 3.8777,
                    "yLat": 43.6119
                },
                "googleFormattedAddress": f"{adr}, {cp} {ville}, France",
                "postalCode": cp,
                "street": adr
            },
            "budget": {
                "amount": 500000.0,
                "currency": "EUR"
            },
            "endEstimated": dateconcretis.strftime("%Y-%m-%d") if dateconcretis else None,
            "headQuarter": {
                "id": 33
            },
            "hoursSold": tempsmo if tempsmo is not None else 0,
            "projectCode": code,
            "comment": sujet,
            "projectName": nom,
            "customerName": nom,
            "projectManager": "DEFINIR",
            "startEstimated": date.strftime("%Y-%m-%d") if date else None,
            "isArchived": False,
            "isFinished": False,
            "projectColor": "#9b1ff1"
        }

        # Détermination de la méthode HTTP
        if code in existing_projects:
            project_id = existing_projects[code]
            method = "PUT"
            url = API_URL
            # Inclure l'id dans le payload pour la mise à jour
            data["id"] = project_id
            print(f"🔄 Mise à jour du projet existant '{code}' (ID: {data['id']})")
        else:
            method = "POST"
            url = API_URL
            print(f"➕ Création du nouveau projet '{code}'")

        # Envoi à l'API et mise à jour du statut
        response = requests.request(method, url, headers=headers, data=json.dumps(data))
        if response.status_code in [200, 201]:
            print(f"✅ Projet '{code}' traité avec succès")
            postgres_cursor.execute(
                "UPDATE batigest_devis SET sync = true, sync_date = NOW() WHERE code = %s", (code,))
            postgres_conn.commit()
            success = True
        else:
            print(f"❌ Erreur pour le projet '{code}' : {response.status_code} → {response.text}")

    # Nettoyage
    postgres_cursor.close()
    postgres_conn.close()

    return success
