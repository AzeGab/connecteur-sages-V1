-- Création de la base de données
SELECT 'CREATE DATABASE connecteur_buffer'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'connecteur_buffer')\gexec

-- Connexion à la nouvelle base
\c connecteur_buffer

-- Création des tables
BEGIN;

CREATE TABLE IF NOT EXISTS public.batigest_devis
(
    code character varying(50) NOT NULL,
    date date,
    nom character varying(100),
    adr text,
    cp character varying(10),
    ville character varying(100),
    sujet text,
    dateconcretis date,
    tempsmo real,
    sync_date timestamp without time zone,
    sync boolean DEFAULT false,
    CONSTRAINT batigest_devis_pkey PRIMARY KEY (code)
TABLESPACE pg_default;

CREATE TABLE IF NOT EXISTS public.batigest_chantiers
(
    id integer NOT NULL DEFAULT nextval('batigest_chantiers_id_seq'::regclass),
    code character varying(50),
    date_debut date,
    date_fin date,
    nom_client character varying(100),
    description character varying(200),
    adr_chantier text,
    cp_chantier character varying(10),
    ville_chantier character varying(45),
    sync_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    sync boolean DEFAULT false,
    total_mo real,
    last_modified_batisimply timestamp with time zone,
    last_modified_batigest timestamp with time zone,
    CONSTRAINT batigest_chantiers_pkey PRIMARY KEY (id),
    CONSTRAINT batigest_chantiers_code_key UNIQUE (code)
TABLESPACE pg_default;

CREATE SEQUENCE IF NOT EXISTS public.batigest_heures_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS public.batigest_heures
(
    id integer NOT NULL DEFAULT nextval('batigest_heures_id_seq'::regclass),
    id_heure character varying(50) NOT NULL,
    date_debut timestamp without time zone NOT NULL,
    date_fin timestamp without time zone NOT NULL,
    id_utilisateur uuid NOT NULL,
    id_projet integer,
    status_management character varying(50),
    total_heure numeric(5,2),
    panier boolean DEFAULT false,
    trajet boolean DEFAULT false,
    code_projet character varying(100),
    sync boolean,
    CONSTRAINT batigest_heures_pkey PRIMARY KEY (id),
    CONSTRAINT unique_id_heure UNIQUE (id_heure)
TABLESPACE pg_default;

-- Création d'un utilisateur dédié
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'connecteur_user') THEN
        CREATE ROLE connecteur_user LOGIN PASSWORD 'connecteur_password';
        GRANT ALL PRIVILEGES ON DATABASE connecteur_buffer TO connecteur_user;
        GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO connecteur_user;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO connecteur_user;
    END IF;
END $$;

COMMIT;