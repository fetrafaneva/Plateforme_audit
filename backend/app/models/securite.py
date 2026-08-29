from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PolitiqueConformite(Base):
    __tablename__ = "politiques_conformite"

    id_politique: Mapped[int] = mapped_column(primary_key=True)
    nom_politique: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(255))
    seuils_configures: Mapped[str] = mapped_column(String(255))  # JSON sérialisé, ex. seuil z-score
    date_effective: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AlerteSecurite(Base):
    __tablename__ = "alertes_securite"

    id_alerte: Mapped[int] = mapped_column(primary_key=True)
    id_score: Mapped[int] = mapped_column(BigInteger, ForeignKey("scores_anomalie.id_score"))
    id_politique: Mapped[int] = mapped_column(ForeignKey("politiques_conformite.id_politique"))
    niveau_gravite: Mapped[str] = mapped_column(String(20))  # faible, moyen, critique
    statut: Mapped[str] = mapped_column(String(20), default="nouvelle")
    date_creation: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    score: Mapped["ScoreAnomalie"] = relationship()
    politique: Mapped["PolitiqueConformite"] = relationship()


class Investigation(Base):
    __tablename__ = "investigations"

    id_investigation: Mapped[int] = mapped_column(primary_key=True)
    id_alerte: Mapped[int] = mapped_column(ForeignKey("alertes_securite.id_alerte"))
    id_enqueteur: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id_utilisateur"))
    statut: Mapped[str] = mapped_column(String(20), default="ouverte")
    conclusion: Mapped[str | None] = mapped_column(String(500))
    date_ouverture: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    date_cloture: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    alerte: Mapped["AlerteSecurite"] = relationship()
    enqueteur: Mapped["Utilisateur"] = relationship()