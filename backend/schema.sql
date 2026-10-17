--
-- PostgreSQL database dump
--

\restrict En3zLESXyoK4ZYZozBdxVfIgHs0heLlBC7A0gAdFKlVYv7ugzud16J9vYcCKHSx

-- Dumped from database version 16.15
-- Dumped by pg_dump version 16.15

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: alertes_securite; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alertes_securite (
    id_alerte integer NOT NULL,
    id_score bigint NOT NULL,
    id_politique integer NOT NULL,
    niveau_gravite character varying(20) NOT NULL,
    statut character varying(20) NOT NULL,
    date_creation timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.alertes_securite OWNER TO postgres;

--
-- Name: alertes_securite_id_alerte_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.alertes_securite_id_alerte_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.alertes_securite_id_alerte_seq OWNER TO postgres;

--
-- Name: alertes_securite_id_alerte_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.alertes_securite_id_alerte_seq OWNED BY public.alertes_securite.id_alerte;


--
-- Name: axes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.axes (
    id integer NOT NULL,
    mission_id integer NOT NULL,
    numero_axe integer,
    itineraire_principal character varying
);


ALTER TABLE public.axes OWNER TO postgres;

--
-- Name: axes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.axes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.axes_id_seq OWNER TO postgres;

--
-- Name: axes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.axes_id_seq OWNED BY public.axes.id;


--
-- Name: benchmarking_services; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.benchmarking_services (
    id_benchmark integer NOT NULL,
    id_service integer NOT NULL,
    periode character varying(20) NOT NULL,
    score_risque_moyen double precision NOT NULL,
    rang integer,
    date_calcul timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.benchmarking_services OWNER TO postgres;

--
-- Name: benchmarking_services_id_benchmark_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.benchmarking_services_id_benchmark_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.benchmarking_services_id_benchmark_seq OWNER TO postgres;

--
-- Name: benchmarking_services_id_benchmark_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.benchmarking_services_id_benchmark_seq OWNED BY public.benchmarking_services.id_benchmark;


--
-- Name: districts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.districts (
    id integer NOT NULL,
    nom character varying NOT NULL,
    region character varying,
    province character varying,
    electrifie boolean
);


ALTER TABLE public.districts OWNER TO postgres;

--
-- Name: districts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.districts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.districts_id_seq OWNER TO postgres;

--
-- Name: districts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.districts_id_seq OWNED BY public.districts.id;


--
-- Name: equipes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.equipes (
    id integer NOT NULL,
    axe_id integer NOT NULL,
    type_equipe character varying
);


ALTER TABLE public.equipes OWNER TO postgres;

--
-- Name: equipes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.equipes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.equipes_id_seq OWNER TO postgres;

--
-- Name: equipes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.equipes_id_seq OWNED BY public.equipes.id;


--
-- Name: indicateurs_performance; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.indicateurs_performance (
    id integer NOT NULL,
    mission_id integer NOT NULL,
    resultat_attendu character varying,
    indicateur_mesure character varying,
    cible character varying,
    valeur_realisee character varying
);


ALTER TABLE public.indicateurs_performance OWNER TO postgres;

--
-- Name: indicateurs_performance_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.indicateurs_performance_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.indicateurs_performance_id_seq OWNER TO postgres;

--
-- Name: indicateurs_performance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.indicateurs_performance_id_seq OWNED BY public.indicateurs_performance.id;


--
-- Name: investigations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.investigations (
    id_investigation integer NOT NULL,
    id_alerte integer NOT NULL,
    id_enqueteur integer NOT NULL,
    statut character varying(20) NOT NULL,
    conclusion character varying(500),
    date_ouverture timestamp with time zone DEFAULT now() NOT NULL,
    date_cloture timestamp with time zone
);


ALTER TABLE public.investigations OWNER TO postgres;

--
-- Name: investigations_id_investigation_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.investigations_id_investigation_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.investigations_id_investigation_seq OWNER TO postgres;

--
-- Name: investigations_id_investigation_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.investigations_id_investigation_seq OWNED BY public.investigations.id_investigation;


--
-- Name: journal_acces; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.journal_acces (
    id_entree bigint NOT NULL,
    id_utilisateur integer NOT NULL,
    id_ressource integer NOT NULL,
    type_action character varying(30) NOT NULL,
    horodatage timestamp with time zone DEFAULT now() NOT NULL,
    adresse_ip character varying(45) NOT NULL,
    hash_entree character varying(64) NOT NULL,
    hash_precedent character varying(64) NOT NULL
);


ALTER TABLE public.journal_acces OWNER TO postgres;

--
-- Name: journal_acces_id_entree_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.journal_acces_id_entree_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.journal_acces_id_entree_seq OWNER TO postgres;

--
-- Name: journal_acces_id_entree_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.journal_acces_id_entree_seq OWNED BY public.journal_acces.id_entree;


--
-- Name: journees; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.journees (
    id integer NOT NULL,
    mission_district_id integer NOT NULL,
    numero_jour integer,
    date date,
    lieu character varying,
    statut character varying,
    activites_prevues text,
    activites_realisees text,
    ecart text
);


ALTER TABLE public.journees OWNER TO postgres;

--
-- Name: journees_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.journees_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.journees_id_seq OWNER TO postgres;

--
-- Name: journees_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.journees_id_seq OWNED BY public.journees.id;


--
-- Name: livrables; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.livrables (
    id integer NOT NULL,
    phase_id integer NOT NULL,
    type_livrable character varying,
    date_production timestamp without time zone,
    signe boolean,
    fichier character varying
);


ALTER TABLE public.livrables OWNER TO postgres;

--
-- Name: livrables_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.livrables_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.livrables_id_seq OWNER TO postgres;

--
-- Name: livrables_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.livrables_id_seq OWNED BY public.livrables.id;


--
-- Name: missions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.missions (
    id integer NOT NULL,
    titre character varying NOT NULL,
    type_mission character varying,
    date_debut timestamp without time zone,
    date_fin_prevue timestamp without time zone,
    statut character varying
);


ALTER TABLE public.missions OWNER TO postgres;

--
-- Name: missions_districts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.missions_districts (
    id integer NOT NULL,
    axe_id integer NOT NULL,
    district_id integer NOT NULL,
    ordre_visite integer,
    statut character varying
);


ALTER TABLE public.missions_districts OWNER TO postgres;

--
-- Name: missions_districts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.missions_districts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.missions_districts_id_seq OWNER TO postgres;

--
-- Name: missions_districts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.missions_districts_id_seq OWNED BY public.missions_districts.id;


--
-- Name: missions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.missions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.missions_id_seq OWNER TO postgres;

--
-- Name: missions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.missions_id_seq OWNED BY public.missions.id;


--
-- Name: notifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notifications (
    id integer NOT NULL,
    id_utilisateur integer NOT NULL,
    type_notification character varying(40) NOT NULL,
    message character varying(500) NOT NULL,
    lien character varying(255),
    lue boolean NOT NULL,
    date_creation timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.notifications OWNER TO postgres;

--
-- Name: notifications_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.notifications_id_seq OWNER TO postgres;

--
-- Name: notifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.notifications_id_seq OWNED BY public.notifications.id;


--
-- Name: participants; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.participants (
    id integer NOT NULL,
    equipe_id integer NOT NULL,
    nom character varying NOT NULL,
    fonction character varying,
    id_utilisateur integer
);


ALTER TABLE public.participants OWNER TO postgres;

--
-- Name: participants_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.participants_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.participants_id_seq OWNER TO postgres;

--
-- Name: participants_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.participants_id_seq OWNED BY public.participants.id;


--
-- Name: phases; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.phases (
    id integer NOT NULL,
    mission_district_id integer NOT NULL,
    type_activite_id integer NOT NULL,
    numero_ordre integer,
    duree_prevue character varying,
    livrable_attendu character varying,
    statut character varying
);


ALTER TABLE public.phases OWNER TO postgres;

--
-- Name: phases_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.phases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.phases_id_seq OWNER TO postgres;

--
-- Name: phases_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.phases_id_seq OWNED BY public.phases.id;


--
-- Name: pieces_jointes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pieces_jointes (
    id integer NOT NULL,
    id_rapport integer NOT NULL,
    id_mission_district integer,
    type_piece character varying(30) NOT NULL,
    nom_original character varying(255) NOT NULL,
    chemin_stockage character varying(500) NOT NULL,
    type_mime character varying(100) NOT NULL,
    taille integer NOT NULL,
    empreinte_sha256 character varying(64) NOT NULL,
    legende character varying(255),
    id_televerseur integer NOT NULL,
    date_depot timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.pieces_jointes OWNER TO postgres;

--
-- Name: pieces_jointes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.pieces_jointes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pieces_jointes_id_seq OWNER TO postgres;

--
-- Name: pieces_jointes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.pieces_jointes_id_seq OWNED BY public.pieces_jointes.id;


--
-- Name: politiques_conformite; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.politiques_conformite (
    id_politique integer NOT NULL,
    nom_politique character varying(100) NOT NULL,
    description character varying(255) NOT NULL,
    seuils_configures character varying(255) NOT NULL,
    date_effective timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.politiques_conformite OWNER TO postgres;

--
-- Name: politiques_conformite_id_politique_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.politiques_conformite_id_politique_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.politiques_conformite_id_politique_seq OWNER TO postgres;

--
-- Name: politiques_conformite_id_politique_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.politiques_conformite_id_politique_seq OWNED BY public.politiques_conformite.id_politique;


--
-- Name: profils_comportementaux; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.profils_comportementaux (
    id_profil integer NOT NULL,
    id_utilisateur integer NOT NULL,
    periode_reference character varying(20) NOT NULL,
    volume_moyen double precision NOT NULL,
    horaires_habituels character varying(50) NOT NULL,
    perimetre_habituel character varying(255) NOT NULL,
    date_calcul timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.profils_comportementaux OWNER TO postgres;

--
-- Name: profils_comportementaux_id_profil_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.profils_comportementaux_id_profil_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.profils_comportementaux_id_profil_seq OWNER TO postgres;

--
-- Name: profils_comportementaux_id_profil_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.profils_comportementaux_id_profil_seq OWNED BY public.profils_comportementaux.id_profil;


--
-- Name: rapport_difficultes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.rapport_difficultes (
    id integer NOT NULL,
    id_rapport integer NOT NULL,
    categorie character varying(100) NOT NULL,
    description text NOT NULL,
    solution text
);


ALTER TABLE public.rapport_difficultes OWNER TO postgres;

--
-- Name: rapport_difficultes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.rapport_difficultes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.rapport_difficultes_id_seq OWNER TO postgres;

--
-- Name: rapport_difficultes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.rapport_difficultes_id_seq OWNED BY public.rapport_difficultes.id;


--
-- Name: rapports_audit; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.rapports_audit (
    id_rapport integer NOT NULL,
    id_service integer,
    periode_couverte character varying(20) NOT NULL,
    contenu text NOT NULL,
    date_generation timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.rapports_audit OWNER TO postgres;

--
-- Name: rapports_audit_id_rapport_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.rapports_audit_id_rapport_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.rapports_audit_id_rapport_seq OWNER TO postgres;

--
-- Name: rapports_audit_id_rapport_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.rapports_audit_id_rapport_seq OWNED BY public.rapports_audit.id_rapport;


--
-- Name: rapports_mission; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.rapports_mission (
    id integer NOT NULL,
    axe_id integer NOT NULL,
    id_auteur integer NOT NULL,
    statut character varying(20) NOT NULL,
    contexte text,
    justification text,
    itineraire_reel text,
    inventaire_materiel text,
    configuration_technique text,
    tests_securite text,
    nb_participants_formes integer,
    profil_participants character varying(255),
    themes_formation text,
    evaluation_formation text,
    points_forts text,
    lecons_apprises text,
    bonnes_pratiques text,
    conclusion text,
    recommandations text,
    date_creation timestamp with time zone DEFAULT now() NOT NULL,
    date_modification timestamp with time zone DEFAULT now() NOT NULL,
    date_soumission timestamp with time zone,
    id_validateur integer,
    date_validation timestamp with time zone,
    commentaire_validation text
);


ALTER TABLE public.rapports_mission OWNER TO postgres;

--
-- Name: rapports_mission_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.rapports_mission_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.rapports_mission_id_seq OWNER TO postgres;

--
-- Name: rapports_mission_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.rapports_mission_id_seq OWNED BY public.rapports_mission.id;


--
-- Name: ressources_sensibles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ressources_sensibles (
    id_ressource integer NOT NULL,
    type_ressource character varying(100) NOT NULL,
    niveau_sensibilite character varying(20) NOT NULL,
    id_service_proprietaire integer NOT NULL
);


ALTER TABLE public.ressources_sensibles OWNER TO postgres;

--
-- Name: ressources_sensibles_id_ressource_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ressources_sensibles_id_ressource_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ressources_sensibles_id_ressource_seq OWNER TO postgres;

--
-- Name: ressources_sensibles_id_ressource_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ressources_sensibles_id_ressource_seq OWNED BY public.ressources_sensibles.id_ressource;


--
-- Name: roles_permissions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.roles_permissions (
    id_role integer NOT NULL,
    nom_role character varying(50) NOT NULL,
    niveau_acces character varying(20) NOT NULL
);


ALTER TABLE public.roles_permissions OWNER TO postgres;

--
-- Name: roles_permissions_id_role_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.roles_permissions_id_role_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.roles_permissions_id_role_seq OWNER TO postgres;

--
-- Name: roles_permissions_id_role_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.roles_permissions_id_role_seq OWNED BY public.roles_permissions.id_role;


--
-- Name: scores_anomalie; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.scores_anomalie (
    id_score bigint NOT NULL,
    id_entree_journal bigint NOT NULL,
    id_profil_reference integer NOT NULL,
    z_score double precision NOT NULL,
    methode_utilisee character varying(50) NOT NULL,
    date_calcul timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.scores_anomalie OWNER TO postgres;

--
-- Name: scores_anomalie_id_score_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.scores_anomalie_id_score_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.scores_anomalie_id_score_seq OWNER TO postgres;

--
-- Name: scores_anomalie_id_score_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.scores_anomalie_id_score_seq OWNED BY public.scores_anomalie.id_score;


--
-- Name: services_communes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.services_communes (
    id_service integer NOT NULL,
    nom_service character varying(100) NOT NULL,
    type character varying(30) NOT NULL,
    id_service_parent integer
);


ALTER TABLE public.services_communes OWNER TO postgres;

--
-- Name: services_communes_id_service_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.services_communes_id_service_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.services_communes_id_service_seq OWNER TO postgres;

--
-- Name: services_communes_id_service_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.services_communes_id_service_seq OWNED BY public.services_communes.id_service;


--
-- Name: types_activite; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.types_activite (
    id integer NOT NULL,
    libelle character varying NOT NULL
);


ALTER TABLE public.types_activite OWNER TO postgres;

--
-- Name: types_activite_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.types_activite_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.types_activite_id_seq OWNER TO postgres;

--
-- Name: types_activite_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.types_activite_id_seq OWNED BY public.types_activite.id;


--
-- Name: utilisateurs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.utilisateurs (
    id_utilisateur integer NOT NULL,
    nom character varying(100) NOT NULL,
    prenom character varying(100) NOT NULL,
    email character varying(150) NOT NULL,
    matricule character varying(30) NOT NULL,
    mot_de_passe_hash character varying(255) NOT NULL,
    id_service integer NOT NULL,
    id_role integer NOT NULL,
    statut character varying(20) NOT NULL,
    date_creation timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.utilisateurs OWNER TO postgres;

--
-- Name: utilisateurs_id_utilisateur_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.utilisateurs_id_utilisateur_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.utilisateurs_id_utilisateur_seq OWNER TO postgres;

--
-- Name: utilisateurs_id_utilisateur_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.utilisateurs_id_utilisateur_seq OWNED BY public.utilisateurs.id_utilisateur;


--
-- Name: alertes_securite id_alerte; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alertes_securite ALTER COLUMN id_alerte SET DEFAULT nextval('public.alertes_securite_id_alerte_seq'::regclass);


--
-- Name: axes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.axes ALTER COLUMN id SET DEFAULT nextval('public.axes_id_seq'::regclass);


--
-- Name: benchmarking_services id_benchmark; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.benchmarking_services ALTER COLUMN id_benchmark SET DEFAULT nextval('public.benchmarking_services_id_benchmark_seq'::regclass);


--
-- Name: districts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.districts ALTER COLUMN id SET DEFAULT nextval('public.districts_id_seq'::regclass);


--
-- Name: equipes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipes ALTER COLUMN id SET DEFAULT nextval('public.equipes_id_seq'::regclass);


--
-- Name: indicateurs_performance id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.indicateurs_performance ALTER COLUMN id SET DEFAULT nextval('public.indicateurs_performance_id_seq'::regclass);


--
-- Name: investigations id_investigation; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.investigations ALTER COLUMN id_investigation SET DEFAULT nextval('public.investigations_id_investigation_seq'::regclass);


--
-- Name: journal_acces id_entree; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journal_acces ALTER COLUMN id_entree SET DEFAULT nextval('public.journal_acces_id_entree_seq'::regclass);


--
-- Name: journees id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journees ALTER COLUMN id SET DEFAULT nextval('public.journees_id_seq'::regclass);


--
-- Name: livrables id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.livrables ALTER COLUMN id SET DEFAULT nextval('public.livrables_id_seq'::regclass);


--
-- Name: missions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.missions ALTER COLUMN id SET DEFAULT nextval('public.missions_id_seq'::regclass);


--
-- Name: missions_districts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.missions_districts ALTER COLUMN id SET DEFAULT nextval('public.missions_districts_id_seq'::regclass);


--
-- Name: notifications id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications ALTER COLUMN id SET DEFAULT nextval('public.notifications_id_seq'::regclass);


--
-- Name: participants id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.participants ALTER COLUMN id SET DEFAULT nextval('public.participants_id_seq'::regclass);


--
-- Name: phases id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.phases ALTER COLUMN id SET DEFAULT nextval('public.phases_id_seq'::regclass);


--
-- Name: pieces_jointes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pieces_jointes ALTER COLUMN id SET DEFAULT nextval('public.pieces_jointes_id_seq'::regclass);


--
-- Name: politiques_conformite id_politique; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.politiques_conformite ALTER COLUMN id_politique SET DEFAULT nextval('public.politiques_conformite_id_politique_seq'::regclass);


--
-- Name: profils_comportementaux id_profil; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.profils_comportementaux ALTER COLUMN id_profil SET DEFAULT nextval('public.profils_comportementaux_id_profil_seq'::regclass);


--
-- Name: rapport_difficultes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rapport_difficultes ALTER COLUMN id SET DEFAULT nextval('public.rapport_difficultes_id_seq'::regclass);


--
-- Name: rapports_audit id_rapport; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rapports_audit ALTER COLUMN id_rapport SET DEFAULT nextval('public.rapports_audit_id_rapport_seq'::regclass);


--
-- Name: rapports_mission id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rapports_mission ALTER COLUMN id SET DEFAULT nextval('public.rapports_mission_id_seq'::regclass);


--
-- Name: ressources_sensibles id_ressource; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ressources_sensibles ALTER COLUMN id_ressource SET DEFAULT nextval('public.ressources_sensibles_id_ressource_seq'::regclass);


--
-- Name: roles_permissions id_role; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles_permissions ALTER COLUMN id_role SET DEFAULT nextval('public.roles_permissions_id_role_seq'::regclass);


--
-- Name: scores_anomalie id_score; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scores_anomalie ALTER COLUMN id_score SET DEFAULT nextval('public.scores_anomalie_id_score_seq'::regclass);


--
-- Name: services_communes id_service; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.services_communes ALTER COLUMN id_service SET DEFAULT nextval('public.services_communes_id_service_seq'::regclass);


--
-- Name: types_activite id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.types_activite ALTER COLUMN id SET DEFAULT nextval('public.types_activite_id_seq'::regclass);


--
-- Name: utilisateurs id_utilisateur; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.utilisateurs ALTER COLUMN id_utilisateur SET DEFAULT nextval('public.utilisateurs_id_utilisateur_seq'::regclass);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: alertes_securite alertes_securite_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alertes_securite
    ADD CONSTRAINT alertes_securite_pkey PRIMARY KEY (id_alerte);


--
-- Name: axes axes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.axes
    ADD CONSTRAINT axes_pkey PRIMARY KEY (id);


--
-- Name: benchmarking_services benchmarking_services_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.benchmarking_services
    ADD CONSTRAINT benchmarking_services_pkey PRIMARY KEY (id_benchmark);


--
-- Name: districts districts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.districts
    ADD CONSTRAINT districts_pkey PRIMARY KEY (id);


--
-- Name: equipes equipes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipes
    ADD CONSTRAINT equipes_pkey PRIMARY KEY (id);


--
-- Name: indicateurs_performance indicateurs_performance_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.indicateurs_performance
    ADD CONSTRAINT indicateurs_performance_pkey PRIMARY KEY (id);


--
-- Name: investigations investigations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.investigations
    ADD CONSTRAINT investigations_pkey PRIMARY KEY (id_investigation);


--
-- Name: journal_acces journal_acces_hash_entree_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journal_acces
    ADD CONSTRAINT journal_acces_hash_entree_key UNIQUE (hash_entree);


--
-- Name: journal_acces journal_acces_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journal_acces
    ADD CONSTRAINT journal_acces_pkey PRIMARY KEY (id_entree);


--
-- Name: journees journees_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journees
    ADD CONSTRAINT journees_pkey PRIMARY KEY (id);


--
-- Name: livrables livrables_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.livrables
    ADD CONSTRAINT livrables_pkey PRIMARY KEY (id);


--
-- Name: missions_districts missions_districts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.missions_districts
    ADD CONSTRAINT missions_districts_pkey PRIMARY KEY (id);


--
-- Name: missions missions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.missions
    ADD CONSTRAINT missions_pkey PRIMARY KEY (id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: participants participants_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.participants
    ADD CONSTRAINT participants_pkey PRIMARY KEY (id);


--
-- Name: phases phases_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.phases
    ADD CONSTRAINT phases_pkey PRIMARY KEY (id);


--
-- Name: pieces_jointes pieces_jointes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pieces_jointes
    ADD CONSTRAINT pieces_jointes_pkey PRIMARY KEY (id);


--
-- Name: politiques_conformite politiques_conformite_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.politiques_conformite
    ADD CONSTRAINT politiques_conformite_pkey PRIMARY KEY (id_politique);


--
-- Name: profils_comportementaux profils_comportementaux_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.profils_comportementaux
    ADD CONSTRAINT profils_comportementaux_pkey PRIMARY KEY (id_profil);


--
-- Name: rapport_difficultes rapport_difficultes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rapport_difficultes
    ADD CONSTRAINT rapport_difficultes_pkey PRIMARY KEY (id);


--
-- Name: rapports_audit rapports_audit_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rapports_audit
    ADD CONSTRAINT rapports_audit_pkey PRIMARY KEY (id_rapport);


--
-- Name: rapports_mission rapports_mission_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rapports_mission
    ADD CONSTRAINT rapports_mission_pkey PRIMARY KEY (id);


--
-- Name: ressources_sensibles ressources_sensibles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ressources_sensibles
    ADD CONSTRAINT ressources_sensibles_pkey PRIMARY KEY (id_ressource);


--
-- Name: roles_permissions roles_permissions_nom_role_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles_permissions
    ADD CONSTRAINT roles_permissions_nom_role_key UNIQUE (nom_role);


--
-- Name: roles_permissions roles_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles_permissions
    ADD CONSTRAINT roles_permissions_pkey PRIMARY KEY (id_role);


--
-- Name: scores_anomalie scores_anomalie_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scores_anomalie
    ADD CONSTRAINT scores_anomalie_pkey PRIMARY KEY (id_score);


--
-- Name: services_communes services_communes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.services_communes
    ADD CONSTRAINT services_communes_pkey PRIMARY KEY (id_service);


--
-- Name: types_activite types_activite_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.types_activite
    ADD CONSTRAINT types_activite_pkey PRIMARY KEY (id);


--
-- Name: participants uq_participants_equipe_utilisateur; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.participants
    ADD CONSTRAINT uq_participants_equipe_utilisateur UNIQUE (equipe_id, id_utilisateur);


--
-- Name: rapports_mission uq_rapports_mission_axe; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rapports_mission
    ADD CONSTRAINT uq_rapports_mission_axe UNIQUE (axe_id);


--
-- Name: utilisateurs utilisateurs_matricule_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.utilisateurs
    ADD CONSTRAINT utilisateurs_matricule_key UNIQUE (matricule);


--
-- Name: utilisateurs utilisateurs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.utilisateurs
    ADD CONSTRAINT utilisateurs_pkey PRIMARY KEY (id_utilisateur);


--
-- Name: ix_notifications_id_utilisateur; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_notifications_id_utilisateur ON public.notifications USING btree (id_utilisateur);


--
-- Name: ix_utilisateurs_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_utilisateurs_email ON public.utilisateurs USING btree (email);


--
-- Name: alertes_securite alertes_securite_id_politique_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alertes_securite
    ADD CONSTRAINT alertes_securite_id_politique_fkey FOREIGN KEY (id_politique) REFERENCES public.politiques_conformite(id_politique);


--
-- Name: alertes_securite alertes_securite_id_score_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alertes_securite
    ADD CONSTRAINT alertes_securite_id_score_fkey FOREIGN KEY (id_score) REFERENCES public.scores_anomalie(id_score);


--
-- Name: axes axes_mission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.axes
    ADD CONSTRAINT axes_mission_id_fkey FOREIGN KEY (mission_id) REFERENCES public.missions(id);


--
-- Name: benchmarking_services benchmarking_services_id_service_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.benchmarking_services
    ADD CONSTRAINT benchmarking_services_id_service_fkey FOREIGN KEY (id_service) REFERENCES public.services_communes(id_service);


--
-- Name: equipes equipes_axe_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipes
    ADD CONSTRAINT equipes_axe_id_fkey FOREIGN KEY (axe_id) REFERENCES public.axes(id);


--
-- Name: participants fk_participants_id_utilisateur_utilisateurs; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.participants
    ADD CONSTRAINT fk_participants_id_utilisateur_utilisateurs FOREIGN KEY (id_utilisateur) REFERENCES public.utilisateurs(id_utilisateur);


--
-- Name: indicateurs_performance indicateurs_performance_mission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.indicateurs_performance
    ADD CONSTRAINT indicateurs_performance_mission_id_fkey FOREIGN KEY (mission_id) REFERENCES public.missions(id);


--
-- Name: investigations investigations_id_alerte_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.investigations
    ADD CONSTRAINT investigations_id_alerte_fkey FOREIGN KEY (id_alerte) REFERENCES public.alertes_securite(id_alerte);


--
-- Name: investigations investigations_id_enqueteur_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.investigations
    ADD CONSTRAINT investigations_id_enqueteur_fkey FOREIGN KEY (id_enqueteur) REFERENCES public.utilisateurs(id_utilisateur);


--
-- Name: journal_acces journal_acces_id_ressource_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journal_acces
    ADD CONSTRAINT journal_acces_id_ressource_fkey FOREIGN KEY (id_ressource) REFERENCES public.ressources_sensibles(id_ressource);


--
-- Name: journal_acces journal_acces_id_utilisateur_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journal_acces
    ADD CONSTRAINT journal_acces_id_utilisateur_fkey FOREIGN KEY (id_utilisateur) REFERENCES public.utilisateurs(id_utilisateur);


--
-- Name: journees journees_mission_district_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journees
    ADD CONSTRAINT journees_mission_district_id_fkey FOREIGN KEY (mission_district_id) REFERENCES public.missions_districts(id);


--
-- Name: livrables livrables_phase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.livrables
    ADD CONSTRAINT livrables_phase_id_fkey FOREIGN KEY (phase_id) REFERENCES public.phases(id);


--
-- Name: missions_districts missions_districts_axe_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.missions_districts
    ADD CONSTRAINT missions_districts_axe_id_fkey FOREIGN KEY (axe_id) REFERENCES public.axes(id);


--
-- Name: missions_districts missions_districts_district_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.missions_districts
    ADD CONSTRAINT missions_districts_district_id_fkey FOREIGN KEY (district_id) REFERENCES public.districts(id);


--
-- Name: notifications notifications_id_utilisateur_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_id_utilisateur_fkey FOREIGN KEY (id_utilisateur) REFERENCES public.utilisateurs(id_utilisateur);


--
-- Name: participants participants_equipe_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.participants
    ADD CONSTRAINT participants_equipe_id_fkey FOREIGN KEY (equipe_id) REFERENCES public.equipes(id);


--
-- Name: phases phases_mission_district_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.phases
    ADD CONSTRAINT phases_mission_district_id_fkey FOREIGN KEY (mission_district_id) REFERENCES public.missions_districts(id);


--
-- Name: phases phases_type_activite_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.phases
    ADD CONSTRAINT phases_type_activite_id_fkey FOREIGN KEY (type_activite_id) REFERENCES public.types_activite(id);


--
-- Name: pieces_jointes pieces_jointes_id_mission_district_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pieces_jointes
    ADD CONSTRAINT pieces_jointes_id_mission_district_fkey FOREIGN KEY (id_mission_district) REFERENCES public.missions_districts(id);


--
-- Name: pieces_jointes pieces_jointes_id_rapport_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pieces_jointes
    ADD CONSTRAINT pieces_jointes_id_rapport_fkey FOREIGN KEY (id_rapport) REFERENCES public.rapports_mission(id);


--
-- Name: pieces_jointes pieces_jointes_id_televerseur_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pieces_jointes
    ADD CONSTRAINT pieces_jointes_id_televerseur_fkey FOREIGN KEY (id_televerseur) REFERENCES public.utilisateurs(id_utilisateur);


--
-- Name: profils_comportementaux profils_comportementaux_id_utilisateur_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.profils_comportementaux
    ADD CONSTRAINT profils_comportementaux_id_utilisateur_fkey FOREIGN KEY (id_utilisateur) REFERENCES public.utilisateurs(id_utilisateur);


--
-- Name: rapport_difficultes rapport_difficultes_id_rapport_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rapport_difficultes
    ADD CONSTRAINT rapport_difficultes_id_rapport_fkey FOREIGN KEY (id_rapport) REFERENCES public.rapports_mission(id);


--
-- Name: rapports_audit rapports_audit_id_service_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rapports_audit
    ADD CONSTRAINT rapports_audit_id_service_fkey FOREIGN KEY (id_service) REFERENCES public.services_communes(id_service);


--
-- Name: rapports_mission rapports_mission_axe_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rapports_mission
    ADD CONSTRAINT rapports_mission_axe_id_fkey FOREIGN KEY (axe_id) REFERENCES public.axes(id);


--
-- Name: rapports_mission rapports_mission_id_auteur_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rapports_mission
    ADD CONSTRAINT rapports_mission_id_auteur_fkey FOREIGN KEY (id_auteur) REFERENCES public.utilisateurs(id_utilisateur);


--
-- Name: rapports_mission rapports_mission_id_validateur_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rapports_mission
    ADD CONSTRAINT rapports_mission_id_validateur_fkey FOREIGN KEY (id_validateur) REFERENCES public.utilisateurs(id_utilisateur);


--
-- Name: ressources_sensibles ressources_sensibles_id_service_proprietaire_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ressources_sensibles
    ADD CONSTRAINT ressources_sensibles_id_service_proprietaire_fkey FOREIGN KEY (id_service_proprietaire) REFERENCES public.services_communes(id_service);


--
-- Name: scores_anomalie scores_anomalie_id_entree_journal_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scores_anomalie
    ADD CONSTRAINT scores_anomalie_id_entree_journal_fkey FOREIGN KEY (id_entree_journal) REFERENCES public.journal_acces(id_entree);


--
-- Name: scores_anomalie scores_anomalie_id_profil_reference_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scores_anomalie
    ADD CONSTRAINT scores_anomalie_id_profil_reference_fkey FOREIGN KEY (id_profil_reference) REFERENCES public.profils_comportementaux(id_profil);


--
-- Name: services_communes services_communes_id_service_parent_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.services_communes
    ADD CONSTRAINT services_communes_id_service_parent_fkey FOREIGN KEY (id_service_parent) REFERENCES public.services_communes(id_service);


--
-- Name: utilisateurs utilisateurs_id_role_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.utilisateurs
    ADD CONSTRAINT utilisateurs_id_role_fkey FOREIGN KEY (id_role) REFERENCES public.roles_permissions(id_role);


--
-- Name: utilisateurs utilisateurs_id_service_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.utilisateurs
    ADD CONSTRAINT utilisateurs_id_service_fkey FOREIGN KEY (id_service) REFERENCES public.services_communes(id_service);


--
-- PostgreSQL database dump complete
--

\unrestrict En3zLESXyoK4ZYZozBdxVfIgHs0heLlBC7A0gAdFKlVYv7ugzud16J9vYcCKHSx

