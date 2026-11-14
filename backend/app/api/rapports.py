"""Rapports de mission : rédaction par le chef d'équipe, pièces jointes obligatoires,
soumission et validation.

Droits :
- rédiger, déposer des pièces, soumettre : chef_mission uniquement, pour l'axe dont il fait
  partie de l'équipe (participant lié à son compte) et seulement sur ses propres rapports ;
- valider ou demander une correction : administrateur uniquement (il ne rédige jamais) ;
- lire : chef_mission (ses rapports), administrateur, responsable_hierarchique, auditeur ;
- télécharger le PDF, une fois le rapport validé : l'auteur et l'administrateur.

Traçabilité : les consultations, les soumissions/validations, les dépôts de fiches et les
téléchargements de documents sont écrits dans le journal d'accès chaîné (ressource
« Rapports de mission »), donc visibles par l'audit. Les photos, simples illustrations
affichées avec le rapport, ne génèrent pas d'entrée séparée.
"""

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.deps import get_current_user, require_role
from app.core.config import settings
from app.core.journal import ajouter_entree, obtenir_id_ressource
from app.core.notifications import notifier, notifier_administrateurs
from app.core.reseau import ip_du_client
from app.core.pdf_rapport import construire_pdf
from app.db.base import get_db
from app.models.identity import Utilisateur
from app.models.missions import (
    Axe,
    District,
    Equipe,
    IndicateurPerformance,
    Journee,
    MissionDistrict,
    Participant,
)
from app.models.rapports import PieceJointe, RapportDifficulte, RapportMission
from app.schemas.rapports import (
    AxeDisponibleOut,
    ChronoLigneIn,
    CompletudeOut,
    CompteursRapportsOut,
    CorrectionIn,
    DifficulteIn,
    DifficulteOut,
    DistrictRapportOut,
    ElementCompletude,
    JourneeRapportOut,
    MembreOut,
    PieceOut,
    RapportCreate,
    RapportDetailOut,
    RapportResume,
    RapportUpdate,
    ResultatOut,
    TypePiece,
)

router = APIRouter(prefix="/rapports", tags=["rapports de mission"])

ROLES_REDACTION = ("chef_mission",)  # l'administrateur valide, il ne rédige pas
ROLES_LECTURE = ("chef_mission", "administrateur", "responsable_hierarchique", "auditeur")
STATUTS_MODIFIABLES = ("brouillon", "a_corriger")
RESSOURCE_RAPPORTS = "Rapports de mission"

# --- Pièces requises pour pouvoir soumettre (à adapter au besoin) ---
PIECES_PAR_DISTRICT = [
    ("fiche_reception", "Fiche de réception technique signée", 1),
    ("fiche_presence", "Fiche de présence des participants", 1),
    ("photo", "Photos de la mission", 1),
]
PIECES_GLOBALES = [
    ("fiche_evaluation", "Fiche d'évaluation de la formation (consolidée)", 1),
]
TYPES_PAR_DISTRICT = tuple(code for code, _, _ in PIECES_PAR_DISTRICT)
SECTIONS_OBLIGATOIRES = {"contexte": "Contexte", "conclusion": "Conclusion générale"}

CHAMPS_TEXTE = (
    "contexte", "justification", "itineraire_reel", "inventaire_materiel",
    "configuration_technique", "tests_securite", "profil_participants",
    "themes_formation", "evaluation_formation", "points_forts", "lecons_apprises",
    "bonnes_pratiques", "conclusion", "recommandations",
)

# --- Fichiers acceptés ---
TAILLE_MAX = 10 * 1024 * 1024  # 10 Mo
EXTENSIONS = {
    ".jpg": "jpeg", ".jpeg": "jpeg", ".png": "png", ".webp": "webp",
    ".pdf": "pdf", ".docx": "zip", ".xlsx": "zip",
}
MIMES = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp",
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
EXTENSIONS_PHOTO = {".jpg", ".jpeg", ".png", ".webp"}


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------


def _role(user: Utilisateur) -> str:
    return user.role.nom_role


def _maintenant() -> datetime:
    return datetime.now(timezone.utc)


def _dossier_base() -> Path:
    return Path(settings.uploads_dir).resolve()


def _journaliser(db: Session, user: Utilisateur, type_action: str, request: Request) -> None:
    id_ressource = obtenir_id_ressource(db, RESSOURCE_RAPPORTS, "moyen", user.id_service)
    ajouter_entree(db, user.id_utilisateur, id_ressource, type_action, ip_du_client(request))


def _charger(db: Session, id_rapport: int) -> RapportMission:
    rapport = (
        db.query(RapportMission)
        .options(
            joinedload(RapportMission.axe).joinedload(Axe.mission),
            joinedload(RapportMission.auteur),
            joinedload(RapportMission.validateur),
            selectinload(RapportMission.difficultes),
            selectinload(RapportMission.pieces),
        )
        .filter(RapportMission.id == id_rapport)
        .first()
    )
    if rapport is None:
        raise HTTPException(status_code=404, detail="Rapport introuvable")
    return rapport


def _verifier_lecture(rapport: RapportMission, user: Utilisateur) -> None:
    if _role(user) == "chef_mission" and rapport.id_auteur != user.id_utilisateur:
        raise HTTPException(status_code=403, detail="Ce rapport appartient à un autre chef de mission")


def _verifier_edition(rapport: RapportMission, user: Utilisateur) -> None:
    if _role(user) == "chef_mission" and rapport.id_auteur != user.id_utilisateur:
        raise HTTPException(status_code=403, detail="Ce rapport appartient à un autre chef de mission")
    if rapport.statut not in STATUTS_MODIFIABLES:
        raise HTTPException(
            status_code=400,
            detail=f"Le rapport est « {rapport.statut} » : il n'est plus modifiable",
        )


def _libelle_axe(rapport: RapportMission) -> str:
    numero = rapport.axe.numero_axe if rapport.axe.numero_axe is not None else rapport.axe_id
    return f"axe {numero} de « {rapport.axe.mission.titre} »"


def _journees_axe(db: Session, noms_districts: dict[int, str]) -> list[JourneeRapportOut]:
    """Journées des districts de l'axe, avec les colonnes du chronogramme."""
    if not noms_districts:
        return []
    journees = (
        db.query(Journee)
        .filter(Journee.mission_district_id.in_(list(noms_districts)))
        .order_by(Journee.mission_district_id, Journee.date, Journee.numero_jour, Journee.id)
        .all()
    )
    return [
        JourneeRapportOut(
            id_journee=j.id,
            id_mission_district=j.mission_district_id,
            nom_district=noms_districts[j.mission_district_id],
            numero_jour=j.numero_jour,
            date=j.date,
            lieu=j.lieu,
            statut=j.statut,
            activites_prevues=j.activites_prevues,
            activites_realisees=j.activites_realisees,
            ecart=j.ecart,
        )
        for j in journees
    ]


def _est_membre_axe(db: Session, user: Utilisateur, axe_id: int) -> bool:
    """L'utilisateur est-il lié (via un participant) à une équipe de cet axe ?"""
    return (
        db.query(Participant.id)
        .join(Equipe, Participant.equipe_id == Equipe.id)
        .filter(Equipe.axe_id == axe_id, Participant.id_utilisateur == user.id_utilisateur)
        .first()
        is not None
    )


def _nombre(valeur: str | None) -> float | None:
    try:
        return float(str(valeur).replace(",", ".").replace("%", "").strip())
    except (TypeError, ValueError):
        return None


def _taux(cible: str | None, realise: str | None) -> float | None:
    c, r = _nombre(cible), _nombre(realise)
    if not c or r is None:  # cible absente, nulle ou non numérique
        return None
    return round(r / c * 100, 1)


def _famille(contenu: bytes) -> str | None:
    """Type réel du fichier d'après ses premiers octets (et non son extension)."""
    if contenu.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if contenu.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if contenu[:4] == b"RIFF" and contenu[8:12] == b"WEBP":
        return "webp"
    if contenu.startswith(b"%PDF-"):
        return "pdf"
    if contenu.startswith(b"PK\x03\x04"):
        return "zip"
    return None


def _chemin_piece(piece: PieceJointe) -> Path:
    base = _dossier_base()
    chemin = (base / piece.chemin_stockage).resolve()
    if base not in chemin.parents:  # garde-fou contre un chemin qui sortirait du dossier
        raise HTTPException(status_code=404, detail="Fichier introuvable")
    return chemin


def _piece_out(p: PieceJointe, nom_district: str | None, nom_televerseur: str) -> PieceOut:
    return PieceOut(
        id=p.id,
        type_piece=p.type_piece,
        nom_original=p.nom_original,
        type_mime=p.type_mime,
        taille=p.taille,
        legende=p.legende,
        id_mission_district=p.id_mission_district,
        nom_district=nom_district,
        nom_televerseur=nom_televerseur,
        date_depot=p.date_depot,
        empreinte_sha256=p.empreinte_sha256,
    )


def _completude(rapport: RapportMission, districts: list[DistrictRapportOut]) -> CompletudeOut:
    elements: list[ElementCompletude] = []
    if not districts:
        elements.append(
            ElementCompletude(
                code="districts", libelle="Au moins un district rattaché à l'axe",
                district=None, requis=1, fourni=0, ok=False,
            )
        )
    for d in districts:
        for code, libelle, requis in PIECES_PAR_DISTRICT:
            fourni = sum(
                1 for p in rapport.pieces
                if p.type_piece == code and p.id_mission_district == d.id_mission_district
            )
            elements.append(
                ElementCompletude(
                    code=code, libelle=libelle, district=d.nom,
                    requis=requis, fourni=fourni, ok=fourni >= requis,
                )
            )
    for code, libelle, requis in PIECES_GLOBALES:
        fourni = sum(1 for p in rapport.pieces if p.type_piece == code)
        elements.append(
            ElementCompletude(
                code=code, libelle=libelle, district=None,
                requis=requis, fourni=fourni, ok=fourni >= requis,
            )
        )
    manquantes = [
        libelle for champ, libelle in SECTIONS_OBLIGATOIRES.items()
        if not (getattr(rapport, champ) or "").strip()
    ]
    return CompletudeOut(
        complet=all(e.ok for e in elements) and not manquantes,
        elements=elements,
        sections_manquantes=manquantes,
    )


def _detail(db: Session, rapport: RapportMission, user: Utilisateur) -> RapportDetailOut:
    axe = rapport.axe
    mission = axe.mission

    lignes = (
        db.query(MissionDistrict, District.nom)
        .join(District, District.id == MissionDistrict.district_id)
        .filter(MissionDistrict.axe_id == axe.id)
        .order_by(MissionDistrict.ordre_visite, MissionDistrict.id)
        .all()
    )
    districts = [
        DistrictRapportOut(id_mission_district=md.id, nom=nom, statut=md.statut)
        for md, nom in lignes
    ]
    noms_districts = {d.id_mission_district: d.nom for d in districts}
    journees = _journees_axe(db, noms_districts)

    membres = [
        MembreOut(nom=p.nom, fonction=p.fonction, equipe=type_equipe)
        for p, type_equipe in (
            db.query(Participant, Equipe.type_equipe)
            .join(Equipe, Participant.equipe_id == Equipe.id)
            .filter(Equipe.axe_id == axe.id)
            .order_by(Participant.id)
            .all()
        )
    ]

    debut = fin = None
    if noms_districts:
        debut, fin = (
            db.query(func.min(Journee.date), func.max(Journee.date))
            .filter(Journee.mission_district_id.in_(list(noms_districts)))
            .one()
        )
    if debut is None and mission.date_debut:
        debut = mission.date_debut.date()
    if fin is None and mission.date_fin_prevue:
        fin = mission.date_fin_prevue.date()

    resultats = [
        ResultatOut(
            resultat_attendu=i.resultat_attendu,
            indicateur_mesure=i.indicateur_mesure,
            cible=i.cible,
            realise=i.valeur_realisee,
            taux=_taux(i.cible, i.valeur_realisee),
        )
        for i in (
            db.query(IndicateurPerformance)
            .filter(IndicateurPerformance.mission_id == mission.id)
            .order_by(IndicateurPerformance.id)
            .all()
        )
    ]

    ids_users = {p.id_televerseur for p in rapport.pieces}
    noms_users = (
        {
            u.id_utilisateur: f"{u.prenom} {u.nom}"
            for u in db.query(Utilisateur).filter(Utilisateur.id_utilisateur.in_(ids_users)).all()
        }
        if ids_users
        else {}
    )
    pieces = [
        _piece_out(p, noms_districts.get(p.id_mission_district), noms_users.get(p.id_televerseur, "—"))
        for p in rapport.pieces
    ]

    role = _role(user)
    est_auteur = rapport.id_auteur == user.id_utilisateur
    modifiable = (
        role in ROLES_REDACTION and est_auteur and rapport.statut in STATUTS_MODIFIABLES
    )
    peut_valider = role == "administrateur" and rapport.statut == "soumis" and not est_auteur
    peut_telecharger_pdf = rapport.statut == "valide" and (
        role == "administrateur" or (role == "chef_mission" and est_auteur)
    )

    return RapportDetailOut(
        id=rapport.id,
        statut=rapport.statut,
        modifiable=modifiable,
        peut_valider=peut_valider,
        peut_telecharger_pdf=peut_telecharger_pdf,
        id_axe=axe.id,
        numero_axe=axe.numero_axe,
        id_mission=mission.id,
        titre_mission=mission.titre,
        type_mission=mission.type_mission,
        periode_debut=debut,
        periode_fin=fin,
        districts=districts,
        membres=membres,
        journees=journees,
        resultats=resultats,
        id_auteur=rapport.id_auteur,
        auteur=f"{rapport.auteur.prenom} {rapport.auteur.nom}",
        **{champ: getattr(rapport, champ) for champ in CHAMPS_TEXTE},
        nb_participants_formes=rapport.nb_participants_formes,
        difficultes=[
            DifficulteOut(id=d.id, categorie=d.categorie, description=d.description, solution=d.solution)
            for d in rapport.difficultes
        ],
        pieces=pieces,
        completude=_completude(rapport, districts),
        date_creation=rapport.date_creation,
        date_modification=rapport.date_modification,
        date_soumission=rapport.date_soumission,
        date_validation=rapport.date_validation,
        nom_validateur=(
            f"{rapport.validateur.prenom} {rapport.validateur.nom}" if rapport.validateur else None
        ),
        commentaire_validation=rapport.commentaire_validation,
    )


# ---------------------------------------------------------------------------
# Liste et création
# ---------------------------------------------------------------------------


@router.get(
    "/axes-disponibles",
    response_model=list[AxeDisponibleOut],
    dependencies=[Depends(require_role(*ROLES_REDACTION))],
)
def axes_disponibles(
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Axes sans rapport dont le chef de mission fait partie de l'équipe."""
    ses_axes = (
        select(Equipe.axe_id)
        .join(Participant, Participant.equipe_id == Equipe.id)
        .where(Participant.id_utilisateur == current_user.id_utilisateur)
    )
    axes = (
        db.query(Axe)
        .options(joinedload(Axe.mission))
        .outerjoin(RapportMission, RapportMission.axe_id == Axe.id)
        .filter(RapportMission.id.is_(None), Axe.id.in_(ses_axes))
        .order_by(Axe.mission_id.desc(), Axe.numero_axe)
        .all()
    )
    return [
        AxeDisponibleOut(
            id_axe=a.id, numero_axe=a.numero_axe,
            id_mission=a.mission.id, titre_mission=a.mission.titre,
        )
        for a in axes
    ]


@router.get(
    "/compteurs",
    response_model=CompteursRapportsOut,
    dependencies=[Depends(require_role(*ROLES_LECTURE))],
)
def compter_rapports(
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Nombre de rapports par statut (les siens pour un chef de mission, tous sinon)."""
    requete = db.query(RapportMission.statut, func.count(RapportMission.id))
    if _role(current_user) == "chef_mission":
        requete = requete.filter(RapportMission.id_auteur == current_user.id_utilisateur)
    comptes = dict(requete.group_by(RapportMission.statut).all())
    return CompteursRapportsOut(
        brouillon=comptes.get("brouillon", 0),
        soumis=comptes.get("soumis", 0),
        a_corriger=comptes.get("a_corriger", 0),
        valide=comptes.get("valide", 0),
    )


@router.get(
    "/",
    response_model=list[RapportResume],
    dependencies=[Depends(require_role(*ROLES_LECTURE))],
)
def lister_rapports(
    statut: str | None = None,
    id_mission: int | None = None,
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    requete = db.query(RapportMission).options(
        joinedload(RapportMission.axe).joinedload(Axe.mission),
        joinedload(RapportMission.auteur),
        selectinload(RapportMission.pieces),
    )
    if _role(current_user) == "chef_mission":
        requete = requete.filter(RapportMission.id_auteur == current_user.id_utilisateur)
    if statut:
        requete = requete.filter(RapportMission.statut == statut)
    if id_mission is not None:
        requete = requete.join(Axe, RapportMission.axe_id == Axe.id).filter(Axe.mission_id == id_mission)

    rapports = requete.order_by(RapportMission.date_modification.desc()).all()
    return [
        RapportResume(
            id=r.id,
            id_axe=r.axe_id,
            numero_axe=r.axe.numero_axe,
            id_mission=r.axe.mission.id,
            titre_mission=r.axe.mission.titre,
            auteur=f"{r.auteur.prenom} {r.auteur.nom}",
            statut=r.statut,
            nb_pieces=len(r.pieces),
            date_soumission=r.date_soumission,
            date_modification=r.date_modification,
        )
        for r in rapports
    ]


@router.post(
    "/",
    response_model=RapportDetailOut,
    status_code=201,
    dependencies=[Depends(require_role(*ROLES_REDACTION))],
)
def creer_rapport(
    payload: RapportCreate,
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    axe = db.get(Axe, payload.axe_id)
    if axe is None:
        raise HTTPException(status_code=404, detail="Axe introuvable")
    if not _est_membre_axe(db, current_user, axe.id):
        raise HTTPException(
            status_code=403,
            detail=(
                "Tu ne peux rédiger que le rapport d'un axe dont tu fais partie de l'équipe. "
                "Ton compte doit être lié à un participant de cet axe."
            ),
        )
    if db.query(RapportMission).filter(RapportMission.axe_id == axe.id).first():
        raise HTTPException(status_code=400, detail="Un rapport existe déjà pour cet axe")

    rapport = RapportMission(
        axe_id=axe.id,
        id_auteur=current_user.id_utilisateur,
        itineraire_reel=axe.itineraire_principal,
    )
    db.add(rapport)
    db.commit()
    return _detail(db, _charger(db, rapport.id), current_user)


# ---------------------------------------------------------------------------
# Lecture, modification
# ---------------------------------------------------------------------------


@router.get(
    "/{id_rapport}",
    response_model=RapportDetailOut,
    dependencies=[Depends(require_role(*ROLES_LECTURE))],
)
def obtenir_rapport(
    id_rapport: int,
    request: Request,
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rapport = _charger(db, id_rapport)
    _verifier_lecture(rapport, current_user)
    detail = _detail(db, rapport, current_user)
    _journaliser(db, current_user, "consultation", request)
    db.commit()
    return detail


@router.patch(
    "/{id_rapport}",
    response_model=RapportDetailOut,
    dependencies=[Depends(require_role(*ROLES_REDACTION))],
)
def modifier_rapport(
    id_rapport: int,
    payload: RapportUpdate,
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rapport = _charger(db, id_rapport)
    _verifier_edition(rapport, current_user)

    for champ, valeur in payload.model_dump(exclude_unset=True).items():
        if isinstance(valeur, str):
            valeur = valeur.strip()
        setattr(rapport, champ, valeur)
    rapport.date_modification = _maintenant()
    db.commit()
    return _detail(db, _charger(db, id_rapport), current_user)


@router.put(
    "/{id_rapport}/difficultes",
    response_model=list[DifficulteOut],
    dependencies=[Depends(require_role(*ROLES_REDACTION))],
)
def remplacer_difficultes(
    id_rapport: int,
    difficultes: list[DifficulteIn],
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remplace toute la liste des difficultés et solutions (section 5)."""
    if len(difficultes) > 30:
        raise HTTPException(status_code=400, detail="30 difficultés au maximum")
    rapport = _charger(db, id_rapport)
    _verifier_edition(rapport, current_user)

    rapport.difficultes = [RapportDifficulte(**d.model_dump()) for d in difficultes]
    rapport.date_modification = _maintenant()
    db.commit()
    db.refresh(rapport)
    return [
        DifficulteOut(id=d.id, categorie=d.categorie, description=d.description, solution=d.solution)
        for d in rapport.difficultes
    ]


@router.put(
    "/{id_rapport}/chronogramme",
    response_model=list[JourneeRapportOut],
    dependencies=[Depends(require_role(*ROLES_REDACTION))],
)
def remplacer_chronogramme(
    id_rapport: int,
    lignes: list[ChronoLigneIn],
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Renseigne, jour par jour, les activités planifiées, réalisées et l'écart."""
    rapport = _charger(db, id_rapport)
    _verifier_edition(rapport, current_user)

    noms = {
        md.id: nom
        for md, nom in (
            db.query(MissionDistrict, District.nom)
            .join(District, District.id == MissionDistrict.district_id)
            .filter(MissionDistrict.axe_id == rapport.axe_id)
            .all()
        )
    }
    journees = (
        {j.id: j for j in db.query(Journee).filter(Journee.mission_district_id.in_(list(noms)))}
        if noms
        else {}
    )
    for ligne in lignes:
        journee = journees.get(ligne.id_journee)
        if journee is None:
            raise HTTPException(
                status_code=400,
                detail=f"La journée {ligne.id_journee} n'appartient pas à l'axe de ce rapport",
            )
        journee.activites_prevues = (ligne.activites_prevues or "").strip() or None
        journee.activites_realisees = (ligne.activites_realisees or "").strip() or None
        journee.ecart = (ligne.ecart or "").strip() or None

    rapport.date_modification = _maintenant()
    db.commit()
    return _journees_axe(db, noms)


# ---------------------------------------------------------------------------
# Pièces jointes
# ---------------------------------------------------------------------------


@router.post(
    "/{id_rapport}/pieces",
    response_model=PieceOut,
    status_code=201,
    dependencies=[Depends(require_role(*ROLES_REDACTION))],
)
def deposer_piece(
    id_rapport: int,
    request: Request,
    fichier: UploadFile = File(...),
    type_piece: TypePiece = Form(...),
    id_mission_district: int | None = Form(None),
    legende: str | None = Form(None),
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rapport = _charger(db, id_rapport)
    _verifier_edition(rapport, current_user)

    nom_district = None
    if type_piece in TYPES_PAR_DISTRICT:
        if id_mission_district is None:
            raise HTTPException(status_code=400, detail="Choisis le district concerné par cette pièce")
        md = (
            db.query(MissionDistrict, District.nom)
            .join(District, District.id == MissionDistrict.district_id)
            .filter(MissionDistrict.id == id_mission_district)
            .first()
        )
        if md is None or md[0].axe_id != rapport.axe_id:
            raise HTTPException(status_code=400, detail="Ce district n'appartient pas à l'axe du rapport")
        nom_district = md[1]
    else:
        id_mission_district = None

    nom_original = Path((fichier.filename or "fichier").replace("\\", "/")).name[:255]
    extension = Path(nom_original).suffix.lower()
    autorisees = EXTENSIONS_PHOTO if type_piece == "photo" else set(EXTENSIONS)
    if extension not in autorisees:
        raise HTTPException(
            status_code=400,
            detail="Format non accepté. Autorisés : " + ", ".join(sorted(autorisees)),
        )

    contenu = fichier.file.read(TAILLE_MAX + 1)
    if not contenu:
        raise HTTPException(status_code=400, detail="Le fichier est vide")
    if len(contenu) > TAILLE_MAX:
        raise HTTPException(status_code=413, detail="Fichier trop volumineux (10 Mo maximum)")
    if _famille(contenu) != EXTENSIONS[extension]:
        raise HTTPException(
            status_code=400, detail="Le contenu du fichier ne correspond pas à son extension"
        )

    dossier = _dossier_base() / "rapports" / str(rapport.id)
    dossier.mkdir(parents=True, exist_ok=True)
    nom_stockage = f"{uuid.uuid4().hex}{extension}"
    chemin = dossier / nom_stockage
    chemin.write_bytes(contenu)

    piece = PieceJointe(
        id_rapport=rapport.id,
        id_mission_district=id_mission_district,
        type_piece=type_piece,
        nom_original=nom_original,
        chemin_stockage=f"rapports/{rapport.id}/{nom_stockage}",
        type_mime=MIMES[extension],
        taille=len(contenu),
        empreinte_sha256=hashlib.sha256(contenu).hexdigest(),
        legende=(legende or "").strip()[:255] or None,
        id_televerseur=current_user.id_utilisateur,
    )
    try:
        db.add(piece)
        if type_piece != "photo":
            _journaliser(db, current_user, "modification", request)
        rapport.date_modification = _maintenant()
        db.commit()
    except Exception:
        db.rollback()
        chemin.unlink(missing_ok=True)
        raise
    db.refresh(piece)
    return _piece_out(piece, nom_district, f"{current_user.prenom} {current_user.nom}")


@router.get(
    "/{id_rapport}/pieces/{id_piece}/fichier",
    dependencies=[Depends(require_role(*ROLES_LECTURE))],
)
def telecharger_piece(
    id_rapport: int,
    id_piece: int,
    request: Request,
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rapport = _charger(db, id_rapport)
    _verifier_lecture(rapport, current_user)
    piece = next((p for p in rapport.pieces if p.id == id_piece), None)
    if piece is None:
        raise HTTPException(status_code=404, detail="Pièce introuvable")
    chemin = _chemin_piece(piece)
    if not chemin.is_file():
        raise HTTPException(status_code=404, detail="Fichier introuvable sur le serveur")

    if piece.type_piece != "photo":
        _journaliser(db, current_user, "export", request)
        db.commit()

    return FileResponse(
        chemin,
        media_type=piece.type_mime,
        filename=piece.nom_original,
        content_disposition_type="inline" if piece.type_mime.startswith("image/") else "attachment",
        headers={"X-Content-Type-Options": "nosniff"},
    )


@router.delete(
    "/{id_rapport}/pieces/{id_piece}",
    status_code=204,
    dependencies=[Depends(require_role(*ROLES_REDACTION))],
)
def supprimer_piece(
    id_rapport: int,
    id_piece: int,
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rapport = _charger(db, id_rapport)
    _verifier_edition(rapport, current_user)
    piece = next((p for p in rapport.pieces if p.id == id_piece), None)
    if piece is None:
        raise HTTPException(status_code=404, detail="Pièce introuvable")

    chemin = _chemin_piece(piece)
    db.delete(piece)
    rapport.date_modification = _maintenant()
    db.commit()
    chemin.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Soumission et validation
# ---------------------------------------------------------------------------


@router.post(
    "/{id_rapport}/soumettre",
    response_model=RapportDetailOut,
    dependencies=[Depends(require_role(*ROLES_REDACTION))],
)
def soumettre_rapport(
    id_rapport: int,
    request: Request,
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rapport = _charger(db, id_rapport)
    _verifier_edition(rapport, current_user)

    detail = _detail(db, rapport, current_user)
    if not detail.completude.complet:
        morceaux = []
        if detail.completude.sections_manquantes:
            morceaux.append("sections à remplir : " + ", ".join(detail.completude.sections_manquantes))
        nb_manquants = sum(1 for e in detail.completude.elements if not e.ok)
        if nb_manquants:
            morceaux.append(f"{nb_manquants} pièce(s) requise(s) manquante(s)")
        raise HTTPException(status_code=400, detail="Le rapport est incomplet : " + " ; ".join(morceaux) + ".")

    rapport.statut = "soumis"
    rapport.date_soumission = _maintenant()
    rapport.date_modification = rapport.date_soumission
    rapport.commentaire_validation = None
    notifier_administrateurs(
        db,
        "rapport_soumis",
        f"{rapport.auteur.prenom} {rapport.auteur.nom} a soumis le rapport de l'{_libelle_axe(rapport)}. "
        "Il attend ta validation.",
        f"/rapports/{rapport.id}",
        sauf=current_user.id_utilisateur,
    )
    _journaliser(db, current_user, "modification", request)
    db.commit()
    return _detail(db, _charger(db, id_rapport), current_user)


@router.post(
    "/{id_rapport}/valider",
    response_model=RapportDetailOut,
    dependencies=[Depends(require_role("administrateur"))],
)
def valider_rapport(
    id_rapport: int,
    request: Request,
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rapport = _charger(db, id_rapport)
    if rapport.statut != "soumis":
        raise HTTPException(status_code=400, detail="Seul un rapport soumis peut être validé")
    if rapport.id_auteur == current_user.id_utilisateur:
        raise HTTPException(status_code=400, detail="Tu ne peux pas valider ton propre rapport")

    rapport.statut = "valide"
    rapport.id_validateur = current_user.id_utilisateur
    rapport.date_validation = _maintenant()
    rapport.commentaire_validation = None
    notifier(
        db,
        rapport.id_auteur,
        "rapport_valide",
        f"Ton rapport de l'{_libelle_axe(rapport)} a été validé. Tu peux télécharger le PDF.",
        f"/rapports/{rapport.id}",
    )
    _journaliser(db, current_user, "modification", request)
    db.commit()
    return _detail(db, _charger(db, id_rapport), current_user)


@router.post(
    "/{id_rapport}/demander-correction",
    response_model=RapportDetailOut,
    dependencies=[Depends(require_role("administrateur"))],
)
def demander_correction(
    id_rapport: int,
    payload: CorrectionIn,
    request: Request,
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rapport = _charger(db, id_rapport)
    if rapport.statut != "soumis":
        raise HTTPException(status_code=400, detail="Seul un rapport soumis peut être renvoyé")
    if rapport.id_auteur == current_user.id_utilisateur:
        raise HTTPException(status_code=400, detail="Tu ne peux pas traiter ton propre rapport")

    rapport.statut = "a_corriger"
    rapport.id_validateur = current_user.id_utilisateur
    rapport.date_validation = _maintenant()
    rapport.commentaire_validation = payload.commentaire.strip()
    notifier(
        db,
        rapport.id_auteur,
        "rapport_correction",
        f"Ton rapport de l'{_libelle_axe(rapport)} est renvoyé pour correction : "
        f"{rapport.commentaire_validation}",
        f"/rapports/{rapport.id}",
    )
    _journaliser(db, current_user, "modification", request)
    db.commit()
    return _detail(db, _charger(db, id_rapport), current_user)


# ---------------------------------------------------------------------------
# PDF du rapport validé
# ---------------------------------------------------------------------------


def _donnees_pdf(db: Session, rapport: RapportMission, detail: RapportDetailOut) -> dict:
    """Données du rapport au format attendu par app.core.pdf_rapport.construire_pdf."""
    donnees = detail.model_dump()

    # Le PDF attend les journées regroupées par district.
    journees: dict[int, list[dict]] = {d.id_mission_district: [] for d in detail.districts}
    for journee in donnees["journees"]:
        journees[journee["id_mission_district"]].append(journee)
    donnees["journees"] = journees

    pieces_par_id = {p.id: p for p in rapport.pieces}
    for piece in donnees["pieces"]:
        piece["chemin"] = None
        if piece["type_piece"] == "photo":
            try:
                chemin = _chemin_piece(pieces_par_id[piece["id"]])
                piece["chemin"] = chemin if chemin.is_file() else None
            except HTTPException:
                pass  # fichier introuvable : le PDF mentionnera « Image non disponible »

    donnees["service_auteur"] = rapport.auteur.service.nom_service
    return donnees


@router.get(
    "/{id_rapport}/pdf",
    dependencies=[Depends(require_role("chef_mission", "administrateur"))],
)
def telecharger_pdf(
    id_rapport: int,
    request: Request,
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """PDF du rapport, disponible seulement une fois validé (auteur et administrateur)."""
    rapport = _charger(db, id_rapport)
    _verifier_lecture(rapport, current_user)
    if rapport.statut != "valide":
        raise HTTPException(
            status_code=400,
            detail="Le PDF n'est disponible qu'après validation du rapport par l'administrateur",
        )

    detail = _detail(db, rapport, current_user)
    contenu = construire_pdf(_donnees_pdf(db, rapport, detail))

    _journaliser(db, current_user, "export", request)
    db.commit()

    numero = rapport.axe.numero_axe if rapport.axe.numero_axe is not None else rapport.axe_id
    return Response(
        content=contenu,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="rapport_mission_axe{numero}_{rapport.id}.pdf"',
            "X-Content-Type-Options": "nosniff",
        },
    )