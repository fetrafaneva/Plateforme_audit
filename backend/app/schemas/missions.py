from datetime import datetime, date as date_type
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
    id_utilisateur: int | None = None


class ParticipantOut(ParticipantCreate):
    id: int

    class Config:
        from_attributes = True

class MissionDistrictCreate(BaseModel):
    axe_id: int
    district_id: int
    ordre_visite: int | None = None


class MissionDistrictOut(MissionDistrictCreate):
    id: int
    statut: str

    class Config:
        from_attributes = True


class TypeActiviteCreate(BaseModel):
    libelle: str


class TypeActiviteOut(TypeActiviteCreate):
    id: int

    class Config:
        from_attributes = True


class PhaseCreate(BaseModel):
    mission_district_id: int
    type_activite_id: int
    numero_ordre: int | None = None
    duree_prevue: str | None = None
    livrable_attendu: str | None = None


class PhaseOut(PhaseCreate):
    id: int
    statut: str

    class Config:
        from_attributes = True


class JourneeCreate(BaseModel):
    mission_district_id: int
    numero_jour: int | None = None
    date: date_type | None = None
    lieu: str | None = None


class JourneeOut(JourneeCreate):
    id: int
    statut: str

    class Config:
        from_attributes = True


class LivrableCreate(BaseModel):
    phase_id: int
    type_livrable: str | None = None
    date_production: datetime | None = None
    signe: bool = False
    fichier: str | None = None


class LivrableOut(LivrableCreate):
    id: int

    class Config:
        from_attributes = True


class IndicateurPerformanceCreate(BaseModel):
    mission_id: int
    resultat_attendu: str | None = None
    indicateur_mesure: str | None = None
    cible: str | None = None
    valeur_realisee: str | None = None


class IndicateurPerformanceOut(IndicateurPerformanceCreate):
    id: int

    class Config:
        from_attributes = True