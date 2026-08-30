from datetime import datetime

from pydantic import BaseModel


class JournalEntryCreate(BaseModel):
    id_ressource: int
    type_action: str  # consultation, modification, export
    adresse_ip: str


class JournalEntryOut(BaseModel):
    id_entree: int
    id_utilisateur: int
    id_ressource: int
    type_action: str
    horodatage: datetime
    adresse_ip: str
    hash_entree: str
    hash_precedent: str

    class Config:
        from_attributes = True


class VerificationResult(BaseModel):
    intact: bool
    nb_entrees_verifiees: int
    premiere_entree_corrompue: int | None = None