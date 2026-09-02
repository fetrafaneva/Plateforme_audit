from datetime import datetime

from pydantic import BaseModel


class ProfilOut(BaseModel):
    id_profil: int
    id_utilisateur: int
    periode_reference: str
    volume_moyen: float
    horaires_habituels: str
    perimetre_habituel: str
    date_calcul: datetime

    class Config:
        from_attributes = True


class ScoreOut(BaseModel):
    id_score: int
    id_entree_journal: int
    id_profil_reference: int
    z_score: float
    methode_utilisee: str
    date_calcul: datetime

    class Config:
        from_attributes = True