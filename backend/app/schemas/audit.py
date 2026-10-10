from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ResumeAudit(BaseModel):
    nb_entrees_journal: int
    nb_utilisateurs_surveilles: int
    nb_scores: int
    nb_alertes_nouvelles: int
    nb_alertes_critiques_ouvertes: int
    nb_investigations_ouvertes: int


class JournalLigneOut(BaseModel):
    id_entree: int
    id_utilisateur: int
    nom_utilisateur: str
    id_ressource: int
    type_ressource: str
    type_action: str
    horodatage: datetime
    adresse_ip: str
    hash_entree: str
    hash_precedent: str


class ScoreLigneOut(BaseModel):
    id_score: int
    id_entree_journal: int
    id_utilisateur: int
    nom_utilisateur: str
    type_action: str
    horodatage: datetime
    z_score: float
    methode_utilisee: str
    date_calcul: datetime


class AlerteOut(BaseModel):
    id_alerte: int
    id_score: int
    niveau_gravite: str
    statut: str
    date_creation: datetime
    id_utilisateur: int
    nom_utilisateur: str
    z_score: float
    horodatage: datetime
    nom_politique: str


StatutAlerte = Literal["nouvelle", "en_investigation", "traitee", "fausse_alerte"]


class AlerteUpdate(BaseModel):
    statut: StatutAlerte


class InvestigationOut(BaseModel):
    id_investigation: int
    id_alerte: int
    id_enqueteur: int
    nom_enqueteur: str
    statut: str
    conclusion: str | None
    date_ouverture: datetime
    date_cloture: datetime | None
    niveau_gravite: str
    id_utilisateur: int
    nom_utilisateur: str


class InvestigationCloture(BaseModel):
    conclusion: str = Field(min_length=1, max_length=500)


class ProfilLigneOut(BaseModel):
    id_profil: int
    id_utilisateur: int
    nom_utilisateur: str
    periode_reference: str
    volume_moyen: float
    horaires_habituels: str
    perimetre_habituel: str
    date_calcul: datetime
    missions: list[str] = Field(default_factory=list)


class RessourceOut(BaseModel):
    id_ressource: int
    type_ressource: str
    niveau_sensibilite: str
    id_service_proprietaire: int
    nb_acces: int


class ParticipationOut(BaseModel):
    id_participant: int
    id_mission: int
    titre_mission: str
    statut_mission: str
    type_equipe: str | None
    numero_axe: int | None
    fonction: str | None


class FicheUtilisateurOut(BaseModel):
    id_utilisateur: int
    nom: str
    prenom: str
    email: str
    matricule: str
    statut: str
    role: str
    service: str
    nb_acces: int
    profil: ProfilLigneOut | None
    participations: list[ParticipationOut]
    alertes: list[AlerteOut]