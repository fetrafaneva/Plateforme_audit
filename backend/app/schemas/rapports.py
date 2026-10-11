from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

TypePiece = Literal["fiche_reception", "fiche_presence", "photo", "fiche_evaluation", "autre"]


def _texte():
    return Field(default=None, max_length=20000)


class DifficulteIn(BaseModel):
    categorie: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=2000)
    solution: str | None = Field(default=None, max_length=2000)


class DifficulteOut(DifficulteIn):
    id: int


class RapportCreate(BaseModel):
    axe_id: int


class RapportUpdate(BaseModel):
    contexte: str | None = _texte()
    justification: str | None = _texte()
    itineraire_reel: str | None = _texte()
    inventaire_materiel: str | None = _texte()
    configuration_technique: str | None = _texte()
    tests_securite: str | None = _texte()
    nb_participants_formes: int | None = Field(default=None, ge=0, le=100000)
    profil_participants: str | None = Field(default=None, max_length=255)
    themes_formation: str | None = _texte()
    evaluation_formation: str | None = _texte()
    points_forts: str | None = _texte()
    lecons_apprises: str | None = _texte()
    bonnes_pratiques: str | None = _texte()
    conclusion: str | None = _texte()
    recommandations: str | None = _texte()


class CorrectionIn(BaseModel):
    commentaire: str = Field(min_length=1, max_length=1000)


class PieceOut(BaseModel):
    id: int
    type_piece: str
    nom_original: str
    type_mime: str
    taille: int
    legende: str | None
    id_mission_district: int | None
    nom_district: str | None
    nom_televerseur: str
    date_depot: datetime
    empreinte_sha256: str


class ElementCompletude(BaseModel):
    code: str
    libelle: str
    district: str | None
    requis: int
    fourni: int
    ok: bool


class CompletudeOut(BaseModel):
    complet: bool
    elements: list[ElementCompletude]
    sections_manquantes: list[str]


class MembreOut(BaseModel):
    nom: str
    fonction: str | None
    equipe: str | None


class DistrictRapportOut(BaseModel):
    id_mission_district: int
    nom: str
    statut: str


class ResultatOut(BaseModel):
    resultat_attendu: str | None
    indicateur_mesure: str | None
    cible: str | None
    realise: str | None
    taux: float | None


class AxeDisponibleOut(BaseModel):
    id_axe: int
    numero_axe: int | None
    id_mission: int
    titre_mission: str


class RapportResume(BaseModel):
    id: int
    id_axe: int
    numero_axe: int | None
    id_mission: int
    titre_mission: str
    auteur: str
    statut: str
    nb_pieces: int
    date_soumission: datetime | None
    date_modification: datetime


class RapportDetailOut(BaseModel):
    id: int
    statut: str
    modifiable: bool
    peut_valider: bool
    peut_telecharger_pdf: bool

    id_axe: int
    numero_axe: int | None
    id_mission: int
    titre_mission: str
    type_mission: str | None
    periode_debut: date | None
    periode_fin: date | None
    districts: list[DistrictRapportOut]
    membres: list[MembreOut]
    resultats: list[ResultatOut]

    id_auteur: int
    auteur: str

    contexte: str | None
    justification: str | None
    itineraire_reel: str | None
    inventaire_materiel: str | None
    configuration_technique: str | None
    tests_securite: str | None
    nb_participants_formes: int | None
    profil_participants: str | None
    themes_formation: str | None
    evaluation_formation: str | None
    points_forts: str | None
    lecons_apprises: str | None
    bonnes_pratiques: str | None
    conclusion: str | None
    recommandations: str | None

    difficultes: list[DifficulteOut]
    pieces: list[PieceOut]
    completude: CompletudeOut

    date_creation: datetime
    date_modification: datetime
    date_soumission: datetime | None
    date_validation: datetime | None
    nom_validateur: str | None
    commentaire_validation: str | None