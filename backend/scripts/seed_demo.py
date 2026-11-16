#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seed_demo.py - Banque de données de démonstration pour la Plateforme d'audit (MID)

Génère des données cohérentes pour les deux modules :
  - gestion des missions (missions, axes, équipes, districts, phases, journées, rapports...)
  - audit comportemental (journal d'accès, profils, scores, alertes, investigations...)

Utilisation (PowerShell) :
  python seed_demo.py              -> simulation : génère en mémoire, vérifie la cohérence, n'écrit rien
  python seed_demo.py --inspect    -> affiche les valeurs réellement utilisées dans ta base (statuts, rôles...)
  python seed_demo.py --apply      -> VIDE les tables de données puis insère la démo (demande confirmation)

La table alembic_version n'est jamais touchée. Les rôles existants (roles_permissions) sont conservés.
Le mot de passe de tous les comptes de démo est : Demo@2026
"""
import argparse
import getpass
import os
import random
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

# Le journal de démonstration est haché avec LA fonction de l'application, et non
# avec une formule recopiée ici : l'ordre des champs doit être identique, sinon
# GET /journal/verify déclare la chaîne corrompue dès la première entrée.
try:
    from app.core.chaining import GENESIS_HASH, compute_hash
except ModuleNotFoundError:  # lancé depuis scripts/ : on ajoute backend/ au chemin
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.core.chaining import GENESIS_HASH, compute_hash

# --------------------------------------------------------------------------------------
# 1) VALEURS À VÉRIFIER AVEC  `python seed_demo.py --inspect`
#    (je ne connais pas les valeurs exactes attendues par ton application : adapte ici)
# --------------------------------------------------------------------------------------
DEMO_PASSWORD = "Demo@2026"

S = {
    "user": "actif",
    "mission": {"T": "terminee", "E": "en_cours", "P": "planifiee"},
    "district": {"T": "terminee", "E": "en_cours", "P": "planifiee"},
    "phase": {"T": "terminee", "E": "en_cours", "P": "planifiee"},
    "journee": {"T": "realisee", "E": "en_cours", "P": "planifiee"},
    "rapport": {"brouillon": "brouillon", "soumis": "soumis", "valide": "valide", "rejete": "rejete"},
    "demande": {"attente": "en_attente", "traitee": "traitee"},
    # Vocabulaire aligné sur l'application, sans quoi les données de démonstration
    # sont invisibles pour elle : schemas/audit.py (StatutAlerte), api/audit.py
    # (statuts d'investigation, compteurs du résumé) et core/alertes.py (gravités).
    "alerte": {"nouvelle": "nouvelle", "en_investigation": "en_investigation",
               "traitee": "traitee", "fausse_alerte": "fausse_alerte"},
    "investigation": {"ouverte": "ouverte", "cloturee": "cloturee"},
    "gravite": {"faible": "faible", "moyen": "moyen", "critique": "critique"},
    "service": {"ministere": "ministere", "direction": "direction", "service": "service"},
    "niveau": {"critique": "critique", "eleve": "eleve", "moyen": "moyen", "faible": "faible"},
}
ROLES_NIVEAU = {  # utilisé seulement si un rôle manque dans roles_permissions
    "administrateur": "admin", "chef_mission": "standard", "technicien": "standard",
    "agent": "standard", "auditeur": "audit", "responsable_hierarchique": "standard",
}

# --------------------------------------------------------------------------------------
# 2) Constantes générales
# --------------------------------------------------------------------------------------
random.seed(2026)  # résultats reproductibles
TZ = timezone(timedelta(hours=3))  # heure de Madagascar
NOW = datetime.now(TZ).replace(microsecond=0)
TODAY = NOW.date()


def at(d, h=9, m=0):
    return datetime(d.year, d.month, d.day, h, m, tzinfo=TZ)


def naive(d, h=0):
    return datetime(d.year, d.month, d.day, h, 0)


# Ordre de dépendance des tables (parents avant enfants) et nom de la clé primaire
PK = {
    "roles_permissions": "id_role", "services_communes": "id_service", "utilisateurs": "id_utilisateur",
    "districts": "id", "types_activite": "id", "missions": "id", "axes": "id", "equipes": "id",
    "participants": "id", "missions_districts": "id", "phases": "id", "livrables": "id",
    "journees": "id", "indicateurs_performance": "id", "rapports_mission": "id",
    "rapport_difficultes": "id", "notifications": "id", "demandes_mot_de_passe": "id",
    "echecs_connexion": "id", "politiques_conformite": "id_politique",
    "ressources_sensibles": "id_ressource", "profils_comportementaux": "id_profil",
    "journal_acces": "id_entree", "scores_anomalie": "id_score", "alertes_securite": "id_alerte",
    "investigations": "id_investigation", "benchmarking_services": "id_benchmark",
    "rapports_audit": "id_rapport",
}
# Tables vidées avant insertion (roles_permissions est conservée, alembic_version aussi)
TO_TRUNCATE = [t for t in PK if t != "roles_permissions"] + ["pieces_jointes"]

FK = {
    ("utilisateurs", "id_service"): "services_communes", ("utilisateurs", "id_role"): "roles_permissions",
    ("services_communes", "id_service_parent"): "services_communes",
    ("axes", "mission_id"): "missions", ("equipes", "axe_id"): "axes",
    ("participants", "equipe_id"): "equipes", ("participants", "id_utilisateur"): "utilisateurs",
    ("missions_districts", "axe_id"): "axes", ("missions_districts", "district_id"): "districts",
    ("phases", "mission_district_id"): "missions_districts", ("phases", "type_activite_id"): "types_activite",
    ("livrables", "phase_id"): "phases", ("journees", "mission_district_id"): "missions_districts",
    ("indicateurs_performance", "mission_id"): "missions",
    ("rapports_mission", "axe_id"): "axes", ("rapports_mission", "id_auteur"): "utilisateurs",
    ("rapports_mission", "id_validateur"): "utilisateurs",
    ("rapport_difficultes", "id_rapport"): "rapports_mission",
    ("notifications", "id_utilisateur"): "utilisateurs",
    ("demandes_mot_de_passe", "id_utilisateur"): "utilisateurs",
    ("demandes_mot_de_passe", "id_traitant"): "utilisateurs",
    ("ressources_sensibles", "id_service_proprietaire"): "services_communes",
    ("profils_comportementaux", "id_utilisateur"): "utilisateurs",
    ("journal_acces", "id_utilisateur"): "utilisateurs", ("journal_acces", "id_ressource"): "ressources_sensibles",
    ("scores_anomalie", "id_entree_journal"): "journal_acces",
    ("scores_anomalie", "id_profil_reference"): "profils_comportementaux",
    ("alertes_securite", "id_score"): "scores_anomalie", ("alertes_securite", "id_politique"): "politiques_conformite",
    ("investigations", "id_alerte"): "alertes_securite", ("investigations", "id_enqueteur"): "utilisateurs",
    ("benchmarking_services", "id_service"): "services_communes", ("rapports_audit", "id_service"): "services_communes",
}


class Store:
    """Accumule les lignes en mémoire, avec des identifiants explicites."""

    def __init__(self):
        self.rows = {t: [] for t in PK}
        self.ids = {t: set() for t in PK}
        self.next = defaultdict(lambda: 1)
        self.cols = {}

    def add(self, table, **row):
        rid = self.next[table]
        self.next[table] += 1
        row = {PK[table]: rid, **row}
        cols = tuple(sorted(row))
        if self.cols.setdefault(table, cols) != cols:
            raise ValueError(f"Colonnes incohérentes pour {table}")
        self.rows[table].append(row)
        self.ids[table].add(rid)
        return rid

    def register_existing(self, table, rid):
        self.ids[table].add(rid)


# --------------------------------------------------------------------------------------
# 3) Données de référence
# --------------------------------------------------------------------------------------
PRENOMS = ["Hery", "Tahina", "Faly", "Mamy", "Nirina", "Voahangy", "Lalaina", "Soa", "Haingo", "Fanja",
           "Rivo", "Toky", "Andry", "Miora", "Nomena", "Sitraka", "Tiana", "Zo", "Lova", "Aina", "Mialy",
           "Rojo", "Njaka", "Fidy", "Vola", "Hanitra", "Ony", "Tsiory", "Mahefa", "Bakoly"]
NOMS = ["Rakotoarisoa", "Randrianarivelo", "Rasolofonirina", "Razafindrakoto", "Andrianasolo",
        "Ratsimbazafy", "Rabemananjara", "Rakotomalala", "Randriamampionona", "Ravelojaona", "Rasoanaivo",
        "Andriamanantena", "Razanamahefa", "Rakotonirina", "Ramanantsoa", "Randrianasolo", "Rajaonarison",
        "Raharimanana", "Rafanomezantsoa", "Andrianjafy"]

DEMO_LOGINS = {  # un compte facile à retenir par rôle
    "administrateur": ("Hery", "Rakotoarisoa", "admin"),
    "chef_mission": ("Tahina", "Randrianarivelo", "chef"),
    "technicien": ("Faly", "Rasolofonirina", "technicien"),
    "agent": ("Voahangy", "Razafindrakoto", "agent"),
    "auditeur": ("Mamy", "Andrianasolo", "auditeur"),
    "responsable_hierarchique": ("Lalaina", "Ratsimbazafy", "responsable"),
}

DISTRICTS = {
    "Ambatolampy": ("Vakinankaratra", "Antananarivo", True), "Antsirabe I": ("Vakinankaratra", "Antananarivo", True),
    "Ambositra": ("Amoron'i Mania", "Fianarantsoa", True), "Fianarantsoa I": ("Haute Matsiatra", "Fianarantsoa", True),
    "Arivonimamo": ("Itasy", "Antananarivo", True), "Miarinarivo": ("Itasy", "Antananarivo", True),
    "Soavinandriana": ("Itasy", "Antananarivo", False), "Manjakandriana": ("Analamanga", "Antananarivo", True),
    "Brickaville": ("Atsinanana", "Toamasina", True), "Toamasina I": ("Atsinanana", "Toamasina", True),
    "Fenoarivo Atsinanana": ("Analanjirofo", "Toamasina", True), "Maroantsetra": ("Analanjirofo", "Toamasina", False),
    "Ambilobe": ("Diana", "Antsiranana", True), "Antsiranana I": ("Diana", "Antsiranana", True),
    "Nosy Be": ("Diana", "Antsiranana", True), "Sambava": ("Sava", "Antsiranana", True),
    "Antalaha": ("Sava", "Antsiranana", True), "Ankazobe": ("Analamanga", "Antananarivo", False),
    "Ambato-Boeny": ("Boeny", "Mahajanga", False), "Marovoay": ("Boeny", "Mahajanga", True),
    "Mahajanga I": ("Boeny", "Mahajanga", True), "Maintirano": ("Melaky", "Mahajanga", False),
    "Port-Bergé": ("Sofia", "Mahajanga", False), "Ihosy": ("Ihorombe", "Fianarantsoa", False),
    "Toliara I": ("Atsimo-Andrefana", "Toliara", True), "Morondava": ("Menabe", "Toliara", True),
    "Betioky": ("Atsimo-Andrefana", "Toliara", False), "Farafangana": ("Atsimo-Atsinanana", "Fianarantsoa", False),
    "Manakara": ("Vatovavy-Fitovinany", "Fianarantsoa", True),
}

# (titre, type, décalage du début en jours, durée, statut, axes[(itinéraire, [(district, T/E/P)])])
MISSIONS = [
    ("Déploiement du réseau sécurisé – Hauts Plateaux", "deploiement", -270, 25, "T", [
        ("RN7", [("Ambatolampy", "T"), ("Antsirabe I", "T"), ("Ambositra", "T"), ("Fianarantsoa I", "T")]),
        ("RN1", [("Arivonimamo", "T"), ("Miarinarivo", "T"), ("Soavinandriana", "T")])]),
    ("Formation des agents – Côte Est", "formation", -210, 20, "T", [
        ("RN2", [("Manjakandriana", "T"), ("Brickaville", "T"), ("Toamasina I", "T")]),
        ("RN5", [("Fenoarivo Atsinanana", "T"), ("Maroantsetra", "T")])]),
    ("Maintenance et audit des installations – Nord", "maintenance", -140, 18, "T", [
        ("RN6", [("Ambilobe", "T"), ("Antsiranana I", "T"), ("Nosy Be", "T")]),
        ("RN5A", [("Sambava", "T"), ("Antalaha", "T")])]),
    ("Déploiement du réseau sécurisé – Ouest", "deploiement", -8, 20, "E", [
        ("RN4", [("Ankazobe", "T"), ("Ambato-Boeny", "T"), ("Marovoay", "E"), ("Mahajanga I", "P")]),
        ("Axe Maintirano", [("Maintirano", "T"), ("Port-Bergé", "E")])]),
    ("Formation des agents – Sud-Ouest", "formation", -2, 14, "E", [
        ("RN7 Sud", [("Ihosy", "E"), ("Toliara I", "P")]),
        ("RN9", [("Morondava", "E"), ("Betioky", "P")])]),
    ("Déploiement du réseau sécurisé – Sud-Est", "deploiement", 30, 25, "P", [
        ("RN12", [("Manakara", "P"), ("Farafangana", "P")]),
        ("RN7 Sud-Est", [("Ambositra", "P"), ("Fianarantsoa I", "P")])]),
]
# Statut des rapports de mission par (indice mission, indice axe)
RAPPORTS_PLAN = {(0, 0): "valide", (0, 1): "valide", (1, 0): "valide", (1, 1): "rejete",
                 (2, 0): "valide", (2, 1): "soumis", (3, 0): "brouillon"}

PHASES = [
    ("Installation des équipements", "2 jours", "PV d'installation",
     "Installation des postes, du câblage et de l'onduleur"),
    ("Configuration réseau", "1 jour", "Fiche de configuration",
     "Configuration du réseau local, des VLAN et de l'accès VPN"),
    ("Tests de sécurité", "1 jour", "Rapport de tests de sécurité",
     "Tests d'authentification, de segmentation et de sauvegarde"),
    ("Formation des agents", "2 jours", "Liste de présence et évaluation",
     "Formation des agents locaux et remise du PV de fin d'intervention"),
]
DIFFICULTES = [
    ("Énergie", "Coupures d'électricité fréquentes pendant l'installation",
     "Utilisation d'un onduleur et d'un kit solaire d'appoint"),
    ("Logistique", "Route difficile d'accès en saison des pluies, retard de deux jours",
     "Replanification des journées et départ anticipé vers le district suivant"),
    ("Connectivité", "Liaison internet instable dans le district",
     "Configuration d'un lien de secours et mise en cache locale"),
    ("Ressources humaines", "Indisponibilité du responsable local le jour de la formation",
     "Session reprogrammée le lendemain"),
    ("Sécurité", "Local informatique non sécurisé",
     "Installation d'une armoire fermée à clé et sensibilisation du chef de district"),
]
ECARTS = ["Coupure d'électricité de trois heures", "Arrivée tardive du matériel", "Absence du responsable local",
          "Pluies abondantes, activité reportée en fin de journée"]

RESSOURCES = [  # (libellé, niveau, service propriétaire)
    ("Base de données des agents (RH)", "critique", "DRH"), ("Fichiers de paie", "critique", "DAF"),
    ("Registre d'état civil", "critique", "DDEC"), ("Dossiers d'audit", "eleve", "IG"),
    ("Serveur de sauvegarde", "critique", "RS"), ("Cartographie des districts", "moyen", "DDEC"),
    ("Rapports de mission", "moyen", "SUP"), ("Annuaire des utilisateurs", "faible", "DSI"),
    ("Données électorales", "critique", "DDEC"), ("Journal des accès", "eleve", "RS"),
]

# Accès journalisés par jour ouvré et par service. Chaque service a son propre
# rythme : un tirage uniforme sur les comptes donnerait un volume proportionnel
# au seul effectif, et les services de deux agents resteraient sous le seuil de
# classement du benchmarking (MIN_ACCES_CLASSEMENT dans core/benchmarking.py).
ACTIVITE_PAR_SERVICE = {
    "RS": (5, 9), "SUP": (5, 9), "DSI": (3, 6), "DDEC": (4, 7),
    "DRH": (3, 6), "DAF": (4, 7), "SG": (2, 5), "IG": (3, 7),
}
ACTIVITE_DEFAUT = (2, 4)

# Mêmes seuils que core/alertes.py : alerte à partir de |z| = 3, « moyen » à
# partir de 4.5, « critique » à partir de 6.
SEUIL_GRAVITE_MOYEN = 4.5
SEUIL_GRAVITE_CRITIQUE = 6.0


# --------------------------------------------------------------------------------------
# 4) Construction des données
# --------------------------------------------------------------------------------------
def slug(s):
    return s.lower().replace("é", "e").replace("è", "e").replace(" ", "")


def month_label(dt):
    return dt.strftime("%Y-%m")


def build(roles, pw_hash):
    st = Store()
    for name, rid in roles.items():
        st.register_existing("roles_permissions", rid)

    # ---- Services -------------------------------------------------------------------
    svc = {}
    T = S["service"]
    svc["MID"] = st.add("services_communes", nom_service="Ministère de l'Intérieur et de la Décentralisation",
                        type=T["ministere"], id_service_parent=None)
    for key, nom in [("SG", "Secrétariat Général"), ("DSI", "Direction des Systèmes d'Information"),
                     ("DRH", "Direction des Ressources Humaines"), ("DDEC", "Direction de la Décentralisation"),
                     ("IG", "Inspection Générale"), ("DAF", "Direction des Affaires Financières")]:
        svc[key] = st.add("services_communes", nom_service=nom, type=T["direction"], id_service_parent=svc["MID"])
    for key, nom, parent in [("RS", "Service Réseaux et Sécurité", "DSI"), ("DEV", "Service Développement", "DSI"),
                             ("SUP", "Service Support et Maintenance", "DSI"),
                             ("SSTAT", "Service Statistique", "DDEC")]:
        svc[key] = st.add("services_communes", nom_service=nom, type=T["service"], id_service_parent=svc[parent])

    # ---- Utilisateurs ---------------------------------------------------------------
    spec = [("administrateur", ["DSI", "DSI"]),
            ("chef_mission", ["RS", "RS", "RS", "SUP", "SUP", "SUP"]),
            ("technicien", ["SUP"] * 5 + ["RS"] * 5),
            ("agent", ["DDEC", "DDEC", "DDEC", "DRH", "DRH", "DAF", "DAF", "SG"]),
            ("auditeur", ["IG", "IG", "IG"]),
            ("responsable_hierarchique", ["SG", "DAF", "DRH"])]
    used_names = {(p, n) for p, n, _ in DEMO_LOGINS.values()}
    mat = 0
    U = defaultdict(list)
    rng = random.Random(7)
    for role, services in spec:
        for i, skey in enumerate(services):
            if i == 0:
                prenom, nom, local = DEMO_LOGINS[role]
                email = f"{local}@mid.gov.mg"
            else:
                while True:
                    prenom, nom = rng.choice(PRENOMS), rng.choice(NOMS)
                    if (prenom, nom) not in used_names:
                        used_names.add((prenom, nom))
                        break
                email = f"{slug(prenom)}.{slug(nom)}@mid.gov.mg"
            mat += 1
            uid = st.add("utilisateurs", nom=nom, prenom=prenom, email=email, matricule=f"MID-{mat:04d}",
                         mot_de_passe_hash=pw_hash, id_service=svc[skey], id_role=roles[role], statut=S["user"],
                         date_creation=at(TODAY - timedelta(days=rng.randint(320, 420)), 9))
            U[role].append({"id": uid, "nom": f"{prenom} {nom}", "service": skey, "role": role, "email": email,
                            "ip": f"10.20.{len(U['_all']) % 40 + 1}.{10 + len(U['_all'])}"})
            U["_all"].append(U[role][-1])
    users_by_id = {u["id"]: u for u in U["_all"]}
    admin_id = U["administrateur"][0]["id"]

    # ---- Districts, types d'activité ------------------------------------------------
    dist_id = {}
    for nom, (region, province, elec) in DISTRICTS.items():
        dist_id[nom] = st.add("districts", nom=nom, region=region, province=province, electrifie=elec)
    type_id = [st.add("types_activite", libelle=p[0]) for p in PHASES]

    # ---- Missions -------------------------------------------------------------------
    axe_global = 0
    report_info = []  # (rapport_id, chef_id, statut, date_soumission)
    mission_stats = []
    for mi, (titre, mtype, off, duree, mstat, axes) in enumerate(MISSIONS):
        start = TODAY + timedelta(days=off)
        mid = st.add("missions", titre=titre, type_mission=mtype, date_debut=naive(start),
                     date_fin_prevue=naive(start + timedelta(days=duree)), statut=S["mission"][mstat])
        nb_dist = done = 0
        for ai, (itin, districts) in enumerate(axes):
            axe_id = st.add("axes", mission_id=mid, numero_axe=ai + 1, itineraire_principal=itin)
            # équipe : 1 chef, 2 techniciens, 1 agent (formateur)
            chef = U["chef_mission"][axe_global % 6]
            techs = [U["technicien"][(2 * axe_global) % 10], U["technicien"][(2 * axe_global + 1) % 10]]
            agent = U["agent"][axe_global % 8]
            etype = {"deploiement": "Équipe de déploiement", "formation": "Équipe de formation",
                     "maintenance": "Équipe de maintenance"}[mtype]
            eq = st.add("equipes", axe_id=axe_id, type_equipe=etype)
            for u, fonction in [(chef, "Chef d'équipe"), (techs[0], "Technicien réseau"),
                                (techs[1], "Technicien sécurité"), (agent, "Formateur")]:
                st.add("participants", equipe_id=eq, nom=u["nom"], fonction=fonction, id_utilisateur=u["id"])
            axe_global += 1

            codes = [c for _, c in districts]
            idx_e = codes.index("E") if "E" in codes else None
            last_date = start
            for order, (dname, code) in enumerate(districts, start=1):
                if idx_e is not None:
                    dstart = TODAY - timedelta(days=1) + timedelta(days=(order - 1 - idx_e) * 4)
                else:
                    dstart = start + timedelta(days=(order - 1) * 4)
                last_date = max(last_date, dstart + timedelta(days=2))
                md = st.add("missions_districts", axe_id=axe_id, district_id=dist_id[dname], ordre_visite=order,
                            statut=S["district"][code])
                nb_dist += 1
                done += code == "T"
                phase_codes = {"T": "TTTT", "E": "TTEP", "P": "PPPP"}[code]
                for pi, (plabel, pdur, plivr, _) in enumerate(PHASES):
                    pid = st.add("phases", mission_district_id=md, type_activite_id=type_id[pi],
                                 numero_ordre=pi + 1, duree_prevue=pdur, livrable_attendu=plivr,
                                 statut=S["phase"][phase_codes[pi]])
                    if phase_codes[pi] == "T":
                        st.add("livrables", phase_id=pid, type_livrable=plivr,
                               date_production=naive(dstart + timedelta(days=min(pi, 2)), 16), signe=True,
                               fichier=None)
                jcodes = {"T": "TTT", "E": "TEP", "P": "PPP"}[code]
                offsets = [-1, 0, 1] if code == "E" else [0, 1, 2]
                prevues = [PHASES[0][3], PHASES[1][3] + " et " + PHASES[2][3].lower(), PHASES[3][3]]
                for n in range(3):
                    realise = prevues[n] if jcodes[n] == "T" else None
                    ecart = None
                    if jcodes[n] == "T" and rng.random() < 0.25:
                        ecart = rng.choice(ECARTS)
                        realise = prevues[n] + " (partiellement, voir écart)"
                    st.add("journees", mission_district_id=md, numero_jour=n + 1,
                           date=dstart + timedelta(days=offsets[n]),
                           lieu=f"{rng.choice(['Préfecture', 'Mairie', 'Bureau du district', 'Centre de formation'])} de {dname}",
                           statut=S["journee"][jcodes[n]], activites_prevues=prevues[n],
                           activites_realisees=realise, ecart=ecart)

            # rapport de mission
            plan = RAPPORTS_PLAN.get((mi, ai))
            if plan:
                dnames = [d for d, _ in districts]
                rid = make_rapport(st, plan, titre, ai + 1, itin, dnames, axe_id, chef["id"], admin_id, last_date)
                report_info.append((rid, chef["id"], plan))

        # indicateurs de performance
        dev = mstat != "P"
        st.add("indicateurs_performance", mission_id=mid, resultat_attendu="Districts équipés d'un accès sécurisé",
               indicateur_mesure="Nombre de districts équipés", cible=str(nb_dist),
               valeur_realisee=str(done) if dev else None)
        st.add("indicateurs_performance", mission_id=mid, resultat_attendu="Agents locaux formés",
               indicateur_mesure="Nombre d'agents formés", cible=str(nb_dist * 12),
               valeur_realisee=str(done * rng.randint(10, 12)) if dev else None)
        st.add("indicateurs_performance", mission_id=mid, resultat_attendu="Réseau disponible",
               indicateur_mesure="Taux de disponibilité", cible="95 %",
               valeur_realisee=f"{rng.randint(92, 98)} %" if dev and done else None)

    # ---- Demandes de mot de passe, échecs de connexion, notifications ----------------
    tech_ids = [u["id"] for u in U["technicien"]]
    st.add("demandes_mot_de_passe", id_utilisateur=tech_ids[4], motif="Mot de passe oublié après le retour de mission",
           statut=S["demande"]["attente"], date_demande=NOW - timedelta(hours=5), id_traitant=None,
           date_traitement=None)
    for k, uid in enumerate([U["agent"][2]["id"], U["chef_mission"][5]["id"]]):
        d0 = NOW - timedelta(days=9 + 6 * k)
        st.add("demandes_mot_de_passe", id_utilisateur=uid, motif="Compte verrouillé après plusieurs tentatives",
               statut=S["demande"]["traitee"], date_demande=d0, id_traitant=admin_id,
               date_traitement=d0 + timedelta(hours=3))
    emails = [u["email"] for u in U["_all"]]
    for _ in range(14):
        st.add("echecs_connexion", email=rng.choice(emails), adresse_ip=f"10.20.{rng.randint(1, 40)}.{rng.randint(10, 60)}",
               date_echec=NOW - timedelta(days=rng.randint(0, 10), minutes=rng.randint(0, 1400)))
    burst = NOW - timedelta(days=2, hours=1)  # tentative de force brute sur le compte administrateur
    for k in range(9):
        st.add("echecs_connexion", email="admin@mid.gov.mg", adresse_ip="197.149.42.18",
               date_echec=burst + timedelta(seconds=25 * k))

    for rid, chef_id, plan in report_info:
        if plan == "soumis":
            st.add("notifications", id_utilisateur=admin_id, type_notification="rapport_soumis",
                   message="Un rapport de mission est en attente de validation.", lien=None, lue=False,
                   date_creation=NOW - timedelta(days=3))
        elif plan == "valide":
            st.add("notifications", id_utilisateur=chef_id, type_notification="rapport_valide",
                   message="Votre rapport de mission a été validé.", lien=None, lue=True,
                   date_creation=NOW - timedelta(days=rng.randint(30, 200)))
        elif plan == "rejete":
            st.add("notifications", id_utilisateur=chef_id, type_notification="rapport_rejete",
                   message="Votre rapport de mission a été rejeté : des corrections sont demandées.", lien=None,
                   lue=False, date_creation=NOW - timedelta(days=rng.randint(30, 60)))
    st.add("notifications", id_utilisateur=admin_id, type_notification="demande_mot_de_passe",
           message="Nouvelle demande de réinitialisation de mot de passe.", lien=None, lue=False,
           date_creation=NOW - timedelta(hours=5))

    # ---- Audit comportemental ---------------------------------------------------------
    pol = {}
    for key, nom, desc, seuil in [
        ("horaires", "Accès hors horaires", "Accès à une ressource sensible en dehors des horaires habituels",
         "z_score >= 3.0"),
        ("volume", "Volume de téléchargement anormal", "Volume d'exports très supérieur à la moyenne du profil",
         "z_score >= 3.0"),
        ("perimetre", "Accès hors périmètre", "Accès à une ressource hors du périmètre habituel de l'utilisateur",
         "z_score >= 3.0")]:
        pol[key] = st.add("politiques_conformite", nom_politique=nom, description=desc, seuils_configures=seuil,
                          date_effective=at(TODAY - timedelta(days=300), 9))

    res = {}
    for label, niveau, skey in RESSOURCES:
        res[label] = st.add("ressources_sensibles", type_ressource=label, niveau_sensibilite=S["niveau"][niveau],
                            id_service_proprietaire=svc[skey])
    R = lambda label: res[label]  # noqa: E731

    own_res = {"DRH": "Base de données des agents (RH)", "DAF": "Fichiers de paie", "DDEC": "Registre d'état civil",
               "IG": "Dossiers d'audit"}
    base_res = {
        "administrateur": ["Rapports de mission", "Annuaire des utilisateurs", "Journal des accès", "Serveur de sauvegarde"],
        "chef_mission": ["Rapports de mission", "Cartographie des districts", "Annuaire des utilisateurs"],
        "technicien": ["Rapports de mission", "Cartographie des districts", "Annuaire des utilisateurs"],
        "agent": ["Cartographie des districts", "Annuaire des utilisateurs", "Rapports de mission"],
        "auditeur": ["Dossiers d'audit", "Journal des accès", "Rapports de mission", "Annuaire des utilisateurs"],
        "responsable_hierarchique": ["Rapports de mission", "Annuaire des utilisateurs"],
    }
    normal_res = {}
    for u in U["_all"]:
        labels = list(base_res[u["role"]])
        if u["service"] in own_res:
            labels.append(own_res[u["service"]])
        normal_res[u["id"]] = [R(x) for x in labels]

    prev_month = month_label(TODAY.replace(day=1) - timedelta(days=1))
    profil = {}
    for u in U["_all"]:
        hrs = "07:30-18:00" if u["role"] == "administrateur" else "08:00-17:00"
        perim = ", ".join(r for r in [x for x in base_res[u["role"]]] + ([own_res[u["service"]]] if u["service"] in own_res else []))
        profil[u["id"]] = st.add("profils_comportementaux", id_utilisateur=u["id"], periode_reference=prev_month,
                                 volume_moyen=round(rng.uniform(6, 30), 1), horaires_habituels=hrs,
                                 perimetre_habituel=perim[:255], date_calcul=NOW - timedelta(days=3))

    agents_par_service = defaultdict(list)
    for u in U["_all"]:
        agents_par_service[u["service"]].append(u)

    def acteur(role, skey):
        """Un compte de ce rôle dans ce service, pour situer un scénario d'anomalie."""
        return next(u for u in U[role] if u["service"] == skey)

    # Journal : accès normaux sur 90 jours, service par service
    raw = []  # (ts, uid, rid, action, z, tag)
    for k in range(90, -1, -1):
        d = TODAY - timedelta(days=k)
        if d.weekday() >= 5:
            continue
        for skey, agents in agents_par_service.items():
            bas, haut = ACTIVITE_PAR_SERVICE.get(skey, ACTIVITE_DEFAUT)
            for _ in range(rng.randint(bas, haut)):
                u = rng.choice(agents)
                ts = at(d, rng.randint(8, 16), rng.randint(0, 59)) + timedelta(seconds=rng.randint(0, 59))
                if ts > NOW:
                    continue
                act = rng.choices(["consultation", "modification", "export", "creation"], [70, 18, 6, 6])[0]
                z = max(-2.4, min(2.4, round(rng.gauss(0, 0.9), 2)))
                raw.append((ts, u["id"], rng.choice(normal_res[u["id"]]), act, z, None))

    # Scénarios d'anomalies, répartis sur six services et sur les trois derniers
    # mois : sans cette répartition, la médiane du taux d'alertes d'un type de
    # service reste à zéro et le benchmarking n'a rien à comparer.
    tech_a = acteur("technicien", "SUP")
    agent_b = acteur("agent", "DRH")
    resp_c = acteur("responsable_hierarchique", "DAF")
    audit_d = acteur("auditeur", "IG")
    agent_e = acteur("agent", "DDEC")
    tech_f = acteur("technicien", "RS")

    # A (SUP, mois en cours) : exports de nuit sur les fichiers de paie
    for k, dd in enumerate([12, 10, 9, 6, 4, 2]):
        ts = at(TODAY - timedelta(days=dd), 2, rng.randint(0, 50))
        z = round(rng.uniform(6.2, 7.2), 2) if k < 2 else round(rng.uniform(4.6, 5.9), 2)
        raw.append((ts, tech_a["id"], R("Fichiers de paie"), "export", z, "A"))
    # B (DRH, mois précédent) : agent RH qui consulte des données électorales
    for dd in [21, 20, 20, 19]:
        ts = at(TODAY - timedelta(days=dd), rng.randint(10, 15), rng.randint(0, 59))
        raw.append((ts, agent_b["id"], R("Données électorales"), "consultation",
                    round(rng.uniform(3.1, 3.7), 2), "B"))
    # C (DAF, mois en cours) : rafale d'exports de la base RH
    for k in range(25):
        ts = at(TODAY - timedelta(days=3), 13, 0) + timedelta(seconds=50 * k)
        raw.append((ts, resp_c["id"], R("Base de données des agents (RH)"), "export",
                    round(rng.uniform(4.6, 5.4), 2) if k >= 22 else round(rng.uniform(1.2, 2.3), 2), "C"))
    # D (IG, mois précédent) : auditeur qui exporte le journal des accès la nuit
    for dd in [40, 38, 36]:
        ts = at(TODAY - timedelta(days=dd), 1, rng.randint(0, 50))
        raw.append((ts, audit_d["id"], R("Journal des accès"), "export",
                    round(rng.uniform(5.0, 6.8), 2), "D"))
    # E (DDEC, il y a deux mois) : agent qui consulte des fichiers de paie
    for dd in [55, 54]:
        ts = at(TODAY - timedelta(days=dd), rng.randint(9, 16), rng.randint(0, 59))
        raw.append((ts, agent_e["id"], R("Fichiers de paie"), "consultation",
                    round(rng.uniform(3.2, 3.9), 2), "E"))
    # F (RS, mois en cours) : technicien qui accède au serveur de sauvegarde
    for k in range(12):
        ts = at(TODAY - timedelta(days=8), 21, 0) + timedelta(minutes=4 * k)
        raw.append((ts, tech_f["id"], R("Serveur de sauvegarde"), "export",
                    round(rng.uniform(3.6, 4.9), 2) if k >= 9 else round(rng.uniform(1.4, 2.4), 2), "F"))
    raw.sort(key=lambda r: r[0])

    # Adresses extérieures pour les scénarios qui le justifient (export de nuit
    # depuis un poste inconnu) ; sinon l'adresse habituelle de l'agent.
    IP_SCENARIO = {"A": "41.204.17.9", "D": "41.188.22.4", "F": "10.20.99.7"}

    prev_hash = GENESIS_HASH
    scen = defaultdict(list)
    for ts, uid, rid, act, z, tag in raw:
        ip = IP_SCENARIO.get(tag) or users_by_id[uid]["ip"]
        h = compute_hash(id_utilisateur=uid, id_ressource=rid, type_action=act,
                         horodatage=ts, hash_precedent=prev_hash)
        eid = st.add("journal_acces", id_utilisateur=uid, id_ressource=rid, type_action=act, horodatage=ts,
                     adresse_ip=ip, hash_entree=h, hash_precedent=prev_hash)
        prev_hash = h
        sid = st.add("scores_anomalie", id_entree_journal=eid, id_profil_reference=profil[uid], z_score=z,
                     methode_utilisee="z-score", date_calcul=ts + timedelta(minutes=5))
        if tag:
            scen[tag].append((z, sid, ts))

    def gravite(z):
        """Mêmes seuils que core.alertes.evaluer_alerte."""
        if z >= SEUIL_GRAVITE_CRITIQUE:
            return S["gravite"]["critique"]
        if z >= SEUIL_GRAVITE_MOYEN:
            return S["gravite"]["moyen"]
        return S["gravite"]["faible"]

    # Par scénario : politique déclenchée, nombre d'alertes retenues (les plus
    # fortes) et suite donnée à la plus forte d'entre elles. Les deux issues d'une
    # investigation close sont « fausse_alerte » (exclue du benchmarking, car une
    # alerte infirmée n'est pas du risque) et « traitee » (anomalie confirmée).
    scenarios_alertes = [
        ("A", "horaires", 3, "en_investigation"),
        ("B", "perimetre", 1, "fausse_alerte"),
        ("C", "volume", 2, "nouvelle"),
        ("D", "horaires", 2, "en_investigation"),
        ("E", "perimetre", 1, "traitee"),
        ("F", "perimetre", 2, "nouvelle"),
    ]
    conclusions = {
        "B": "Faux positif : agent détaché temporairement auprès de la Direction de la "
             "Décentralisation pour l'inventaire des données.",
        "E": "Accès hors périmètre confirmé : l'agent consultait des fichiers de paie "
             "sans rapport avec ses attributions. Droit d'accès retiré sur la ressource.",
    }
    auditeurs = U["auditeur"]
    for num, (tag, polkey, count, suite) in enumerate(scenarios_alertes):
        top = sorted(scen[tag], reverse=True)[:count]
        for rank, (z, sid, ts) in enumerate(top):
            created = ts + timedelta(minutes=10)
            # Seule l'alerte la plus forte du scénario reçoit la suite prévue :
            # les autres restent à traiter.
            statut = S["alerte"][suite] if rank == 0 else S["alerte"]["nouvelle"]
            aid = st.add("alertes_securite", id_score=sid, id_politique=pol[polkey],
                         niveau_gravite=gravite(z), statut=statut, date_creation=created)
            if rank != 0:
                continue
            enqueteur = auditeurs[num % len(auditeurs)]["id"]
            if statut == S["alerte"]["en_investigation"]:
                st.add("investigations", id_alerte=aid, id_enqueteur=enqueteur,
                       statut=S["investigation"]["ouverte"], conclusion=None,
                       date_ouverture=min(NOW, created + timedelta(days=1)), date_cloture=None)
            elif tag in conclusions:
                st.add("investigations", id_alerte=aid, id_enqueteur=enqueteur,
                       statut=S["investigation"]["cloturee"], conclusion=conclusions[tag],
                       date_ouverture=created + timedelta(days=1),
                       date_cloture=created + timedelta(days=4))
    for a in U["auditeur"][:2]:
        st.add("notifications", id_utilisateur=a["id"], type_notification="alerte_securite",
               message="Nouvelles alertes de sécurité à examiner.", lien=None, lue=False,
               date_creation=NOW - timedelta(days=2))

    # Le benchmarking par service et les synthèses d'audit ne sont PAS fabriqués
    # ici : ils sont calculés par app/core/benchmarking.py à partir du journal et
    # des alertes de la période. Un jeu de démonstration qui pré-remplirait le
    # résultat du calcul masquerait justement ce que le calcul doit démontrer.
    # Après ce seed : clôturer une période depuis la page Benchmarking, ou
    # POST /benchmarking/calculer?periode=AAAA-MM.
    return st, U


def make_rapport(st, plan, titre, axe_no, itin, dnames, axe_id, chef_id, admin_id, last_date):
    r = random.Random(axe_id)
    full = plan != "brouillon"
    if plan == "soumis":
        created, modif, soum = NOW - timedelta(days=5), NOW - timedelta(days=3), NOW - timedelta(days=3)
    elif plan == "brouillon":
        created, modif, soum = NOW - timedelta(days=1, hours=2), NOW - timedelta(hours=8), None
    else:
        created = at(last_date + timedelta(days=1), 9)
        modif = created + timedelta(days=1)
        soum = created + timedelta(days=2, hours=1)
    valid = plan in ("valide", "rejete")
    val_date = soum + timedelta(days=3, hours=2) if valid else None
    comment = {"valide": "Rapport conforme, validé.",
               "rejete": "La section « tests de sécurité » est trop succincte : merci de détailler les résultats "
                         "par district avant de soumettre à nouveau."}.get(plan)
    n_ok = r.randint(85, 100)
    rid = st.add(
        "rapports_mission", axe_id=axe_id, id_auteur=chef_id, statut=S["rapport"][plan],
        contexte=f"Dans le cadre de la mission « {titre} », l'équipe de l'axe {axe_no} ({itin}) est intervenue dans "
                 f"{len(dnames)} districts : {', '.join(dnames)}.",
        justification="Les districts concernés ne disposaient pas d'un accès sécurisé aux applications du "
                      "ministère ; la mission vise à installer, configurer et sécuriser les postes de travail et "
                      "à former les agents locaux.",
        itineraire_reel=" → ".join(["Antananarivo"] + dnames) + ". Le parcours prévu a été respecté"
                        + (", avec un détour de 40 km dû à l'état de la route." if r.random() < 0.4 else "."),
        inventaire_materiel="5 ordinateurs, 2 routeurs, 1 onduleur par district, 1 kit solaire d'appoint, "
                            "200 m de câblage réseau." if full else None,
        configuration_technique="Réseau local segmenté (VLAN administration / agents), accès VPN vers le serveur "
                                "central, comptes nominatifs créés pour chaque agent." if full else None,
        tests_securite="Tests d'authentification, de segmentation réseau et de restauration de sauvegarde "
                       "réalisés ; aucune vulnérabilité critique relevée, deux correctifs mineurs appliqués."
        if full else None,
        nb_participants_formes=r.randint(7, 10) * len(dnames) if full else None,
        profil_participants="Agents administratifs et secrétaires de district" if full else None,
        themes_formation="Bonnes pratiques de sécurité, gestion des mots de passe, utilisation de la plateforme"
        if full else None,
        evaluation_formation="Satisfaction moyenne de 4,2/5 ; les participants demandent une session de rappel."
        if full else None,
        points_forts="Bonne mobilisation des autorités locales ; équipe complète et matériel disponible dès le "
                     "départ." if full else None,
        lecons_apprises="Anticiper les coupures d'électricité et prévoir une marge de deux jours en saison des "
                        "pluies." if full else None,
        bonnes_pratiques="Pré-configuration des postes à Antananarivo avant le départ ; fiche de procédures remise "
                         "à chaque district." if full else None,
        conclusion=f"Les objectifs de l'axe ont été atteints à {n_ok} %." if full else None,
        recommandations="Prévoir une visite de suivi à trois mois et former un référent informatique par "
                        "district." if full else None,
        date_creation=created, date_modification=modif, date_soumission=soum,
        id_validateur=admin_id if valid else None, date_validation=val_date, commentaire_validation=comment)
    for cat, desc, sol in r.sample(DIFFICULTES, 1 if plan == "brouillon" else r.randint(1, 3)):
        st.add("rapport_difficultes", id_rapport=rid, categorie=cat, description=desc, solution=sol)
    return rid


# --------------------------------------------------------------------------------------
# 5) Vérifications, base de données
# --------------------------------------------------------------------------------------
def check(st):
    errs = []
    for (t, col), ref in FK.items():
        for r in st.rows[t]:
            v = r[col]
            if v is not None and v not in st.ids[ref]:
                errs.append(f"clé étrangère invalide : {t}.{col}={v} -> {ref}")
    for t, col in [("utilisateurs", "email"), ("utilisateurs", "matricule"), ("journal_acces", "hash_entree"),
                   ("rapports_mission", "axe_id")]:
        vals = [r[col] for r in st.rows[t]]
        if len(vals) != len(set(vals)):
            errs.append(f"doublon dans {t}.{col}")
    pairs = [(r["equipe_id"], r["id_utilisateur"]) for r in st.rows["participants"]]
    if len(pairs) != len(set(pairs)):
        errs.append("doublon dans participants (equipe_id, id_utilisateur)")
    return errs


def connect(a):
    try:
        import psycopg2 as pg
    except ImportError:
        try:
            import psycopg as pg
        except ImportError:
            sys.exit("Installe un pilote PostgreSQL :  pip install psycopg2-binary")
    pw = os.environ.get("PGPASSWORD") or getpass.getpass(f"Mot de passe de l'utilisateur {a.user} : ")
    return pg.connect(host=a.host, port=a.port, dbname=a.db, user=a.user, password=pw)


def inspect(conn):
    cur = conn.cursor()
    checks = [("utilisateurs", "statut"), ("roles_permissions", "nom_role"), ("roles_permissions", "niveau_acces"),
              ("services_communes", "type"), ("missions", "type_mission"), ("missions", "statut"),
              ("missions_districts", "statut"), ("phases", "statut"), ("journees", "statut"),
              ("equipes", "type_equipe"), ("participants", "fonction"), ("rapports_mission", "statut"),
              ("notifications", "type_notification"), ("demandes_mot_de_passe", "statut"),
              ("ressources_sensibles", "niveau_sensibilite"), ("journal_acces", "type_action"),
              ("scores_anomalie", "methode_utilisee"), ("alertes_securite", "niveau_gravite"),
              ("alertes_securite", "statut"), ("investigations", "statut")]
    for t, c in checks:
        cur.execute(f"SELECT DISTINCT {c} FROM public.{t} WHERE {c} IS NOT NULL ORDER BY 1")
        print(f"{t}.{c:<20} {[r[0] for r in cur.fetchall()]}")
    cur.execute("SELECT DISTINCT left(mot_de_passe_hash, 7) FROM public.utilisateurs")
    print("préfixe des hash de mot de passe :", [r[0] for r in cur.fetchall()])


def hash_password(pw):
    try:
        import bcrypt
        return bcrypt.hashpw(pw.encode(), bcrypt.gensalt(rounds=12)).decode()
    except ImportError:
        try:
            from passlib.hash import bcrypt as pb
            return pb.hash(pw)
        except ImportError:
            sys.exit("Installe bcrypt :  pip install bcrypt")


def summary(st):
    print("\nLignes générées :")
    for t in PK:
        if st.rows[t]:
            print(f"  {t:<26}{len(st.rows[t]):>6}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="vide les tables puis insère la démo")
    ap.add_argument("--inspect", action="store_true", help="affiche les valeurs présentes dans la base")
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=5433)
    ap.add_argument("--db", default="audit_comportemental")
    ap.add_argument("--user", default="postgres")
    a = ap.parse_args()

    if a.inspect:
        conn = connect(a)
        inspect(conn)
        conn.close()
        return

    if not a.apply:  # simulation
        roles = {r: i + 1 for i, r in enumerate(ROLES_NIVEAU)}
        st, U = build(roles, "$2b$12$" + "x" * 53)
        errs = check(st)
        summary(st)
        print("\nCohérence :", "OK" if not errs else "\n  " + "\n  ".join(errs[:20]))
        print("\nSimulation terminée, rien n'a été écrit. Relance avec --apply pour alimenter la base.")
        return

    print(f"ATTENTION : toutes les données de {a.db} (port {a.port}) vont être SUPPRIMÉES puis remplacées.")
    print("Les tables alembic_version et roles_permissions sont conservées.")
    if input("Tape OUI pour continuer : ").strip() != "OUI":
        sys.exit("Annulé.")
    conn = connect(a)
    try:
        cur = conn.cursor()
        cur.execute("SELECT nom_role, id_role FROM public.roles_permissions")
        roles = dict(cur.fetchall())
        for name, niveau in ROLES_NIVEAU.items():
            if name not in roles:
                print(f"  rôle manquant ajouté : {name}")
                cur.execute("INSERT INTO public.roles_permissions (nom_role, niveau_acces) VALUES (%s, %s) "
                            "RETURNING id_role", (name, niveau))
                roles[name] = cur.fetchone()[0]
        st, U = build(roles, hash_password(DEMO_PASSWORD))
        errs = check(st)
        if errs:
            sys.exit("Incohérences détectées, rien n'est écrit :\n  " + "\n  ".join(errs[:20]))
        cur.execute("TRUNCATE TABLE " + ", ".join(f"public.{t}" for t in TO_TRUNCATE) + " RESTART IDENTITY CASCADE")
        for t in PK:
            rows = st.rows[t]
            if not rows:
                continue
            cols = list(rows[0])
            sql = (f"INSERT INTO public.{t} ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))})")
            cur.executemany(sql, [[r[c] for c in cols] for r in rows])
            pk = PK[t]
            cur.execute(f"SELECT setval(pg_get_serial_sequence('public.{t}', '{pk}'), "
                        f"(SELECT COALESCE(MAX({pk}), 1) FROM public.{t}))")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    summary(st)
    print(f"\nTerminé. Mot de passe de tous les comptes : {DEMO_PASSWORD}")
    print("Comptes faciles à retenir :")
    for role, (_, _, local) in DEMO_LOGINS.items():
        print(f"  {role:<26}{local}@mid.gov.mg")
    print("\nLe benchmarking n'est pas pré-rempli : il se calcule depuis le journal.")
    print("Connecte-toi en auditeur ou en administrateur, page Benchmarking, puis")
    print("clôture les trois derniers mois (ou POST /benchmarking/calculer?periode=AAAA-MM).")


if __name__ == "__main__":
    main()
