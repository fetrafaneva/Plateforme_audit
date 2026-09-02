from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.analytics import construire_profil, detecter_anomalie
from app.db.base import get_db
from app.models.identity import Utilisateur
from app.schemas.analyse import ProfilOut, ScoreOut

router = APIRouter(prefix="/analyse", tags=["analyse comportementale"])


@router.post("/profils/{id_utilisateur}", response_model=ProfilOut, status_code=201)
def calculer_profil(
    id_utilisateur: int,
    periode_reference: str = "2026-08",
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return construire_profil(db, id_utilisateur, periode_reference)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/detecter/{id_entree_journal}", response_model=ScoreOut, status_code=201)
def calculer_score(
    id_entree_journal: int,
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return detecter_anomalie(db, id_entree_journal)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))