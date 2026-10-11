"""Écriture dans le journal d'accès chaîné, réutilisable par tous les modules.

`ajouter_entree` ne valide pas la transaction : c'est l'appelant qui fait
`db.commit()`. Le verrou PostgreSQL pris ici reste donc tenu jusqu'au commit,
ce qui empêche deux écritures simultanées de se chaîner à la même entrée.
"""

from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.chaining import GENESIS_HASH, compute_hash
from app.models.audit import JournalAcces
from app.models.ressources import RessourceSensible

VERROU_CHAINE = 7001


def ajouter_entree(
    db: Session,
    id_utilisateur: int,
    id_ressource: int,
    type_action: str,
    adresse_ip: str,
) -> JournalAcces:
    db.execute(text(f"SELECT pg_advisory_xact_lock({VERROU_CHAINE})"))

    derniere_entree = (
        db.query(JournalAcces).order_by(JournalAcces.id_entree.desc()).first()
    )
    hash_precedent = derniere_entree.hash_entree if derniere_entree else GENESIS_HASH
    horodatage = datetime.now(timezone.utc)

    hash_entree = compute_hash(
        id_utilisateur=id_utilisateur,
        id_ressource=id_ressource,
        type_action=type_action,
        horodatage=horodatage,
        hash_precedent=hash_precedent,
    )
    entree = JournalAcces(
        id_utilisateur=id_utilisateur,
        id_ressource=id_ressource,
        type_action=type_action,
        horodatage=horodatage,
        adresse_ip=adresse_ip,
        hash_entree=hash_entree,
        hash_precedent=hash_precedent,
    )
    db.add(entree)
    db.flush()  # la session n'a pas d'autoflush : les requêtes suivantes verront l'entrée
    return entree


def obtenir_id_ressource(
    db: Session, type_ressource: str, niveau_sensibilite: str, id_service: int
) -> int:
    """Retrouve (ou crée) la ressource sensible correspondant à un type de données."""
    ressource = (
        db.query(RessourceSensible)
        .filter(RessourceSensible.type_ressource == type_ressource)
        .first()
    )
    if ressource is None:
        ressource = RessourceSensible(
            type_ressource=type_ressource,
            niveau_sensibilite=niveau_sensibilite,
            id_service_proprietaire=id_service,
        )
        db.add(ressource)
        db.flush()
    return ressource.id_ressource