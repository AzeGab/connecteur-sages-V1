#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Génère un PDF de documentation pour le projet Connecteur SAGES.
Sortie: docs/Documentation_Connecteur_SAGES.pdf
"""

import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
    Image,
    ListFlowable,
    ListItem,
)


def _header_footer(canvas, doc):
    canvas.saveState()
    width, height = A4
    # Bande en haut
    canvas.setFillColorRGB(0.11, 0.22, 0.45)
    canvas.rect(0, height - 15, width, 15, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(1.2 * cm, height - 11, "Connecteur SAGES – Documentation")

    # Pied de page avec pagination
    canvas.setFillColor(colors.grey)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(width - 1.2 * cm, 1 * cm, f"Page {doc.page}")
    canvas.restoreState()


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TitleBig",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=28,
            leading=32,
            textColor=colors.HexColor("#173b73"),
            spaceAfter=16,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H1",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            textColor=colors.HexColor("#173b73"),
            spaceBefore=14,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            textColor=colors.HexColor("#2c5282"),
            spaceBefore=10,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Body",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=14,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Mono",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            textColor=colors.HexColor("#1a202c"),
        )
    )
    return styles


def bullet_list(items, styles):
    return ListFlowable(
        [ListItem(Paragraph(i, styles["Body"])) for i in items],
        bulletType="bullet",
        start="circle",
        leftIndent=12,
        bulletFontName="Helvetica",
        bulletFontSize=8,
        bulletColor=colors.HexColor("#173b73"),
        spaceBefore=2,
        spaceAfter=6,
    )


def add_file_section(story, styles, title, path, description, key_points=None):
    story.append(Paragraph(title, styles["H2"]))
    meta = [
        ["Fichier", f"{path}"],
        ["Rôle", description],
    ]
    table = Table(meta, colWidths=[2.6 * cm, 14 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f7fafc")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#2d3748")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e0")),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(table)
    if key_points:
        story.append(Spacer(1, 0.2 * cm))
        story.append(bullet_list(key_points, styles))
    story.append(Spacer(1, 0.3 * cm))


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(base_dir, "docs")
    os.makedirs(out_dir, exist_ok=True)
    out_pdf = os.path.join(out_dir, "Documentation_Connecteur_SAGES.pdf")

    styles = build_styles()
    story = []

    # Page de titre
    story.append(Spacer(1, 1.2 * cm))
    story.append(Paragraph("Documentation Technique", styles["TitleBig"]))
    story.append(Paragraph("Connecteur SAGES – Batigest ↔ Batisimply", styles["H1"]))
    story.append(Spacer(1, 0.4 * cm))

    # Bandeau d'infos
    info = [
        ["Version", "1.0.0"],
        ["Date", datetime.now().strftime("%d/%m/%Y")],
        ["Framework", "FastAPI (Uvicorn)"],
        ["Base(s)", "SQL Server, PostgreSQL, API BatiSimply"],
        ["Licence", "Validation Supabase / Service centralisé (optionnel)"],
    ]
    t = Table(info, colWidths=[3 * cm, 13.6 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#edf2f7")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#cbd5e0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 0.6 * cm))

    # Vue d'ensemble
    story.append(Paragraph("Vue d’ensemble", styles["H1"]))
    story.append(
        Paragraph(
            "Application FastAPI permettant la synchronisation des données entre Batigest (SQL Server) et BatiSimply via PostgreSQL. "
            "Elle inclut un système de gestion et de validation de licences, une interface web (templates Jinja2) et des services de transfert/synchronisation.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 0.2 * cm))
    story.append(
        bullet_list(
            [
                "API web: FastAPI + Uvicorn, sessions et middleware de licence.",
                "Données: SQL Server (Batigest), PostgreSQL (tampon), API BatiSimply.",
                "Templates HTML Jinja2 et assets statiques.",
                "Installateur Windows et scripts de test/connectivité.",
            ],
            styles,
        )
    )

    story.append(PageBreak())

    # Fichiers principaux
    story.append(Paragraph("Fichiers principaux", styles["H1"]))

    add_file_section(
        story,
        styles,
        "Point d’entrée – Application FastAPI",
        "app/main.py",
        "Crée l’application, monte /static, configure Jinja2, ajoute les middlewares de session et de licence, expose /health, inclut les routes du formulaire.",
        key_points=[
            "SessionMiddleware (cookie 'connecteur_session').",
            "LicenseMiddleware: vérification/rafraîchissement de licence.",
            "Include router: app.routes.form_routes.",
            "Exécution locale via uvicorn et ouverture navigateur.",
        ],
    )

    add_file_section(
        story,
        styles,
        "Routes – Formulaires et actions",
        "app/routes/form_routes.py",
        "Routes UI et actions: connexions SQL Server/PostgreSQL, transferts, synchronisations, configuration (mode/logiciel), et gestion des licences.",
        key_points=[
            "POST /connect-sqlserver, /connect-postgres: test + sauvegarde credentials.",
            "POST /transfer: Batigest → PostgreSQL (chantiers).",
            "POST /transfer-batisimply: PostgreSQL → BatiSimply (chantiers).",
            "POST /recup-heures /transfer-heure-batigest: heures BatiSimply ↔ Batigest.",
            "POST /sync-batigest-to-batisimply /sync-batisimply-to-batigest.",
            "GET /configuration, /login, /license-expired.",
            "Gestion de la licence: /update-license, /refresh-license, /check-license-status, /get-license-key.",
        ],
    )

    add_file_section(
        story,
        styles,
        "Middleware – Licence",
        "app/middleware/license_middleware.py",
        "Interceptre les requêtes des routes protégées. Vérifie la validité locale, tente un rafraîchissement, redirige vers configuration ou affiche license_expired.",
        key_points=[
            "Routes protégées: '/', transfert, sync, etc.",
            "Routes exclues: /login, /configuration, /static, /license-expired, /update-license, /refresh-license.",
        ],
    )

    add_file_section(
        story,
        styles,
        "Services – Connexions & Auth",
        "app/services/connex.py",
        "Connexions SQL Server (pyodbc), PostgreSQL (psycopg2), HFSQL (pypyodbc). Gestion des credentials JSON et récupération du token BatiSimply (SSO Keycloak).",
        key_points=[
            "CREDENTIALS_FILE: app/services/credentials.json.",
            "recup_batisimply_token(): Keycloak password grant.",
            "check_connection_status(), connexion() (retourne Postgres & SQL Server).",
        ],
    )

    add_file_section(
        story,
        styles,
        "Services – Chantiers",
        "app/services/chantier.py",
        "Transferts Batigest → PostgreSQL (agrégats Devis.TempsMO), envoi vers BatiSimply (création/mise à jour), correspondances de codes projet, initialisation colonne 'sync'.",
        key_points=[
            "transfer_chantiers(): INSERT ... ON CONFLICT dans batigest_chantiers.",
            "transfer_chantiers_vers_batisimply(): POST/PUT /api/project, maj sync.",
            "recup_chantiers_batisimply(), recup_chantiers_postgres().",
            "recup_code_projet_chantiers(): map code ↔ id_projet.",
            "update_code_projet_chantiers(): met à jour batigest_heures.code_projet.",
            "sync_batigest_to_batisimply() / sync_batisimply_to_batigest().",
            "init_postgres_table(): ajoute colonne sync si nécessaire.",
        ],
    )

    add_file_section(
        story,
        styles,
        "Services – Heures",
        "app/services/heures.py",
        "Récupération des créneaux (allUsers) depuis BatiSimply → PostgreSQL; envoi des heures validées vers Batigest (SuiviMO) avec mapping Salarie.codebs; flag sync.",
        key_points=[
            "transfer_heures_to_postgres(): insert dans batigest_heures (ON CONFLICT DO NOTHING).",
            "transfer_heures_to_sqlserver(): sélection VALIDATED & NOT sync, insertion SuiviMO.",
        ],
    )

    add_file_section(
        story,
        styles,
        "Services – Devis",
        "app/services/devis.py",
        "Transfert des devis Batigest → PostgreSQL et synchronisation vers BatiSimply (création/mise à jour projets).",
        key_points=[
            "transfer_devis(): INSERT ... ON CONFLICT dans batigest_devis.",
            "transfer_devis_vers_batisimply(): POST/PUT /api/project, maj sync.",
        ],
    )

    add_file_section(
        story,
        styles,
        "Services – Licence",
        "app/services/license.py",
        "Validation via service central (optionnel) puis fallback Supabase. Sauvegarde locale normalisée (credentials.json), fonctions utilitaires (is_valid, expiry, heartbeat).",
        key_points=[
            "validate_license_key(): service central → Supabase (fallback).",
            "save/load_license_info(), is_license_valid(), get_license_expiry_date().",
            "refresh_license_validation(): met à jour localement.",
        ],
    )

    add_file_section(
        story,
        styles,
        "Utils – Chemins PyInstaller",
        "app/utils/paths.py",
        "Résout les chemins 'templates' et 'static' en mode normal ou binaire PyInstaller (sys._MEIPASS).",
        key_points=[
            "templates_path, static_path selon exécution (frozen vs dev).",
        ],
    )

    add_file_section(
        story,
        styles,
        "Utils – Templates Jinja2",
        "app/utils/templates_engine.py",
        "Initialisation simple du moteur Jinja2 et getter pour injection de dépendance.",
        key_points=[
            "get_templates(): retourne l’instance Jinja2Templates.",
        ],
    )

    add_file_section(
        story,
        styles,
        "Templates & Statics",
        "app/templates/*, app/static/app.js",
        "Pages HTML (index, configuration, login, license_expired) + JS d’animation/feedback de synchronisation.",
        key_points=[
            "UI: formulaire connexions, boutons d’actions, vérification automatique licence.",
        ],
    )

    add_file_section(
        story,
        styles,
        "Installateur Windows",
        "installer.py",
        "Installe PostgreSQL (unattended), configure Python embarqué, initialise la base (initdb.sql), installe requirements, déploie l’app et crée un raccourci.",
        key_points=[
            "install_postgres(), setup_python(), init_database(), install_requirements().",
            "create_start_script(), create_shortcut().",
        ],
    )

    add_file_section(
        story,
        styles,
        "Dépendances",
        "requirements.txt & app/requirements.txt",
        "Dépendances principales pour l’application (FastAPI, Uvicorn, Jinja2, Requests, drivers SQL).",
        key_points=[
            "PyODBC, psycopg2, pypyodbc; supabase; python-dotenv; etc.",
        ],
    )

    add_file_section(
        story,
        styles,
        "Tests & Outils",
        "test_app.py, test_supabase_connection.py, docs/*",
        "Scripts de vérification (connectivité app, accès Supabase) et documents d’installation/migration.",
        key_points=[
            "test_supabase_connection.py: ping REST Supabase + table licenses.",
        ],
    )

    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Fin du document.", styles["Body"]))

    doc = SimpleDocTemplate(
        out_pdf,
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=2.2 * cm,
        bottomMargin=1.6 * cm,
        title="Documentation Connecteur SAGES",
        author="Groupe SAGES",
    )
    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    print(f"✅ PDF généré: {out_pdf}")


if __name__ == "__main__":
    main()


