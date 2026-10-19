from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_role
from app.core.connexion import effacer_echecs, emails_bloques, normaliser_email
from app.db.base import get_db
from app.models.identity import Role, ServiceCommune, Utilisateur
from app.schemas.utilisateurs import (
    CompteOut,
    RoleOut,
    ServiceOut,
    StatutCompteUpdate,
    UtilisateurResume,
)

router = APIRouter(prefix="/utilisateurs", tags=["utilisateurs"])

ADMIN_SEUL = [Depends(require_role("administrateur"))]


def _compte_out(u: Utilisateur, bloque: bool = False) -> CompteOut:
    return CompteOut(
        id_utilisateur=u.id_utilisateur,
        nom=u.nom,
        prenom=u.prenom,
        email=u.email,
        matricule=u.matricule,
        role=u.role.nom_role,
        service=u.service.nom_service,
        statut=u.statut,
        bloque=bloque,
    )


# ---------- Choix d'un compte (liaison avec un participant de mission) ----------


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


# ---------- Gestion des comptes (administrateur) ----------


@router.get("/gestion", response_model=list[CompteOut], dependencies=ADMIN_SEUL)
def lister_comptes(db: Session = Depends(get_db)):
    """Tous les comptes, actifs ou non."""
    comptes = (
        db.query(Utilisateur)
        .options(joinedload(Utilisateur.role), joinedload(Utilisateur.service))
        .order_by(Utilisateur.nom, Utilisateur.prenom)
        .all()
    )
    bloques = emails_bloques(db)
    return [_compte_out(u, normaliser_email(u.email) in bloques) for u in comptes]


@router.get("/roles", response_model=list[RoleOut], dependencies=ADMIN_SEUL)
def lister_roles(db: Session = Depends(get_db)):
    return db.query(Role).order_by(Role.nom_role).all()


@router.get("/services", response_model=list[ServiceOut], dependencies=ADMIN_SEUL)
def lister_services(db: Session = Depends(get_db)):
    return db.query(ServiceCommune).order_by(ServiceCommune.nom_service).all()


@router.patch("/{id_utilisateur}/statut", response_model=CompteOut, dependencies=ADMIN_SEUL)
def modifier_statut(
    id_utilisateur: int,
    payload: StatutCompteUpdate,
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    utilisateur = db.get(Utilisateur, id_utilisateur)
    if utilisateur is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if utilisateur.id_utilisateur == current_user.id_utilisateur and payload.statut != "actif":
        raise HTTPException(status_code=400, detail="Tu ne peux pas désactiver ton propre compte")

    utilisateur.statut = payload.statut
    db.commit()
    db.refresh(utilisateur)
    return _compte_out(utilisateur)


@router.post("/{id_utilisateur}/debloquer", response_model=CompteOut, dependencies=ADMIN_SEUL)
def debloquer_compte(id_utilisateur: int, db: Session = Depends(get_db)):
    """Remet à zéro les échecs de connexion d'un compte bloqué."""
    utilisateur = db.get(Utilisateur, id_utilisateur)
    if utilisateur is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    effacer_echecs(db, normaliser_email(utilisateur.email))
    db.commit()
    return _compte_out(utilisateur)