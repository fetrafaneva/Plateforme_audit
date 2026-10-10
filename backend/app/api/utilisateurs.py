from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_role
from app.db.base import get_db
from app.models.identity import Utilisateur
from app.schemas.utilisateurs import UtilisateurResume

router = APIRouter(prefix="/utilisateurs", tags=["utilisateurs"])


@router.get(
    "/",
    response_model=list[UtilisateurResume],
    dependencies=[Depends(require_role("chef_mission", "administrateur", "auditeur"))],
)
def lister_utilisateurs(db: Session = Depends(get_db)):
    """Comptes actifs, pour pouvoir les lier à un participant de mission."""
    utilisateurs = (
        db.query(Utilisateur)
        .options(joinedload(Utilisateur.role))
        .filter(Utilisateur.statut == "actif")
        .order_by(Utilisateur.nom, Utilisateur.prenom)
        .all()
    )
    return [
        UtilisateurResume(
            id_utilisateur=u.id_utilisateur,
            nom=u.nom,
            prenom=u.prenom,
            matricule=u.matricule,
            role=u.role.nom_role,
        )
        for u in utilisateurs
    ]