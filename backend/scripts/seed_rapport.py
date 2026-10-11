"""Crée un rapport de démonstration (brouillon) pré-rempli d'après un vrai rapport.

Usage (depuis le dossier backend, venv activé) :
    python -m scripts.seed_rapport                  # premier chef de mission trouvé
    python -m scripts.seed_rapport adresse@mail.mg  # ou un chef de mission précis

Règles de l'application : seul un chef de mission rédige, et seulement pour un axe
dont il fait partie de l'équipe. Le script les respecte : il choisit l'axe 4 de la
première mission (ou son premier axe) et, si le chef n'est pas encore lié à cet axe,
il l'ajoute comme participant (avec une équipe si l'axe n'en a pas). Il n'a AUCUNE pièce jointe : la liste des pièces
requises s'affiche donc entièrement « manquante », ce qui permet de montrer
le contrôle avant soumission. Ne supprime rien ; relançable (ignore si le
rapport existe déjà).
"""

import sys

import app.models  # noqa: F401  (enregistre tous les modèles)
from app.db.base import SessionLocal, engine
from app.models.identity import Role, Utilisateur
from app.models.missions import Axe, Equipe, Participant
from app.models.rapports import RapportDifficulte, RapportMission

BASE_ATTENDUE = "audit_comportemental"


def main() -> None:
    if engine.url.database != BASE_ATTENDUE:
        sys.exit(f"Refus : la base ciblée est '{engine.url.database}', pas '{BASE_ATTENDUE}'.")

    db = SessionLocal()
    try:
        requete = (
            db.query(Utilisateur)
            .join(Role, Role.id_role == Utilisateur.id_role)
            .filter(Role.nom_role == "chef_mission", Utilisateur.statut == "actif")
        )
        if len(sys.argv) > 1:
            chef = requete.filter(Utilisateur.email == sys.argv[1]).first()
            if chef is None:
                sys.exit(f"{sys.argv[1]} n'est pas un chef de mission actif.")
        else:
            chef = requete.order_by(Utilisateur.id_utilisateur).first()
            if chef is None:
                sys.exit("Aucun chef de mission actif : crée ce compte depuis la page « Comptes ».")
        print(f"Auteur du rapport : {chef.prenom} {chef.nom} ({chef.email})")

        axes = db.query(Axe).order_by(Axe.mission_id, Axe.numero_axe).all()
        if not axes:
            sys.exit("Aucun axe en base : crée une mission et un axe depuis la page Missions.")
        axe = next((a for a in axes if a.numero_axe == 4), axes[0])

        if db.query(RapportMission).filter(RapportMission.axe_id == axe.id).first():
            sys.exit(f"Un rapport existe déjà pour l'axe {axe.id} : rien à faire.")

        # Le chef doit faire partie de l'équipe de l'axe pour pouvoir le rapporter.
        membre = (
            db.query(Participant.id)
            .join(Equipe, Participant.equipe_id == Equipe.id)
            .filter(Equipe.axe_id == axe.id, Participant.id_utilisateur == chef.id_utilisateur)
            .first()
        )
        if membre is None:
            equipe = db.query(Equipe).filter(Equipe.axe_id == axe.id).order_by(Equipe.id).first()
            if equipe is None:
                equipe = Equipe(axe_id=axe.id, type_equipe="Équipe de mission")
                db.add(equipe)
                db.flush()
                print("Équipe créée pour l'axe (il n'en avait pas).")
            db.add(
                Participant(
                    equipe_id=equipe.id,
                    nom=f"{chef.prenom} {chef.nom}",
                    fonction="Chef d'équipe",
                    id_utilisateur=chef.id_utilisateur,
                )
            )
            db.flush()
            print("Compte lié à l'équipe de l'axe (participant ajouté).")

        rapport = RapportMission(
            axe_id=axe.id,
            id_auteur=chef.id_utilisateur,
            itineraire_reel=axe.itineraire_principal
            or "Tana -> Fianarantsoa -> Betroka -> Taolagnaro -> Ambovombe -> Tsihombe -> Beloha -> Bekily -> Betroka -> Fianarantsoa -> Tana",
            contexte=(
                "Dans le cadre de la mise en œuvre du Projet MIONJO, la DSID du MID est chargée "
                "d'assurer le déploiement d'une infrastructure informatique dédiée au niveau des "
                "districts ciblés : installation de serveurs locaux et séance d'information sur le "
                "SII-CSB. La mission vise l'installation, la configuration, la mise en service et la "
                "vérification des serveurs, tout en accompagnant les agents locaux."
            ),
            justification=(
                "- Absence d'infrastructures serveurs pleinement opérationnelles dans les districts ciblés\n"
                "- Difficultés de connectivité et isolement géographique\n"
                "- Capacités techniques encore insuffisantes de certains agents"
            ),
            inventaire_materiel="4 serveurs, 4 onduleurs, 4 routeurs Tenda F3 N300, 4 kits de câblage réseau.",
            configuration_technique=(
                "Mise à jour du système d'exploitation, installation des applications, configuration "
                "du réseau local et des droits d'accès, importation des bases de données."
            ),
            tests_securite="Test de résistance aux micro-coupures, tests de sauvegarde, contrôle des accès administrateurs.",
            nb_participants_formes=22,
            profil_participants="Adjoint chef district, informaticien, responsable ressources",
            themes_formation="Prise en main du serveur, utilisation du logiciel SII CSB, gestion documentaire, application Patrimoine.",
            evaluation_formation="Niveau d'assimilation jugé satisfaisant à l'issue d'exercices pratiques.",
            points_forts="Bonne collaboration avec les responsables et les agents locaux.",
            lecons_apprises="La préparation du matériel et la vérification des conditions techniques sur site sont essentielles.",
            bonnes_pratiques="Tester complètement l'application après chaque installation ou intervention.",
            conclusion=None,  # volontairement vide : le contrôle de complétude le signalera
            recommandations=(
                "Effectuer régulièrement des sauvegardes des données du serveur\n"
                "Prévoir une maintenance préventive du serveur"
            ),
            difficultes=[
                RapportDifficulte(
                    categorie="Électricité",
                    description="Coupures brèves et répétées du réseau électrique local pendant l'installation et la formation.",
                    solution="Mise en place d'un onduleur renforcé.",
                ),
                RapportDifficulte(
                    categorie="Logiciel",
                    description="Problèmes de permissions sur Ubuntu bloquant certaines fonctionnalités.",
                    solution="Vérification et correction des permissions des fichiers et dossiers.",
                ),
            ],
        )
        db.add(rapport)
        db.commit()
        print(f"Rapport de démonstration créé pour l'axe {axe.id} (id {rapport.id}), statut brouillon.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()