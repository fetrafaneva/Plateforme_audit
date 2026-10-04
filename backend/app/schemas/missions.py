from datetime import datetime
from pydantic import BaseModel


class MissionCreate(BaseModel):
    titre: str
    type_mission: str | None = None
    date_debut: datetime | None = None
    date_fin_prevue: datetime | None = None


class MissionOut(MissionCreate):
    id: int
    statut: str

    class Config:
        from_attributes = True


class DistrictCreate(BaseModel):
    nom: str
    region: str | None = None
    province: str | None = None
    electrifie: bool = False


class DistrictOut(DistrictCreate):
    id: int

    class Config:
        from_attributes = True


class AxeCreate(BaseModel):
    mission_id: int
    numero_axe: int | None = None
    itineraire_principal: str | None = None


class AxeOut(AxeCreate):
    id: int

    class Config:
        from_attributes = True


class EquipeCreate(BaseModel):
    axe_id: int
    type_equipe: str | None = None


class EquipeOut(EquipeCreate):
    id: int

    class Config:
        from_attributes = True


class ParticipantCreate(BaseModel):
    equipe_id: int
    nom: str
    fonction: str | None = None


class ParticipantOut(ParticipantCreate):
    id: int

    class Config:
        from_attributes = True