"""Jeu de données de démonstration pour le module d'audit.

Usage (depuis backend\\, venv activé) :
    python -m scripts.seed_audit

Ce que fait le script :
  1. efface les tables du module d'audit (journal, profils, scores, alertes,
     investigations, politiques, ressources) et seulement elles ;
  2. crée 5 ressources sensibles et une politique de conformité ;
  3. génère des accès réalistes (jours ouvrés, 8h-16h heure de Madagascar) pour
     les comptes de démo, avec UN jour anormal par compte (volume très élevé) ;
  4. écrit ces accès dans le journal avec la VRAIE fonction compute_hash, donc
     la chaîne est valide ;
  5. construit les profils et calcule les scores avec TES fonctions
     (construire_profil, detecter_anomalie), puis crée les alertes avec
     evaluer_alerte ;
  6. ouvre une investigation et en clôture une autre (textes fictifs).

Les comptes viennent de seed_demo.py : lance-le d'abord si la base est vide.
Les volumes, adresses IP et conclusions d'enquête sont inventés.
"""

import json
import random
import sys
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import text

import app.models  # noqa: F401  (enregistre tous les modèles)
from app.api.journal import verifier_integrite
from app.core.alertes import evaluer_alerte
from app.core.analytics import construire_profil, detecter_anomalie
from app.core.chaining import GENESIS_HASH, compute_hash
from app.db.base import SessionLocal, engine
from app.models.audit import JournalAcces
from app.models.identity import ServiceCommune, Utilisateur
from app.models.ressources import RessourceSensible
from app.models.securite import Investigation, PolitiqueConformite

BASE_ATTENDUE = "audit_comportemental"
MADA = timezone(timedelta(hours=3))  # heure de Madagascar
NB_JOURS = 24  # fenêtre en jours calendaires (les week-ends sont ignorés)

TABLES_AUDIT = [
    "investigations",
    "alertes_securite",
    "scores_anomalie",
    "profils_comportementaux",
    "journal_acces",
    "politiques_conformite",
    "ressources_sensibles",
]

RESSOURCES = [
    ("Registre d'état civil", "eleve"),
    ("Dossiers d'identité", "eleve"),
    ("Fichier du personnel", "eleve"),
    ("Registre foncier", "moyen"),
    ("Statistiques communales", "faible"),
]

SEUILS = {"seuil_alerte": 3.0, "seuil_moyen": 4.5, "seuil_critique": 6.0}

# volume : accès par jour normal ; ressources : indices dans RESSOURCES ;
# pic : un jour anormal (jours_avant = position depuis la fin des jours ouvrés)
COMPORTEMENTS = {
    "agent@test.mg": {
        "volume": (3, 5),
        "ressources": [0, 1],
        "ip": "192.168.10.21",
        "pic": {"jours_avant": 4, "volume": 28, "heures": (3, 7), "ip": "10.99.3.7"},
    },
    "tech@test.mg": {
        "volume": (3, 5),
        "ressources": [3, 4],
        "ip": "192.168.10.34",
        "pic": {"jours_avant": 3, "volume": 9, "heures": (9, 15), "ip": "192.168.10.34"},
    },
    "chef@test.mg": {
        "volume": (3, 5),
        "ressources": [2, 3],
        "ip": "192.168.10.8",
        "pic": {"jours_avant": 8, "volume": 8, "heures": (9, 15), "ip": "192.168.10.8"},
    },
    "responsable@test.mg": {
        "volume": (3, 5),
        "ressources": [0, 4],
        "ip": "192.168.10.3",
        "pic": {"jours_avant": 6, "volume": 7, "heures": (9, 15), "ip": "192.168.10.3"},
    },
}


def jours_ouvres() -> list[date]:
    aujourd_hui = date.today()
    jours = [aujourd_hui - timedelta(days=k) for k in range(NB_JOURS, 0, -1)]
    return [j for j in jours if j.weekday() < 5]


def generer_entrees(utilisateurs, ressources_ids, jours):
    entrees = []
    for email, cfg in COMPORTEMENTS.items():
        user = utilisateurs.get(email)
        if user is None:
            print(f"  (compte {email} introuvable, ignoré)")
            continue

        pic = cfg["pic"]
        for i, jour in enumerate(jours):
            est_pic = i == len(jours) - pic["jours_avant"]
            if est_pic:
                nombre = pic["volume"]
                h_min, h_max = pic["heures"]
                poids_actions = [30, 20, 50]  # beaucoup d'exports
                ip = pic["ip"]
            else:
                nombre = random.randint(*cfg["volume"])
                h_min, h_max = 8, 16
                poids_actions = [85, 13, 2]
                ip = cfg["ip"]

            for _ in range(nombre):
                local = datetime(
                    jour.year, jour.month, jour.day,
                    random.randint(h_min, h_max),
                    random.randint(0, 59),
                    random.randint(0, 59),
                    random.randint(0, 999999),
                    tzinfo=MADA,
                )
                if est_pic:
                    id_ressource = random.choice(ressources_ids)  # périmètre inhabituel
                else:
                    id_ressource = ressources_ids[random.choice(cfg["ressources"])]
                entrees.append(
                    {
                        "id_utilisateur": user.id_utilisateur,
                        "id_ressource": id_ressource,
                        "type_action": random.choices(
                            ["consultation", "modification", "export"], weights=poids_actions
                        )[0],
                        "horodatage": local.astimezone(timezone.utc),
                        "adresse_ip": ip,
                    }
                )
    entrees.sort(key=lambda e: e["horodatage"])
    return entrees


def main() -> None:
    if engine.url.database != BASE_ATTENDUE:
        sys.exit(
            f"Refus : la base ciblée est '{engine.url.database}', "
            f"pas '{BASE_ATTENDUE}'. Vérifie DATABASE_URL dans .env."
        )

    print(f"Base ciblée : {engine.url.database} (port {engine.url.port})")
    print("Ce script EFFACE le module d'audit : journal, profils, scores, alertes,")
    print("investigations, politiques et ressources. Les missions et les comptes")
    print("ne sont pas touchés.")
    if input("Tape OUI pour continuer : ").strip() != "OUI":
        sys.exit("Annulé.")

    random.seed(2026)
    db = SessionLocal()
    try:
        utilisateurs = {u.email: u for u in db.query(Utilisateur).all()}
        service = db.query(ServiceCommune).order_by(ServiceCommune.id_service).first()
        if service is None or not utilisateurs:
            sys.exit("Aucun compte ni service en base : lance d'abord seed_demo.py.")

        jours = jours_ouvres()

        # --- 1. Effacement + ressources + politique + journal (une transaction) ---
        db.execute(text("TRUNCATE TABLE " + ", ".join(TABLES_AUDIT) + " RESTART IDENTITY CASCADE"))

        ressources = [
            RessourceSensible(
                type_ressource=nom,
                niveau_sensibilite=niveau,
                id_service_proprietaire=service.id_service,
            )
            for nom, niveau in RESSOURCES
        ]
        db.add_all(ressources)
        db.add(
            PolitiqueConformite(
                nom_politique="Seuils d'anomalie du volume journalier",
                description="Alerte si le z-score du volume journalier dépasse les seuils configurés.",
                seuils_configures=json.dumps(SEUILS),
            )
        )
        db.flush()
        ressources_ids = [r.id_ressource for r in ressources]

        entrees = generer_entrees(utilisateurs, ressources_ids, jours)
        hash_precedent = GENESIS_HASH
        for e in entrees:
            hash_entree = compute_hash(
                id_utilisateur=e["id_utilisateur"],
                id_ressource=e["id_ressource"],
                type_action=e["type_action"],
                horodatage=e["horodatage"],
                hash_precedent=hash_precedent,
            )
            db.add(JournalAcces(**e, hash_entree=hash_entree, hash_precedent=hash_precedent))
            db.flush()  # garde l'ordre d'insertion = ordre de la chaîne
            hash_precedent = hash_entree
        db.commit()
        print(f"\n{len(entrees)} entrées de journal écrites.")

        verification = verifier_integrite(db)
        print(
            f"Vérification de la chaîne : intact={verification.intact}, "
            f"{verification.nb_entrees_verifiees} entrées vérifiées."
        )
        if not verification.intact:
            print("  ATTENTION : la chaîne est signalée corrompue (voir la note sur chaining.py).")

        # --- 2. Profils, scores, alertes (chaque appel valide sa propre transaction) ---
        periode = date.today().strftime("%Y-%m")
        ids_actifs = sorted({e["id_utilisateur"] for e in entrees})
        for id_utilisateur in ids_actifs:
            construire_profil(db, id_utilisateur, periode)
        print(f"{len(ids_actifs)} profils construits.")

        alertes = []
        nb_scores = 0
        for id_utilisateur in ids_actifs:
            lignes = (
                db.query(JournalAcces)
                .filter(JournalAcces.id_utilisateur == id_utilisateur)
                .order_by(JournalAcces.id_entree)
                .all()
            )
            derniere_par_jour = {}
            for ligne in lignes:
                derniere_par_jour[ligne.horodatage.date()] = ligne  # la dernière du jour

            for jour in sorted(derniere_par_jour)[-10:]:
                entree = derniere_par_jour[jour]
                try:
                    score = detecter_anomalie(db, entree.id_entree)
                except ValueError as erreur:
                    print(f"  score impossible pour l'entrée {entree.id_entree} : {erreur}")
                    continue
                nb_scores += 1
                alerte = evaluer_alerte(db, score)
                if alerte is not None:
                    alertes.append((alerte, score, jour))

        print(f"{nb_scores} scores calculés, {len(alertes)} alertes créées :")
        email_par_id = {u.id_utilisateur: email for email, u in utilisateurs.items()}
        for alerte, score, jour in sorted(alertes, key=lambda t: -abs(t[1].z_score)):
            entree = db.get(JournalAcces, score.id_entree_journal)
            print(
                f"  {alerte.niveau_gravite:9s} z={score.z_score:6.1f}  {jour}  "
                f"{email_par_id.get(entree.id_utilisateur)}"
            )

        # --- 3. Deux investigations d'exemple ---
        auditeur = utilisateurs.get("auditeur@test.mg")
        if auditeur is not None and alertes:
            classees = sorted(alertes, key=lambda t: -abs(t[1].z_score))

            a_ouvrir = classees[0][0]
            db.add(Investigation(id_alerte=a_ouvrir.id_alerte, id_enqueteur=auditeur.id_utilisateur))
            a_ouvrir.statut = "en_investigation"

            if len(classees) >= 3:
                a_fermer = classees[-1][0]
                db.add(
                    Investigation(
                        id_alerte=a_fermer.id_alerte,
                        id_enqueteur=auditeur.id_utilisateur,
                        statut="cloturee",
                        conclusion=(
                            "Pic d'accès lié à une opération de mise à jour des dossiers, "
                            "confirmé par le chef de service. Aucune action nécessaire."
                        ),
                        date_cloture=datetime.now(timezone.utc),
                    )
                )
                a_fermer.statut = "traitee"
            db.commit()
            print("Investigations d'exemple créées (1 ouverte, 1 clôturée si assez d'alertes).")
        elif auditeur is None:
            print("Compte auditeur@test.mg introuvable : aucune investigation créée.")

        print("\nTerminé. Mot de passe des comptes de démo : voir seed_demo.py.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()