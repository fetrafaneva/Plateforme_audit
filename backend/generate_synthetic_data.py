"""Génère un historique d'accès simulé pour un utilisateur, sur plusieurs
jours, avec plusieurs journées anormales injectées à des intensités
différentes — des cas évidents (x8) aux cas limites (x1.5) — pour évaluer
la sensibilité réelle de la détection (chapitre 9.3-9.4 du mémoire).

Usage : python generate_synthetic_data.py
IMPORTANT : si tu relances ce script, vide d'abord les tables
journal_acces / profils_comportementaux / scores_anomalie (TRUNCATE) pour
éviter de mélanger plusieurs générations sur les mêmes dates.
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

ID_UTILISATEUR_CIBLE = 1  # adapte à l'id de ton utilisateur de test
NB_JOURS_HISTORIQUE = 20
VOLUME_MOYEN_NORMAL = 5  # accès/jour en moyenne, comportement normal

# Jours anormaux injectés, avec un multiplicateur de volume différent
# chacun — des cas limites (x1.5, x2) aux cas évidents (x8), pour tester
# la sensibilité réelle de la détection plutôt qu'un seul gros pic facile.
# Doit être répété à l'identique dans evaluer_detection.py.
JOURS_ANOMALIE = {
    19: 1.5,  # J-19 : anomalie très légère, cas limite
    11: 2,    # J-11 : anomalie légère
    15: 3,    # J-15 : sur-volume modéré
    8: 5,     # J-8  : sur-volume net
    3: 8,     # J-3  : pic fort, cas évident
}


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

            if jour_offset in JOURS_ANOMALIE:
                volume_jour = max(0, round(VOLUME_MOYEN_NORMAL * JOURS_ANOMALIE[jour_offset]))
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
        print("Jours anormaux injectés :")
        for offset, mult in sorted(JOURS_ANOMALIE.items(), reverse=True):
            volume = round(VOLUME_MOYEN_NORMAL * mult)
            print(f"  J-{offset} : x{mult} ({volume} accès contre ~{VOLUME_MOYEN_NORMAL} en moyenne)")
    finally:
        db.close()


if __name__ == "__main__":
    generer()