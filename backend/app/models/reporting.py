from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RapportAudit(Base):
    """Synthèse d'audit d'un service pour une période, générée depuis le benchmark.

    Une ligne par service et par période : le recalcul d'une période remplace
    les synthèses existantes (cf. app.core.benchmarking.generer_rapports_audit).
    """

    __tablename__ = "rapports_audit"
    __table_args__ = (
        UniqueConstraint(
            "id_service", "periode_couverte", name="uq_rapports_audit_service_periode"
        ),
    )

    id_rapport: Mapped[int] = mapped_column(primary_key=True)
    id_service: Mapped[int | None] = mapped_column(
        ForeignKey("services_communes.id_service")
    )
    periode_couverte: Mapped[str] = mapped_column(String(20))
    contenu: Mapped[str] = mapped_column(Text)  # synthèse/texte du rapport
    date_generation: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    service: Mapped["ServiceCommune | None"] = relationship()


class BenchmarkingService(Base):
    """Photographie du risque d'accès d'un service sur une période (un mois).

    Deux indicateurs, calculés sur la même fenêtre :
      - `taux_alertes` : nombre d'alertes retenues pour 100 accès journalisés.
        Normalisé par le volume, pour qu'un gros district ne paraisse pas
        mécaniquement plus risqué qu'une petite commune.
      - `score_risque_moyen` : moyenne des |z-score| des accès effectivement
        analysés. `nb_scores` dit sur combien d'accès cette moyenne est calculée
        (tous les accès ne sont pas scorés), sans quoi la moyenne n'est pas
        interprétable.

    `rang` : 1 = service le plus risqué de son type (commune, district...).
    Reste à NULL quand le service n'a pas assez d'accès sur la période pour être
    classé honnêtement (cf. MIN_ACCES_CLASSEMENT).
    """

    __tablename__ = "benchmarking_services"
    __table_args__ = (
        UniqueConstraint(
            "id_service", "periode", name="uq_benchmarking_services_service_periode"
        ),
    )

    id_benchmark: Mapped[int] = mapped_column(primary_key=True)
    id_service: Mapped[int] = mapped_column(
        ForeignKey("services_communes.id_service")
    )
    periode: Mapped[str] = mapped_column(String(20), index=True)  # ex. "2026-11"
    nb_agents: Mapped[int] = mapped_column(Integer, default=0)
    nb_acces: Mapped[int] = mapped_column(Integer, default=0)
    nb_scores: Mapped[int] = mapped_column(Integer, default=0)
    nb_alertes: Mapped[int] = mapped_column(Integer, default=0)
    nb_alertes_critiques: Mapped[int] = mapped_column(Integer, default=0)
    taux_alertes: Mapped[float] = mapped_column(Float, default=0.0)
    score_risque_moyen: Mapped[float] = mapped_column(Float)
    rang: Mapped[int | None] = mapped_column(Integer)
    date_calcul: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    service: Mapped["ServiceCommune"] = relationship()
