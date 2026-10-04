from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.missions import Mission, Axe, Equipe, Participant, District
from app.schemas.missions import (
    MissionCreate, MissionOut,
    AxeCreate, AxeOut,
    EquipeCreate, EquipeOut,
    ParticipantCreate, ParticipantOut,
    DistrictCreate, DistrictOut,
)

router = APIRouter(prefix="/missions", tags=["missions"])
axes_router = APIRouter(prefix="/axes", tags=["axes"])
equipes_router = APIRouter(prefix="/equipes", tags=["equipes"])
participants_router = APIRouter(prefix="/participants", tags=["participants"])
districts_router = APIRouter(prefix="/districts", tags=["districts"])


# --- Missions ---

@router.post("/", response_model=MissionOut)
def creer_mission(payload: MissionCreate, db: Session = Depends(get_db)):
    mission = Mission(**payload.model_dump())
    db.add(mission)
    db.commit()
    db.refresh(mission)
    return mission


@router.get("/", response_model=list[MissionOut])
def lister_missions(db: Session = Depends(get_db)):
    return db.query(Mission).all()


# --- Axes ---

@axes_router.post("/", response_model=AxeOut)
def creer_axe(payload: AxeCreate, db: Session = Depends(get_db)):
    if not db.query(Mission).filter(Mission.id == payload.mission_id).first():
        raise HTTPException(status_code=404, detail="Mission introuvable")
    axe = Axe(**payload.model_dump())
    db.add(axe)
    db.commit()
    db.refresh(axe)
    return axe


@axes_router.get("/", response_model=list[AxeOut])
def lister_axes(mission_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Axe)
    if mission_id is not None:
        query = query.filter(Axe.mission_id == mission_id)
    return query.all()


# --- Équipes ---

@equipes_router.post("/", response_model=EquipeOut)
def creer_equipe(payload: EquipeCreate, db: Session = Depends(get_db)):
    if not db.query(Axe).filter(Axe.id == payload.axe_id).first():
        raise HTTPException(status_code=404, detail="Axe introuvable")
    equipe = Equipe(**payload.model_dump())
    db.add(equipe)
    db.commit()
    db.refresh(equipe)
    return equipe


@equipes_router.get("/", response_model=list[EquipeOut])
def lister_equipes(axe_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Equipe)
    if axe_id is not None:
        query = query.filter(Equipe.axe_id == axe_id)
    return query.all()


# --- Participants ---

@participants_router.post("/", response_model=ParticipantOut)
def creer_participant(payload: ParticipantCreate, db: Session = Depends(get_db)):
    if not db.query(Equipe).filter(Equipe.id == payload.equipe_id).first():
        raise HTTPException(status_code=404, detail="Équipe introuvable")
    participant = Participant(**payload.model_dump())
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant


@participants_router.get("/", response_model=list[ParticipantOut])
def lister_participants(equipe_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Participant)
    if equipe_id is not None:
        query = query.filter(Participant.equipe_id == equipe_id)
    return query.all()


# --- Districts (référentiel indépendant) ---

@districts_router.post("/", response_model=DistrictOut)
def creer_district(payload: DistrictCreate, db: Session = Depends(get_db)):
    district = District(**payload.model_dump())
    db.add(district)
    db.commit()
    db.refresh(district)
    return district


@districts_router.get("/", response_model=list[DistrictOut])
def lister_districts(db: Session = Depends(get_db)):
    return db.query(District).all()