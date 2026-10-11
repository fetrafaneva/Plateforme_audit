from datetime import datetime

from pydantic import BaseModel


class AgentRisqueOut(BaseModel):
    rang: int
    id_utilisateur: int
    nom_utilisateur: str
    role: str
    service: str
    nb_acces: int
    nb_alertes: int
    nb_alertes_critiques: int
    points_risque: int
    niveau_risque: str  # aucun | modere | eleve
    nb_missions: int
    derniere_alerte: datetime | None


class ServiceRisqueOut(BaseModel):
    rang: int
    id_service: int
    nom_service: str
    type: str
    nb_agents: int
    nb_alertes: int
    score_risque_moyen: float


class AlerteServiceOut(BaseModel):
    id_alerte: int
    id_utilisateur: int
    nom_utilisateur: str
    niveau_gravite: str
    statut: str
    horodatage: datetime
    z_score: float


class MonServiceOut(BaseModel):
    id_service: int
    nom_service: str
    type: str
    jours: int
    nb_agents: int
    nb_alertes: int
    score_risque_moyen: float
    agents: list[AgentRisqueOut]
    services: list[ServiceRisqueOut]
    alertes_recentes: list[AlerteServiceOut]