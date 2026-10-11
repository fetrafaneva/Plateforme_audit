"""Vue « Mon service » : niveau de risque des agents du périmètre d'un responsable.

Périmètre : le service de l'utilisateur connecté et tous ses sous-services
(services_communes.id_service_parent), à l'exclusion de l'utilisateur lui-même.

Score de risque d'un agent (simple et explicable) : somme des points de ses
alertes sur la période, hors « fausse_alerte » :
    critique = 5 points, moyen = 3 points, faible = 1 point.
Niveau : aucun (0), modere (1 à 4), eleve (5 et plus).

Le responsable voit des compteurs et la liste des alertes de son périmètre.
Il ne voit ni le journal détaillé, ni les conclusions des investigations,
qui restent réservés à l'auditeur et à l'administrateur.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import distinct, func
from sqlalchemy.orm import Session, contains_eager, joinedload

from app.api.deps import get_current_user, require_role
from app.db.base import get_db
from app.models.analyse import ScoreAnomalie
from app.models.audit import JournalAcces
from app.models.identity import ServiceCommune, Utilisateur
from app.models.missions import Axe, Equipe, Participant
from app.models.securite import AlerteSecurite
from app.schemas.service import (
    AgentRisqueOut,
    AlerteServiceOut,
    MonServiceOut,
    ServiceRisqueOut,
)

router = APIRouter(
    prefix="/service",
    tags=["service"],
    dependencies=[Depends(require_role("responsable_hierarchique", "administrateur"))],
)

POIDS_GRAVITE = {"critique": 5, "moyen": 3, "faible": 1}
SEUIL_ELEVE = 5


def _niveau(points: int) -> str:
    if points >= SEUIL_ELEVE:
        return "eleve"
    if points > 0:
        return "modere"
    return "aucun"


def _rangs(valeurs: list[float]) -> list[int]:
    """Rang 1 = valeur la plus élevée ; les ex æquo partagent le même rang."""
    return [1 + sum(1 for autre in valeurs if autre > v) for v in valeurs]


def _perimetre(db: Session, id_racine: int) -> list[ServiceCommune]:
    """Le service et tous ses descendants."""
    tous = db.query(ServiceCommune).all()
    par_id = {s.id_service: s for s in tous}
    enfants: dict[int, list[int]] = {}
    for s in tous:
        if s.id_service_parent is not None:
            enfants.setdefault(s.id_service_parent, []).append(s.id_service)

    ordre: list[int] = []
    vus: set[int] = set()
    pile = [id_racine]
    while pile:
        courant = pile.pop()
        if courant in vus:  # protège d'un éventuel cycle dans la hiérarchie
            continue
        vus.add(courant)
        ordre.append(courant)
        pile.extend(enfants.get(courant, []))
    return [par_id[i] for i in ordre]


@router.get("/mon-service", response_model=MonServiceOut)
def mon_service(
    jours: int = Query(30, ge=1, le=365, description="Fenêtre d'analyse en jours"),
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    racine = db.get(ServiceCommune, current_user.id_service)
    perimetre = _perimetre(db, racine.id_service)
    ids_services = [s.id_service for s in perimetre]
    debut = datetime.now(timezone.utc) - timedelta(days=jours)

    utilisateurs = (
        db.query(Utilisateur)
        .options(joinedload(Utilisateur.role), joinedload(Utilisateur.service))
        .filter(
            Utilisateur.id_service.in_(ids_services),
            Utilisateur.statut == "actif",
            Utilisateur.id_utilisateur != current_user.id_utilisateur,
        )
        .all()
    )
    ids_users = [u.id_utilisateur for u in utilisateurs]
    par_id = {u.id_utilisateur: u for u in utilisateurs}

    acces: dict[int, int] = {}
    missions: dict[int, int] = {}
    alertes: list[AlerteSecurite] = []
    if ids_users:
        acces = dict(
            db.query(JournalAcces.id_utilisateur, func.count(JournalAcces.id_entree))
            .filter(JournalAcces.id_utilisateur.in_(ids_users), JournalAcces.horodatage >= debut)
            .group_by(JournalAcces.id_utilisateur)
            .all()
        )
        missions = dict(
            db.query(Participant.id_utilisateur, func.count(distinct(Axe.mission_id)))
            .join(Equipe, Participant.equipe_id == Equipe.id)
            .join(Axe, Equipe.axe_id == Axe.id)
            .filter(Participant.id_utilisateur.in_(ids_users))
            .group_by(Participant.id_utilisateur)
            .all()
        )
        alertes = (
            db.query(AlerteSecurite)
            .join(AlerteSecurite.score)
            .join(ScoreAnomalie.entree_journal)
            .options(
                contains_eager(AlerteSecurite.score).contains_eager(ScoreAnomalie.entree_journal)
            )
            .filter(
                JournalAcces.id_utilisateur.in_(ids_users),
                JournalAcces.horodatage >= debut,
                AlerteSecurite.statut != "fausse_alerte",
            )
            .all()
        )

    stats = {
        i: {"points": 0, "nb": 0, "critiques": 0, "derniere": None} for i in ids_users
    }
    for a in alertes:
        entree = a.score.entree_journal
        s = stats[entree.id_utilisateur]
        s["points"] += POIDS_GRAVITE.get(a.niveau_gravite, 1)
        s["nb"] += 1
        if a.niveau_gravite == "critique":
            s["critiques"] += 1
        if s["derniere"] is None or entree.horodatage > s["derniere"]:
            s["derniere"] = entree.horodatage

    # --- Classement des agents ---
    classes = sorted(
        utilisateurs,
        key=lambda u: (
            -stats[u.id_utilisateur]["points"],
            -stats[u.id_utilisateur]["nb"],
            u.nom,
            u.prenom,
        ),
    )
    rangs = _rangs([stats[u.id_utilisateur]["points"] for u in classes])
    agents = [
        AgentRisqueOut(
            rang=rangs[i],
            id_utilisateur=u.id_utilisateur,
            nom_utilisateur=f"{u.prenom} {u.nom}",
            role=u.role.nom_role,
            service=u.service.nom_service,
            nb_acces=acces.get(u.id_utilisateur, 0),
            nb_alertes=stats[u.id_utilisateur]["nb"],
            nb_alertes_critiques=stats[u.id_utilisateur]["critiques"],
            points_risque=stats[u.id_utilisateur]["points"],
            niveau_risque=_niveau(stats[u.id_utilisateur]["points"]),
            nb_missions=missions.get(u.id_utilisateur, 0),
            derniere_alerte=stats[u.id_utilisateur]["derniere"],
        )
        for i, u in enumerate(classes)
    ]

    # --- Comparaison des services du périmètre ---
    membres_par_service: dict[int, list[int]] = {}
    for u in utilisateurs:
        membres_par_service.setdefault(u.id_service, []).append(u.id_utilisateur)

    lignes = []
    for s in perimetre:
        membres = membres_par_service.get(s.id_service, [])
        if not membres:
            continue
        points = [stats[m]["points"] for m in membres]
        lignes.append(
            (s, len(membres), sum(stats[m]["nb"] for m in membres), sum(points) / len(points))
        )
    lignes.sort(key=lambda t: (-t[3], t[0].nom_service))
    rangs_services = _rangs([t[3] for t in lignes])
    services = [
        ServiceRisqueOut(
            rang=rangs_services[i],
            id_service=s.id_service,
            nom_service=s.nom_service,
            type=s.type,
            nb_agents=nb_agents,
            nb_alertes=nb_alertes,
            score_risque_moyen=round(moyenne, 1),
        )
        for i, (s, nb_agents, nb_alertes, moyenne) in enumerate(lignes)
    ]

    # --- Alertes récentes du périmètre ---
    recentes = sorted(alertes, key=lambda a: a.score.entree_journal.horodatage, reverse=True)[:10]
    alertes_recentes = [
        AlerteServiceOut(
            id_alerte=a.id_alerte,
            id_utilisateur=a.score.entree_journal.id_utilisateur,
            nom_utilisateur=(
                f"{par_id[a.score.entree_journal.id_utilisateur].prenom} "
                f"{par_id[a.score.entree_journal.id_utilisateur].nom}"
            ),
            niveau_gravite=a.niveau_gravite,
            statut=a.statut,
            horodatage=a.score.entree_journal.horodatage,
            z_score=a.score.z_score,
        )
        for a in recentes
    ]

    total_points = sum(s["points"] for s in stats.values())
    return MonServiceOut(
        id_service=racine.id_service,
        nom_service=racine.nom_service,
        type=racine.type,
        jours=jours,
        nb_agents=len(utilisateurs),
        nb_alertes=sum(s["nb"] for s in stats.values()),
        score_risque_moyen=round(total_points / len(utilisateurs), 1) if utilisateurs else 0.0,
        agents=agents,
        services=services,
        alertes_recentes=alertes_recentes,
    )