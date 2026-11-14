"""Demandes de nouveau mot de passe, traitées par un administrateur.

Aucun utilisateur ne change lui-même son mot de passe. Il envoie une demande (depuis la
page de connexion s'il est bloqué, ou depuis « Mon compte » s'il est connecté) ; les
administrateurs sont notifiés ; l'un d'eux vérifie l'identité de la personne, génère un
mot de passe temporaire (affiché une seule fois) et le lui communique de vive voix.

Un administrateur ne traite pas sa propre demande : un autre administrateur le fait. Si
un seul administrateur existe, il utilise `python -m scripts.reinitialiser_mdp`.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_role
from app.core.connexion import effacer_echecs, normaliser_email
from app.core.journal import ajouter_entree, obtenir_id_ressource
from app.core.mots_de_passe import generer_mot_de_passe
from app.core.notifications import notifier, notifier_administrateurs
from app.core.reseau import ip_du_client
from app.core.security import hash_password
from app.db.base import get_db
from app.models.connexion import DemandeMotDePasse
from app.models.identity import Utilisateur
from app.schemas.demandes_mdp import (
    AccuseOut,
    DemandeMoiIn,
    DemandeOut,
    DemandePubliqueIn,
    MotDePasseTemporaireOut,
)

router = APIRouter(prefix="/demandes-mot-de-passe", tags=["mots de passe"])

MESSAGE_ACCUSE = (
    "Si ces informations correspondent à un compte actif, l'administrateur a été prévenu. "
    "Il te communiquera un nouveau mot de passe."
)
RESSOURCE_COMPTES = "Comptes utilisateurs"


def _nom(u: Utilisateur) -> str:
    return f"{u.prenom} {u.nom}"


def _demande_out(d: DemandeMotDePasse) -> DemandeOut:
    return DemandeOut(
        id=d.id,
        id_utilisateur=d.id_utilisateur,
        nom_utilisateur=_nom(d.utilisateur),
        email=d.utilisateur.email,
        matricule=d.utilisateur.matricule,
        role=d.utilisateur.role.nom_role,
        motif=d.motif,
        statut=d.statut,
        date_demande=d.date_demande,
        nom_traitant=_nom(d.traitant) if d.traitant else None,
        date_traitement=d.date_traitement,
    )


def _requete(db: Session):
    return db.query(DemandeMotDePasse).options(
        joinedload(DemandeMotDePasse.utilisateur).joinedload(Utilisateur.role),
        joinedload(DemandeMotDePasse.traitant),
    )


def _creer_demande(db: Session, utilisateur: Utilisateur, motif: str | None) -> bool:
    """Crée la demande et prévient les administrateurs. False s'il y en a déjà une en attente."""
    deja = (
        db.query(DemandeMotDePasse)
        .filter(
            DemandeMotDePasse.id_utilisateur == utilisateur.id_utilisateur,
            DemandeMotDePasse.statut == "en_attente",
        )
        .first()
    )
    if deja is not None:
        return False
    db.add(
        DemandeMotDePasse(
            id_utilisateur=utilisateur.id_utilisateur,
            motif=(motif or "").strip() or None,
        )
    )
    notifier_administrateurs(
        db,
        "demande_mot_de_passe",
        f"{_nom(utilisateur)} demande un nouveau mot de passe.",
        "/admin/utilisateurs",
        sauf=utilisateur.id_utilisateur,
    )
    db.commit()
    return True


# ---------- Côté utilisateur ----------


@router.post("/", response_model=AccuseOut, status_code=202)
def demander_sans_connexion(payload: DemandePubliqueIn, db: Session = Depends(get_db)):
    """Pour quelqu'un qui ne peut plus se connecter.

    L'adresse et le matricule doivent correspondre à un compte actif. La réponse est
    toujours la même, que le compte existe ou non : elle ne permet pas de deviner quelles
    adresses sont valides.
    """
    utilisateur = (
        db.query(Utilisateur)
        .filter(
            func.lower(Utilisateur.email) == normaliser_email(payload.email),
            Utilisateur.matricule == payload.matricule.strip(),
            Utilisateur.statut == "actif",
        )
        .first()
    )
    if utilisateur is not None:
        _creer_demande(db, utilisateur, payload.motif)
    return AccuseOut(message=MESSAGE_ACCUSE)


@router.get("/moi", response_model=DemandeOut | None)
def ma_derniere_demande(
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    demande = (
        _requete(db)
        .filter(DemandeMotDePasse.id_utilisateur == current_user.id_utilisateur)
        .order_by(DemandeMotDePasse.id.desc())
        .first()
    )
    return _demande_out(demande) if demande else None


@router.post("/moi", response_model=AccuseOut, status_code=201)
def demander_connecte(
    payload: DemandeMoiIn,
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not _creer_demande(db, current_user, payload.motif):
        raise HTTPException(status_code=400, detail="Une demande est déjà en attente de traitement")
    return AccuseOut(message="Demande envoyée : l'administrateur a été prévenu.")


# ---------- Côté administrateur ----------


@router.get(
    "/",
    response_model=list[DemandeOut],
    dependencies=[Depends(require_role("administrateur"))],
)
def lister_demandes(statut: str = "en_attente", db: Session = Depends(get_db)):
    demandes = (
        _requete(db)
        .filter(DemandeMotDePasse.statut == statut)
        .order_by(DemandeMotDePasse.date_demande)
        .all()
    )
    return [_demande_out(d) for d in demandes]


def _demande_en_attente(db: Session, id_demande: int, admin: Utilisateur) -> DemandeMotDePasse:
    demande = _requete(db).filter(DemandeMotDePasse.id == id_demande).first()
    if demande is None:
        raise HTTPException(status_code=404, detail="Demande introuvable")
    if demande.statut != "en_attente":
        raise HTTPException(status_code=400, detail="Cette demande a déjà été traitée")
    if demande.id_utilisateur == admin.id_utilisateur:
        raise HTTPException(
            status_code=400,
            detail="Un autre administrateur doit traiter ta propre demande",
        )
    return demande


@router.post(
    "/{id_demande}/traiter",
    response_model=MotDePasseTemporaireOut,
    dependencies=[Depends(require_role("administrateur"))],
)
def traiter_demande(
    id_demande: int,
    request: Request,
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Génère un mot de passe temporaire, l'enregistre (haché) et le renvoie UNE seule fois."""
    demande = _demande_en_attente(db, id_demande, current_user)
    utilisateur = demande.utilisateur

    mot_de_passe = generer_mot_de_passe()
    utilisateur.mot_de_passe_hash = hash_password(mot_de_passe)
    effacer_echecs(db, normaliser_email(utilisateur.email))  # le compte est aussi débloqué

    demande.statut = "traitee"
    demande.id_traitant = current_user.id_utilisateur
    demande.date_traitement = datetime.now(timezone.utc)

    notifier(
        db,
        utilisateur.id_utilisateur,
        "mot_de_passe_reinitialise",
        "Ton mot de passe a été réinitialisé par l'administrateur, qui te l'a communiqué directement.",
        None,
    )
    id_ressource = obtenir_id_ressource(db, RESSOURCE_COMPTES, "eleve", current_user.id_service)
    ajouter_entree(
        db,
        current_user.id_utilisateur,
        id_ressource,
        "modification",
        ip_du_client(request),
    )
    db.commit()
    return MotDePasseTemporaireOut(mot_de_passe_temporaire=mot_de_passe)


@router.post(
    "/{id_demande}/rejeter",
    response_model=AccuseOut,
    dependencies=[Depends(require_role("administrateur"))],
)
def rejeter_demande(
    id_demande: int,
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    demande = _demande_en_attente(db, id_demande, current_user)
    demande.statut = "rejetee"
    demande.id_traitant = current_user.id_utilisateur
    demande.date_traitement = datetime.now(timezone.utc)
    db.commit()
    return AccuseOut(message="Demande rejetée.")