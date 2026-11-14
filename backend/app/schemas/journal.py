from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class JournalEntryCreate(BaseModel):
    """Corps de POST /journal/acces.

    Pas d'adresse IP ici : le serveur la relève lui-même sur la connexion. Si un ancien
    client en envoie encore une, elle est ignorée.
    """

    id_ressource: int
    type_action: Literal["consultation", "modification", "export"]


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