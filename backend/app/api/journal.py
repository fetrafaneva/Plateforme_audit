from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import asc, text
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.core.chaining import GENESIS_HASH, compute_hash
from app.db.base import get_db
from app.models.audit import JournalAcces
from app.models.identity import Utilisateur
from app.schemas.journal import JournalEntryCreate, JournalEntryOut, VerificationResult

router = APIRouter(prefix="/journal", tags=["journal d'accès"])

# Clé du verrou PostgreSQL qui sérialise l'écriture dans le journal.
# N'importe quel entier convient, tant qu'il est le même pour toutes les écritures.
VERROU_CHAINE = 7001


@router.post("/acces", response_model=JournalEntryOut, status_code=201)
def enregistrer_acces(
    payload: JournalEntryCreate,
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Une seule écriture à la fois peut lire « la dernière entrée » et s'y chaîner.
    # Sans ce verrou, deux requêtes simultanées se chaîneraient à la même entrée
    # précédente et la chaîne se diviserait. Le verrou est relâché au commit.
    db.execute(text(f"SELECT pg_advisory_xact_lock({VERROU_CHAINE})"))

    derniere_entree = (
        db.query(JournalAcces).order_by(JournalAcces.id_entree.desc()).first()
    )
    hash_precedent = derniere_entree.hash_entree if derniere_entree else GENESIS_HASH
    horodatage = datetime.now(timezone.utc)

    hash_entree = compute_hash(
        id_utilisateur=current_user.id_utilisateur,
        id_ressource=payload.id_ressource,
        type_action=payload.type_action,
        horodatage=horodatage,
        hash_precedent=hash_precedent,
    )

    entree = JournalAcces(
        id_utilisateur=current_user.id_utilisateur,
        id_ressource=payload.id_ressource,
        type_action=payload.type_action,
        horodatage=horodatage,
        adresse_ip=payload.adresse_ip,
        hash_entree=hash_entree,
        hash_precedent=hash_precedent,
    )
    db.add(entree)
    db.commit()
    db.refresh(entree)
    return entree


@router.get(
    "/verify",
    response_model=VerificationResult,
    dependencies=[Depends(require_role("auditeur", "administrateur"))],
)
def verifier_integrite(db: Session = Depends(get_db)):
    """Rejoue toute la chaîne depuis le début et recalcule chaque hash.
    Si une seule entrée a été modifiée après coup, le hash recalculé ne
    correspondra plus au hash stocké (ou au hash_precedent attendu par
    l'entrée suivante), et la vérification échoue à partir de ce point.
    """
    entrees = db.query(JournalAcces).order_by(asc(JournalAcces.id_entree)).all()

    hash_attendu = GENESIS_HASH
    for i, entree in enumerate(entrees, start=1):
        if entree.hash_precedent != hash_attendu:
            return VerificationResult(
                intact=False, nb_entrees_verifiees=i, premiere_entree_corrompue=entree.id_entree
            )

        hash_recalcule = compute_hash(
            id_utilisateur=entree.id_utilisateur,
            id_ressource=entree.id_ressource,
            type_action=entree.type_action,
            horodatage=entree.horodatage,
            hash_precedent=entree.hash_precedent,
        )
        if hash_recalcule != entree.hash_entree:
            return VerificationResult(
                intact=False, nb_entrees_verifiees=i, premiere_entree_corrompue=entree.id_entree
            )

        hash_attendu = entree.hash_entree

    return VerificationResult(intact=True, nb_entrees_verifiees=len(entrees))