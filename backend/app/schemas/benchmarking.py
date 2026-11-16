from datetime import datetime

from pydantic import BaseModel


class LigneBenchmarkOut(BaseModel):
    id_benchmark: int
    id_service: int
    nom_service: str
    type: str
    periode: str
    nb_agents: int
    nb_acces: int
    nb_scores: int
    nb_alertes: int
    nb_alertes_critiques: int
    taux_alertes: float  # alertes retenues pour 100 accès
    score_risque_moyen: float  # moyenne des |z-score| sur nb_scores accès
    rang: int | None  # None = pas assez d'accès pour être classé
    date_calcul: datetime


class ReperesTypeOut(BaseModel):
    """Repères d'un type de service, calculés sur les services classés."""

    type: str
    nb_services_classes: int
    taux_median: float
    taux_moyen: float
    score_median: float
    score_moyen: float


class ClassementOut(BaseModel):
    periode: str
    min_acces_classement: int
    nb_services: int
    nb_services_classes: int
    lignes: list[LigneBenchmarkOut]
    reperes: list[ReperesTypeOut]
    message: str | None = None  # ex. « aucune période calculée »


class CalculOut(ClassementOut):
    nb_rapports_generes: int


class PeriodeOut(BaseModel):
    periode: str
    nb_services: int
    date_calcul: datetime


class RapportAuditOut(BaseModel):
    id_rapport: int
    id_service: int | None
    nom_service: str
    periode_couverte: str
    contenu: str
    date_generation: datetime


class MonBenchmarkOut(BaseModel):
    """Vue d'un responsable : son service, ses sous-services, et les repères de son type.

    Les autres services ne sont pas nommés : le responsable se situe par rapport
    à la médiane et à la moyenne de son type, pas par rapport à des voisins
    identifiables.
    """

    periode: str
    min_acces_classement: int
    service: LigneBenchmarkOut | None
    reperes: ReperesTypeOut | None
    sous_services: list[LigneBenchmarkOut]
    historique: list[LigneBenchmarkOut]
    rapport: RapportAuditOut | None
    message: str | None  # ex. « aucun calcul pour cette période »
