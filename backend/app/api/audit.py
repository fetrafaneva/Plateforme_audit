"""Routes de lecture et de traitement pour le module d'audit.

Toutes les routes sont réservées aux rôles `auditeur` et `administrateur`
(dépendance posée sur le routeur). La vérification d'intégrité de la chaîne
reste dans GET /journal/verify.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import distinct, func
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_role
from app.db.base import get_db
from app.models.analyse import ProfilComportemental, ScoreAnomalie
from app.models.audit import JournalAcces
from app.models.identity import Utilisateur
from app.models.ressources import RessourceSensible
from app.models.securite import AlerteSecurite, Investigation
from app.schemas.audit import (
    AlerteOut,
    AlerteUpdate,
    InvestigationCloture,
    InvestigationOut,
    JournalLigneOut,
    ProfilLigneOut,
    RessourceOut,
    ResumeAudit,
    ScoreLigneOut,
)

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(require_role("auditeur", "administrateur"))],
)


def _nom(utilisateur: Utilisateur) -> str:
    return f"{utilisateur.prenom} {utilisateur.nom}"


# Chargement en une seule requête de la chaîne alerte -> score -> entrée -> utilisateur
_CHARGER_ALERTE = (
    joinedload(AlerteSecurite.score)
    .joinedload(ScoreAnomalie.entree_journal)
    .joinedload(JournalAcces.utilisateur),
    joinedload(AlerteSecurite.politique),
)


def _alerte_out(a: AlerteSecurite) -> AlerteOut:
    entree = a.score.entree_journal
    return AlerteOut(
        id_alerte=a.id_alerte,
        id_score=a.id_score,
        niveau_gravite=a.niveau_gravite,
        statut=a.statut,
        date_creation=a.date_creation,
        id_utilisateur=entree.id_utilisateur,
        nom_utilisateur=_nom(entree.utilisateur),
        z_score=a.score.z_score,
        horodatage=entree.horodatage,
        nom_politique=a.politique.nom_politique,
    )


def _investigation_out(i: Investigation) -> InvestigationOut:
    alerte = i.alerte
    entree = alerte.score.entree_journal
    return InvestigationOut(
        id_investigation=i.id_investigation,
        id_alerte=i.id_alerte,
        id_enqueteur=i.id_enqueteur,
        nom_enqueteur=_nom(i.enqueteur),
        statut=i.statut,
        conclusion=i.conclusion,
        date_ouverture=i.date_ouverture,
        date_cloture=i.date_cloture,
        niveau_gravite=alerte.niveau_gravite,
        id_utilisateur=entree.id_utilisateur,
        nom_utilisateur=_nom(entree.utilisateur),
    )


def _requete_investigations(db: Session):
    return db.query(Investigation).options(
        joinedload(Investigation.enqueteur),
        joinedload(Investigation.alerte)
        .joinedload(AlerteSecurite.score)
        .joinedload(ScoreAnomalie.entree_journal)
        .joinedload(JournalAcces.utilisateur),
    )


# ---------- Synthèse ----------


@router.get("/resume", response_model=ResumeAudit)
def resume(db: Session = Depends(get_db)):
    return ResumeAudit(
        nb_entrees_journal=db.query(func.count(JournalAcces.id_entree)).scalar(),
        nb_utilisateurs_surveilles=db.query(
            func.count(distinct(JournalAcces.id_utilisateur))
        ).scalar(),
        nb_scores=db.query(func.count(ScoreAnomalie.id_score)).scalar(),
        nb_alertes_nouvelles=db.query(func.count(AlerteSecurite.id_alerte))
        .filter(AlerteSecurite.statut == "nouvelle")
        .scalar(),
        nb_alertes_critiques_ouvertes=db.query(func.count(AlerteSecurite.id_alerte))
        .filter(
            AlerteSecurite.niveau_gravite == "critique",
            AlerteSecurite.statut.in_(["nouvelle", "en_investigation"]),
        )
        .scalar(),
        nb_investigations_ouvertes=db.query(func.count(Investigation.id_investigation))
        .filter(Investigation.statut == "ouverte")
        .scalar(),
    )


# ---------- Journal d'accès ----------


@router.get("/journal", response_model=list[JournalLigneOut])
def lister_journal(
    id_utilisateur: int | None = None,
    id_ressource: int | None = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    requete = db.query(JournalAcces).options(
        joinedload(JournalAcces.utilisateur), joinedload(JournalAcces.ressource)
    )
    if id_utilisateur is not None:
        requete = requete.filter(JournalAcces.id_utilisateur == id_utilisateur)
    if id_ressource is not None:
        requete = requete.filter(JournalAcces.id_ressource == id_ressource)

    entrees = (
        requete.order_by(JournalAcces.id_entree.desc()).offset(offset).limit(limit).all()
    )
    return [
        JournalLigneOut(
            id_entree=e.id_entree,
            id_utilisateur=e.id_utilisateur,
            nom_utilisateur=_nom(e.utilisateur),
            id_ressource=e.id_ressource,
            type_ressource=e.ressource.type_ressource,
            type_action=e.type_action,
            horodatage=e.horodatage,
            adresse_ip=e.adresse_ip,
            hash_entree=e.hash_entree,
            hash_precedent=e.hash_precedent,
        )
        for e in entrees
    ]


# ---------- Scores d'anomalie ----------


@router.get("/scores", response_model=list[ScoreLigneOut])
def lister_scores(
    z_min: float | None = Query(None, ge=0, description="Valeur absolue minimale du z-score"),
    id_utilisateur: int | None = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    requete = db.query(ScoreAnomalie).options(
        joinedload(ScoreAnomalie.entree_journal).joinedload(JournalAcces.utilisateur)
    )
    if z_min is not None:
        requete = requete.filter(func.abs(ScoreAnomalie.z_score) >= z_min)
    if id_utilisateur is not None:
        requete = requete.join(ScoreAnomalie.entree_journal).filter(
            JournalAcces.id_utilisateur == id_utilisateur
        )

    scores = requete.order_by(func.abs(ScoreAnomalie.z_score).desc()).limit(limit).all()
    return [
        ScoreLigneOut(
            id_score=s.id_score,
            id_entree_journal=s.id_entree_journal,
            id_utilisateur=s.entree_journal.id_utilisateur,
            nom_utilisateur=_nom(s.entree_journal.utilisateur),
            type_action=s.entree_journal.type_action,
            horodatage=s.entree_journal.horodatage,
            z_score=s.z_score,
            methode_utilisee=s.methode_utilisee,
            date_calcul=s.date_calcul,
        )
        for s in scores
    ]


# ---------- Alertes ----------


@router.get("/alertes", response_model=list[AlerteOut])
def lister_alertes(
    statut: str | None = None,
    niveau_gravite: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    requete = db.query(AlerteSecurite).options(*_CHARGER_ALERTE)
    if statut:
        requete = requete.filter(AlerteSecurite.statut == statut)
    if niveau_gravite:
        requete = requete.filter(AlerteSecurite.niveau_gravite == niveau_gravite)
    alertes = (
        requete.order_by(AlerteSecurite.date_creation.desc(), AlerteSecurite.id_alerte.desc())
        .limit(limit)
        .all()
    )
    return [_alerte_out(a) for a in alertes]


@router.patch("/alertes/{id_alerte}", response_model=AlerteOut)
def modifier_alerte(id_alerte: int, payload: AlerteUpdate, db: Session = Depends(get_db)):
    alerte = db.get(AlerteSecurite, id_alerte)
    if alerte is None:
        raise HTTPException(status_code=404, detail="Alerte introuvable")
    alerte.statut = payload.statut
    db.commit()
    db.refresh(alerte)
    return _alerte_out(alerte)


@router.post(
    "/alertes/{id_alerte}/investigation",
    response_model=InvestigationOut,
    status_code=201,
)
def ouvrir_investigation(
    id_alerte: int,
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alerte = db.get(AlerteSecurite, id_alerte)
    if alerte is None:
        raise HTTPException(status_code=404, detail="Alerte introuvable")

    deja_ouverte = (
        db.query(Investigation)
        .filter(Investigation.id_alerte == id_alerte, Investigation.statut == "ouverte")
        .first()
    )
    if deja_ouverte is not None:
        raise HTTPException(
            status_code=400, detail="Une investigation est déjà ouverte pour cette alerte"
        )

    investigation = Investigation(id_alerte=id_alerte, id_enqueteur=current_user.id_utilisateur)
    alerte.statut = "en_investigation"
    db.add(investigation)
    db.commit()
    return _investigation_out(
        _requete_investigations(db)
        .filter(Investigation.id_investigation == investigation.id_investigation)
        .one()
    )


# ---------- Investigations ----------


@router.get("/investigations", response_model=list[InvestigationOut])
def lister_investigations(statut: str | None = None, db: Session = Depends(get_db)):
    requete = _requete_investigations(db)
    if statut:
        requete = requete.filter(Investigation.statut == statut)
    investigations = requete.order_by(Investigation.id_investigation.desc()).all()
    return [_investigation_out(i) for i in investigations]


@router.patch("/investigations/{id_investigation}/cloture", response_model=InvestigationOut)
def cloturer_investigation(
    id_investigation: int, payload: InvestigationCloture, db: Session = Depends(get_db)
):
    investigation = (
        _requete_investigations(db)
        .filter(Investigation.id_investigation == id_investigation)
        .first()
    )
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation introuvable")
    if investigation.statut == "cloturee":
        raise HTTPException(status_code=400, detail="Cette investigation est déjà clôturée")

    investigation.statut = "cloturee"
    investigation.conclusion = payload.conclusion.strip()
    investigation.date_cloture = datetime.now(timezone.utc)
    investigation.alerte.statut = "traitee"
    db.commit()
    db.refresh(investigation)
    return _investigation_out(investigation)


# ---------- Profils et ressources ----------


@router.get("/profils", response_model=list[ProfilLigneOut])
def lister_profils(db: Session = Depends(get_db)):
    """Dernier profil calculé de chaque utilisateur."""
    profils = (
        db.query(ProfilComportemental)
        .options(joinedload(ProfilComportemental.utilisateur))
        .order_by(
            ProfilComportemental.date_calcul.desc(), ProfilComportemental.id_profil.desc()
        )
        .all()
    )
    derniers: dict[int, ProfilComportemental] = {}
    for p in profils:
        derniers.setdefault(p.id_utilisateur, p)

    return [
        ProfilLigneOut(
            id_profil=p.id_profil,
            id_utilisateur=p.id_utilisateur,
            nom_utilisateur=_nom(p.utilisateur),
            periode_reference=p.periode_reference,
            volume_moyen=p.volume_moyen,
            horaires_habituels=p.horaires_habituels,
            perimetre_habituel=p.perimetre_habituel,
            date_calcul=p.date_calcul,
        )
        for p in sorted(derniers.values(), key=lambda p: _nom(p.utilisateur))
    ]


@router.get("/ressources", response_model=list[RessourceOut])
def lister_ressources(db: Session = Depends(get_db)):
    compte = dict(
        db.query(JournalAcces.id_ressource, func.count(JournalAcces.id_entree))
        .group_by(JournalAcces.id_ressource)
        .all()
    )
    ressources = db.query(RessourceSensible).order_by(RessourceSensible.id_ressource).all()
    return [
        RessourceOut(
            id_ressource=r.id_ressource,
            type_ressource=r.type_ressource,
            niveau_sensibilite=r.niveau_sensibilite,
            id_service_proprietaire=r.id_service_proprietaire,
            nb_acces=compte.get(r.id_ressource, 0),
        )
        for r in ressources
    ]