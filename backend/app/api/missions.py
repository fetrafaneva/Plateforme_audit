from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.identity import Utilisateur  # à ajouter aux imports en haut du fichier


from app.api.deps import get_db, get_current_user, require_role
from app.models.missions import (
    Mission, Axe, Equipe, Participant, District, MissionDistrict,
    TypeActivite, Phase, Journee, Livrable, IndicateurPerformance,
)
from app.schemas.missions import (
    MissionCreate, MissionOut,
    AxeCreate, AxeOut,
    EquipeCreate, EquipeOut,
    ParticipantCreate, ParticipantOut,
    DistrictCreate, DistrictOut,
    MissionDistrictCreate, MissionDistrictOut,
    TypeActiviteCreate, TypeActiviteOut,
    PhaseCreate, PhaseOut,
    JourneeCreate, JourneeOut,
    LivrableCreate, LivrableOut,
    IndicateurPerformanceCreate, IndicateurPerformanceOut,
)

router = APIRouter(prefix="/missions", tags=["missions"])
axes_router = APIRouter(prefix="/axes", tags=["axes"])
equipes_router = APIRouter(prefix="/equipes", tags=["equipes"])
participants_router = APIRouter(prefix="/participants", tags=["participants"])
districts_router = APIRouter(prefix="/districts", tags=["districts"])
missions_districts_router = APIRouter(prefix="/missions-districts", tags=["missions-districts"])
types_activite_router = APIRouter(prefix="/types-activite", tags=["types-activite"])
phases_router = APIRouter(prefix="/phases", tags=["phases"])
journees_router = APIRouter(prefix="/journees", tags=["journees"])
livrables_router = APIRouter(prefix="/livrables", tags=["livrables"])
indicateurs_router = APIRouter(prefix="/indicateurs-performance", tags=["indicateurs-performance"])


# --- Missions ---

@router.post("/", response_model=MissionOut, dependencies=[Depends(require_role("chef_mission", "administrateur"))])
def creer_mission(payload: MissionCreate, db: Session = Depends(get_db)):
    mission = Mission(**payload.model_dump())
    db.add(mission)
    db.commit()
    db.refresh(mission)
    return mission


@router.get("/", response_model=list[MissionOut])
def lister_missions(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(Mission).all()


# --- Axes ---

@axes_router.post("/", response_model=AxeOut, dependencies=[Depends(require_role("chef_mission", "administrateur"))])
def creer_axe(payload: AxeCreate, db: Session = Depends(get_db)):
    if not db.query(Mission).filter(Mission.id == payload.mission_id).first():
        raise HTTPException(status_code=404, detail="Mission introuvable")
    axe = Axe(**payload.model_dump())
    db.add(axe)
    db.commit()
    db.refresh(axe)
    return axe


@axes_router.get("/", response_model=list[AxeOut])
def lister_axes(mission_id: int | None = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    query = db.query(Axe)
    if mission_id is not None:
        query = query.filter(Axe.mission_id == mission_id)
    return query.all()


# --- Équipes ---

@equipes_router.post("/", response_model=EquipeOut, dependencies=[Depends(require_role("chef_mission", "administrateur"))])
def creer_equipe(payload: EquipeCreate, db: Session = Depends(get_db)):
    if not db.query(Axe).filter(Axe.id == payload.axe_id).first():
        raise HTTPException(status_code=404, detail="Axe introuvable")
    equipe = Equipe(**payload.model_dump())
    db.add(equipe)
    db.commit()
    db.refresh(equipe)
    return equipe


@equipes_router.get("/", response_model=list[EquipeOut])
def lister_equipes(axe_id: int | None = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    query = db.query(Equipe)
    if axe_id is not None:
        query = query.filter(Equipe.axe_id == axe_id)
    return query.all()


# --- Participants ---

@participants_router.post("/", response_model=ParticipantOut, dependencies=[Depends(require_role("chef_mission", "administrateur"))])
def creer_participant(payload: ParticipantCreate, db: Session = Depends(get_db)):
    if not db.query(Equipe).filter(Equipe.id == payload.equipe_id).first():
        raise HTTPException(status_code=404, detail="Équipe introuvable")
    if payload.id_utilisateur is not None and not db.query(Utilisateur).filter(
        Utilisateur.id_utilisateur == payload.id_utilisateur
    ).first():
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    participant = Participant(**payload.model_dump())
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant


@participants_router.get("/", response_model=list[ParticipantOut])
def lister_participants(equipe_id: int | None = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    query = db.query(Participant)
    if equipe_id is not None:
        query = query.filter(Participant.equipe_id == equipe_id)
    return query.all()


# --- Districts (référentiel, administrateur seul) ---

@districts_router.post("/", response_model=DistrictOut, dependencies=[Depends(require_role("administrateur"))])
def creer_district(payload: DistrictCreate, db: Session = Depends(get_db)):
    district = District(**payload.model_dump())
    db.add(district)
    db.commit()
    db.refresh(district)
    return district


@districts_router.get("/", response_model=list[DistrictOut])
def lister_districts(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(District).all()


# --- Missions × Districts ---

@missions_districts_router.post("/", response_model=MissionDistrictOut, dependencies=[Depends(require_role("chef_mission", "administrateur"))])
def creer_mission_district(payload: MissionDistrictCreate, db: Session = Depends(get_db)):
    if not db.query(Axe).filter(Axe.id == payload.axe_id).first():
        raise HTTPException(status_code=404, detail="Axe introuvable")
    if not db.query(District).filter(District.id == payload.district_id).first():
        raise HTTPException(status_code=404, detail="District introuvable")
    md = MissionDistrict(**payload.model_dump())
    db.add(md)
    db.commit()
    db.refresh(md)
    return md


@missions_districts_router.get("/", response_model=list[MissionDistrictOut])
def lister_missions_districts(axe_id: int | None = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    query = db.query(MissionDistrict)
    if axe_id is not None:
        query = query.filter(MissionDistrict.axe_id == axe_id)
    return query.all()


@router.get("/{mission_id}", response_model=MissionOut)
def obtenir_mission(mission_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission introuvable")
    return mission

# --- Types d'activité (référentiel, administrateur seul) ---

@types_activite_router.post("/", response_model=TypeActiviteOut, dependencies=[Depends(require_role("administrateur"))])
def creer_type_activite(payload: TypeActiviteCreate, db: Session = Depends(get_db)):
    type_activite = TypeActivite(**payload.model_dump())
    db.add(type_activite)
    db.commit()
    db.refresh(type_activite)
    return type_activite


@types_activite_router.get("/", response_model=list[TypeActiviteOut])
def lister_types_activite(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(TypeActivite).all()


# --- Phases ---

@phases_router.post("/", response_model=PhaseOut, dependencies=[Depends(require_role("chef_mission", "administrateur"))])
def creer_phase(payload: PhaseCreate, db: Session = Depends(get_db)):
    if not db.query(MissionDistrict).filter(MissionDistrict.id == payload.mission_district_id).first():
        raise HTTPException(status_code=404, detail="MissionDistrict introuvable")
    if not db.query(TypeActivite).filter(TypeActivite.id == payload.type_activite_id).first():
        raise HTTPException(status_code=404, detail="Type d'activité introuvable")
    phase = Phase(**payload.model_dump())
    db.add(phase)
    db.commit()
    db.refresh(phase)
    return phase


@phases_router.get("/", response_model=list[PhaseOut])
def lister_phases(mission_district_id: int | None = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    query = db.query(Phase)
    if mission_district_id is not None:
        query = query.filter(Phase.mission_district_id == mission_district_id)
    return query.all()


# --- Journées (accessibles au technicien sur le terrain) ---

@journees_router.post("/", response_model=JourneeOut, dependencies=[Depends(require_role("technicien", "chef_mission", "administrateur"))])
def creer_journee(payload: JourneeCreate, db: Session = Depends(get_db)):
    if not db.query(MissionDistrict).filter(MissionDistrict.id == payload.mission_district_id).first():
        raise HTTPException(status_code=404, detail="MissionDistrict introuvable")
    journee = Journee(**payload.model_dump())
    db.add(journee)
    db.commit()
    db.refresh(journee)
    return journee


@journees_router.get("/", response_model=list[JourneeOut])
def lister_journees(mission_district_id: int | None = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    query = db.query(Journee)
    if mission_district_id is not None:
        query = query.filter(Journee.mission_district_id == mission_district_id)
    return query.all()


# --- Livrables (accessibles au technicien sur le terrain) ---

@livrables_router.post("/", response_model=LivrableOut, dependencies=[Depends(require_role("technicien", "chef_mission", "administrateur"))])
def creer_livrable(payload: LivrableCreate, db: Session = Depends(get_db)):
    if not db.query(Phase).filter(Phase.id == payload.phase_id).first():
        raise HTTPException(status_code=404, detail="Phase introuvable")
    livrable = Livrable(**payload.model_dump())
    db.add(livrable)
    db.commit()
    db.refresh(livrable)
    return livrable


@livrables_router.get("/", response_model=list[LivrableOut])
def lister_livrables(phase_id: int | None = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    query = db.query(Livrable)
    if phase_id is not None:
        query = query.filter(Livrable.phase_id == phase_id)
    return query.all()


# --- Indicateurs de performance ---

@indicateurs_router.post("/", response_model=IndicateurPerformanceOut, dependencies=[Depends(require_role("chef_mission", "administrateur"))])
def creer_indicateur(payload: IndicateurPerformanceCreate, db: Session = Depends(get_db)):
    if not db.query(Mission).filter(Mission.id == payload.mission_id).first():
        raise HTTPException(status_code=404, detail="Mission introuvable")
    indicateur = IndicateurPerformance(**payload.model_dump())
    db.add(indicateur)
    db.commit()
    db.refresh(indicateur)
    return indicateur


@indicateurs_router.get("/", response_model=list[IndicateurPerformanceOut])
def lister_indicateurs(mission_id: int | None = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    query = db.query(IndicateurPerformance)
    if mission_id is not None:
        query = query.filter(IndicateurPerformance.mission_id == mission_id)
    return query.all()