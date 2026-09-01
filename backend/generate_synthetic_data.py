"""Génère un historique d'accès simulé pour un utilisateur, sur plusieurs
jours, avec une journée anormale injectée (pic de volume) — sert de jeu
de test pour la construction du profil comportemental et la détection
d'anomalies (chapitre 9.3 du mémoire).

Usage : python generate_synthetic_data.py
"""

import random
from datetime import datetime, timedelta, timezone

import numpy as np

from app import models  # noqa: F401 — enregistre les modèles sur Base
from app.core.chaining import GENESIS_HASH, compute_hash
from app.db.base import SessionLocal
from app.models.audit import JournalAcces
from app.models.identity import Utilisateur
from app.models.ressources import RessourceSensible

ID_UTILISATEUR_CIBLE = 1 # adapte à l'id de ton utilisateur de test
NB_JOURS_HISTORIQUE = 20
VOLUME_MOYEN_NORMAL = 5  # accès/jour en moyenne, comportement normal
JOUR_ANOMALIE = 5  # J-5 : journée avec un pic de volume anormal


def generer():
    db = SessionLocal()
    try:
        utilisateur = db.get(Utilisateur, ID_UTILISATEUR_CIBLE)
        if utilisateur is None:
            raise SystemExit(f"Utilisateur {ID_UTILISATEUR_CIBLE} introuvable.")

        ressources = db.query(RessourceSensible).all()
        if not ressources:
            raise SystemExit("Aucune ressource sensible en base — lance seed_data.py d'abord.")

        derniere_entree = (
            db.query(JournalAcces).order_by(JournalAcces.id_entree.desc()).first()
        )
        hash_precedent = derniere_entree.hash_entree if derniere_entree else GENESIS_HASH

        aujourdhui = datetime.now(timezone.utc).date()
        nb_inserees = 0

        for jour_offset in range(NB_JOURS_HISTORIQUE, 0, -1):
            jour = aujourdhui - timedelta(days=jour_offset)

            if jour_offset == JOUR_ANOMALIE:
                volume_jour = VOLUME_MOYEN_NORMAL * 6  # pic anormal volontaire
            else:
                volume_jour = max(0, int(np.random.poisson(VOLUME_MOYEN_NORMAL)))

            for _ in range(volume_jour):
                heure = random.randint(8, 17)
                horodatage = datetime(
                    jour.year,
                    jour.month,
                    jour.day,
                    heure,
                    random.randint(0, 59),
                    tzinfo=timezone.utc,
                )
                ressource = random.choice(ressources)
                type_action = random.choice(
                    ["consultation", "consultation", "consultation", "export"]
                )

                hash_entree = compute_hash(
                    id_utilisateur=ID_UTILISATEUR_CIBLE,
                    id_ressource=ressource.id_ressource,
                    type_action=type_action,
                    horodatage=horodatage,
                    hash_precedent=hash_precedent,
                )

                db.add(
                    JournalAcces(
                        id_utilisateur=ID_UTILISATEUR_CIBLE,
                        id_ressource=ressource.id_ressource,
                        type_action=type_action,
                        horodatage=horodatage,
                        adresse_ip="127.0.0.1",
                        hash_entree=hash_entree,
                        hash_precedent=hash_precedent,
                    )
                )
                db.flush()
                hash_precedent = hash_entree
                nb_inserees += 1

        db.commit()
        print(f"{nb_inserees} entrées générées sur {NB_JOURS_HISTORIQUE} jours.")
        print(f"Jour J-{JOUR_ANOMALIE} : pic de volume anormal injecté "
              f"({VOLUME_MOYEN_NORMAL * 6} accès contre ~{VOLUME_MOYEN_NORMAL} en moyenne).")
    finally:
        db.close()


if __name__ == "__main__":
    generer()