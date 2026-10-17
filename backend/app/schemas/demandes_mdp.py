from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class DemandePubliqueIn(BaseModel):
    email: EmailStr
    matricule: str = Field(min_length=1, max_length=30)
    motif: str | None = Field(default=None, max_length=300)


class DemandeMoiIn(BaseModel):
    motif: str | None = Field(default=None, max_length=300)


class AccuseOut(BaseModel):
    message: str


class DemandeOut(BaseModel):
    id: int
    id_utilisateur: int
    nom_utilisateur: str
    email: str
    matricule: str
    role: str
    motif: str | None
    statut: str
    date_demande: datetime
    nom_traitant: str | None
    date_traitement: datetime | None


class MotDePasseTemporaireOut(BaseModel):
    mot_de_passe_temporaire: str