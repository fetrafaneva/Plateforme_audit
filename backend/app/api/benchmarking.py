"""Benchmarking du risque d'accès entre services.

Qui voit quoi :
  - auditeur, administrateur : le classement complet, le calcul d'une période et
    les synthèses d'audit de tous les services ;
  - responsable_hierarchique : son propre service, ses sous-services et les
    repères (médiane, moyenne) de son type de service, sans voir le détail
    nominatif des autres services.

Le calcul est déclenché à la main (POST /benchmarking/calculer) : c'est une
clôture de période, pas un recalcul permanent. Relancer la même période remplace
sa photographie et ses synthèses.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_role
from app.core.benchmarking import (
    MIN_ACCES_CLASSEMENT,
    MOTIF_PERIODE,
    PeriodeInvalide,
    calculer_benchmark,
    generer_rapports_audit,
    lignes_periode,
    periode_courante,
    periodes_disponibles,
    reperes_par_type,
)
from app.core.hierarchie import perimetre
from app.db.base import get_db
from app.models.identity import ServiceCommune, Utilisateur
from app.models.reporting import BenchmarkingService, RapportAudit
from app.schemas.benchmarking import (
    CalculOut,
    ClassementOut,
    LigneBenchmarkOut,
    MonBenchmarkOut,
    PeriodeOut,
    RapportAuditOut,
    ReperesTypeOut,
)

router = APIRouter(prefix="/benchmarking", tags=["benchmarking"])

ROLES_LECTURE = ("auditeur", "administrateur", "responsable_hierarchique")
ROLES_CALCUL = ("auditeur", "administrateur")

PERIODE_QUERY = Query(
    None,
    pattern=MOTIF_PERIODE.pattern,
    description="Période au format AAAA-MM. Par défaut, la dernière période calculée.",
)


def _ligne_out(ligne: BenchmarkingService) -> LigneBenchmarkOut:
    service = ligne.service
    return LigneBenchmarkOut(
        id_benchmark=ligne.id_benchmark,
        id_service=ligne.id_service,
        nom_service=service.nom_service if service else f"service {ligne.id_service}",
        type=service.type if service else "inconnu",
        periode=ligne.periode,
        nb_agents=ligne.nb_agents,
        nb_acces=ligne.nb_acces,
        nb_scores=ligne.nb_scores,
        nb_alertes=ligne.nb_alertes,
        nb_alertes_critiques=ligne.nb_alertes_critiques,
        taux_alertes=ligne.taux_alertes,
        score_risque_moyen=ligne.score_risque_moyen,
        rang=ligne.rang,
        date_calcul=ligne.date_calcul,
    )


def _rapport_out(rapport: RapportAudit) -> RapportAuditOut:
    return RapportAuditOut(
        id_rapport=rapport.id_rapport,
        id_service=rapport.id_service,
        nom_service=(
            rapport.service.nom_service
            if rapport.service
            else f"service {rapport.id_service}"
        ),
        periode_couverte=rapport.periode_couverte,
        contenu=rapport.contenu,
        date_generation=rapport.date_generation,
    )


def _reperes_out(
    lignes: list[BenchmarkingService],
) -> tuple[list[ReperesTypeOut], dict[str, ReperesTypeOut]]:
    type_par_service = {
        ligne.id_service: (ligne.service.type if ligne.service else "inconnu")
        for ligne in lignes
    }
    brut = reperes_par_type(lignes, type_par_service)
    sortie = {
        type_service: ReperesTypeOut(type=type_service, **valeurs)
        for type_service, valeurs in brut.items()
    }
    return sorted(sortie.values(), key=lambda r: r.type), sortie


def _tri_affichage(lignes: list[BenchmarkingService]) -> list[BenchmarkingService]:
    """Par type, puis les services classés dans l'ordre des rangs, puis les non classés."""
    return sorted(
        lignes,
        key=lambda ligne: (
            ligne.service.type if ligne.service else "zzz",
            ligne.rang is None,
            ligne.rang or 0,
            (ligne.service.nom_service if ligne.service else ""),
        ),
    )


def _derniere_periode(db: Session) -> str | None:
    periodes = periodes_disponibles(db)
    return periodes[0][0] if periodes else None


def _classement(
    db: Session, periode: str, type_service: str | None = None
) -> ClassementOut:
    lignes = lignes_periode(db, periode)
    reperes, _ = _reperes_out(lignes)
    if type_service:
        lignes = [
            ligne
            for ligne in lignes
            if ligne.service and ligne.service.type == type_service
        ]
        reperes = [r for r in reperes if r.type == type_service]
    return ClassementOut(
        periode=periode,
        min_acces_classement=MIN_ACCES_CLASSEMENT,
        nb_services=len(lignes),
        nb_services_classes=sum(1 for ligne in lignes if ligne.rang is not None),
        lignes=[_ligne_out(ligne) for ligne in _tri_affichage(lignes)],
        reperes=reperes,
    )


@router.get(
    "/periodes",
    response_model=list[PeriodeOut],
    dependencies=[Depends(require_role(*ROLES_LECTURE))],
)
def lister_periodes(db: Session = Depends(get_db)):
    """Périodes déjà calculées, de la plus récente à la plus ancienne."""
    return [
        PeriodeOut(periode=periode, nb_services=nb, date_calcul=date)
        for periode, nb, date in periodes_disponibles(db)
    ]


@router.post(
    "/calculer",
    response_model=CalculOut,
    dependencies=[Depends(require_role(*ROLES_CALCUL))],
)
def calculer(
    periode: str | None = Query(
        None,
        pattern=MOTIF_PERIODE.pattern,
        description="Période à clôturer (AAAA-MM). Par défaut, le mois en cours.",
    ),
    min_acces: int = Query(
        MIN_ACCES_CLASSEMENT,
        ge=1,
        le=10000,
        description="Nombre minimum d'accès pour qu'un service soit classé.",
    ),
    db: Session = Depends(get_db),
):
    """Calcule la photographie d'une période et régénère les synthèses d'audit."""
    periode = periode or periode_courante()
    try:
        calculer_benchmark(db, periode, min_acces=min_acces)
        rapports = generer_rapports_audit(db, periode)
    except PeriodeInvalide as erreur:
        raise HTTPException(status_code=400, detail=str(erreur))

    classement = _classement(db, periode)
    return CalculOut(
        **classement.model_dump(),
        nb_rapports_generes=len(rapports),
    )


@router.get(
    "/",
    response_model=ClassementOut,
    dependencies=[Depends(require_role(*ROLES_CALCUL))],
)
def classement(
    periode: str | None = PERIODE_QUERY,
    type_service: str | None = Query(
        None,
        max_length=30,
        description="Ne garder qu'un type de service (commune, district, ministere).",
    ),
    db: Session = Depends(get_db),
):
    """Classement complet d'une période (auditeur et administrateur)."""
    periode = periode or _derniere_periode(db)
    if periode is None:
        return ClassementOut(
            periode=periode_courante(),
            min_acces_classement=MIN_ACCES_CLASSEMENT,
            nb_services=0,
            nb_services_classes=0,
            lignes=[],
            reperes=[],
            message=(
                "Aucune période n'a encore été calculée. "
                "Lance le calcul d'une période pour obtenir un classement."
            ),
        )
    return _classement(db, periode, type_service)


@router.get(
    "/mon-service",
    response_model=MonBenchmarkOut,
    dependencies=[Depends(require_role(*ROLES_LECTURE))],
)
def mon_service(
    periode: str | None = PERIODE_QUERY,
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Position du service du responsable, sans nommer les autres services."""
    mon_id = current_user.id_service
    service = db.get(ServiceCommune, mon_id)
    mon_type = service.type if service else "inconnu"

    historique = [
        _ligne_out(ligne)
        for ligne in (
            db.query(BenchmarkingService)
            .options(joinedload(BenchmarkingService.service))
            .filter(BenchmarkingService.id_service == mon_id)
            .order_by(BenchmarkingService.periode.desc())
            .limit(12)
            .all()
        )
    ]

    periode = periode or _derniere_periode(db)
    if periode is None:
        return MonBenchmarkOut(
            periode=periode_courante(),
            min_acces_classement=MIN_ACCES_CLASSEMENT,
            service=None,
            reperes=None,
            sous_services=[],
            historique=historique,
            rapport=None,
            message=(
                "Aucune période n'a encore été calculée. "
                "L'auditeur ou l'administrateur doit clôturer une période."
            ),
        )

    lignes = lignes_periode(db, periode)
    _, reperes = _reperes_out(lignes)

    ma_ligne = next((ligne for ligne in lignes if ligne.id_service == mon_id), None)
    ids_perimetre = {s.id_service for s in perimetre(db, mon_id)} - {mon_id}
    sous_services = [
        ligne for ligne in _tri_affichage(lignes) if ligne.id_service in ids_perimetre
    ]

    rapport = (
        db.query(RapportAudit)
        .options(joinedload(RapportAudit.service))
        .filter(
            RapportAudit.id_service == mon_id,
            RapportAudit.periode_couverte == periode,
        )
        .first()
    )

    if ma_ligne is None:
        message = (
            "Ton service n'a ni agent actif ni accès journalisé sur cette période : "
            "il n'apparaît pas dans le benchmark."
        )
    elif ma_ligne.rang is None:
        message = (
            f"Ton service a {ma_ligne.nb_acces} accès sur la période, en dessous du "
            f"minimum de {MIN_ACCES_CLASSEMENT} : les indicateurs sont affichés mais "
            "le service n'est pas classé."
        )
    else:
        message = None

    return MonBenchmarkOut(
        periode=periode,
        min_acces_classement=MIN_ACCES_CLASSEMENT,
        service=_ligne_out(ma_ligne) if ma_ligne else None,
        reperes=reperes.get(mon_type),
        sous_services=[_ligne_out(ligne) for ligne in sous_services],
        historique=historique,
        rapport=_rapport_out(rapport) if rapport else None,
        message=message,
    )


@router.get(
    "/rapports",
    response_model=list[RapportAuditOut],
    dependencies=[Depends(require_role(*ROLES_CALCUL))],
)
def lister_rapports_audit(
    periode: str | None = PERIODE_QUERY,
    id_service: int | None = Query(None, description="Ne garder qu'un service."),
    db: Session = Depends(get_db),
):
    """Synthèses d'audit générées pour une période."""
    periode = periode or _derniere_periode(db)
    if periode is None:
        return []

    requete = (
        db.query(RapportAudit)
        .options(joinedload(RapportAudit.service))
        .filter(RapportAudit.periode_couverte == periode)
    )
    if id_service is not None:
        requete = requete.filter(RapportAudit.id_service == id_service)
    return [
        _rapport_out(rapport)
        for rapport in requete.order_by(RapportAudit.id_service).all()
    ]
