from typing import Literal

from pydantic import BaseModel


class UtilisateurResume(BaseModel):
    """Informations minimales pour choisir un compte (ex. lier un participant).

    Ni email ni mot de passe : seulement ce qui permet de distinguer deux homonymes.
    """

    id_utilisateur: int
    nom: str
    prenom: str
    matricule: str
    role: str


class RoleOut(BaseModel):
    id_role: int
    nom_role: str


class ServiceOut(BaseModel):
    id_service: int
    nom_service: str
    type: str


class CompteOut(BaseModel):
    id_utilisateur: int
    nom: str
    prenom: str
    email: str
    matricule: str
    role: str
    service: str
    statut: str


class StatutCompteUpdate(BaseModel):
    statut: Literal["actif", "inactif"]