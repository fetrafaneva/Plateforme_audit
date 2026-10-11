"""Crée un rapport de démonstration (brouillon) pré-rempli d'après un vrai rapport.

Usage (depuis le dossier backend, venv activé) :
    python -m scripts.seed_rapport

Le rapport est créé au nom de chef@test.mg pour l'axe 4 de la première mission
(ou son premier axe). Il n'a AUCUNE pièce jointe : la liste des pièces
requises s'affiche donc entièrement « manquante », ce qui permet de montrer
le contrôle avant soumission. Ne supprime rien ; relançable (ignore si le
rapport existe déjà).
"""

import sys

import app.models  # noqa: F401  (enregistre tous les modèles)
from app.db.base import SessionLocal, engine
from app.models.identity import Utilisateur
from app.models.missions import Axe
from app.models.rapports import RapportDifficulte, RapportMission

BASE_ATTENDUE = "audit_comportemental"


def main() -> None:
    if engine.url.database != BASE_ATTENDUE:
        sys.exit(f"Refus : la base ciblée est '{engine.url.database}', pas '{BASE_ATTENDUE}'.")

    db = SessionLocal()
    try:
        chef = db.query(Utilisateur).filter(Utilisateur.email == "chef@test.mg").first()
        if chef is None:
            sys.exit("Compte chef@test.mg introuvable : lance d'abord seed_demo.py.")

        axes = db.query(Axe).order_by(Axe.mission_id, Axe.numero_axe).all()
        if not axes:
            sys.exit("Aucun axe en base : lance d'abord seed_demo.py.")
        axe = next((a for a in axes if a.numero_axe == 4), axes[0])

        if db.query(RapportMission).filter(RapportMission.axe_id == axe.id).first():
            sys.exit(f"Un rapport existe déjà pour l'axe {axe.id} : rien à faire.")

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