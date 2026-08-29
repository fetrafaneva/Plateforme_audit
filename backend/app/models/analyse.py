from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProfilComportemental(Base):
    __tablename__ = "profils_comportementaux"

    id_profil: Mapped[int] = mapped_column(primary_key=True)
    id_utilisateur: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id_utilisateur"))
    periode_reference: Mapped[str] = mapped_column(String(20))  # ex. "2026-07"
    volume_moyen: Mapped[float] = mapped_column(Float)
    horaires_habituels: Mapped[str] = mapped_column(String(50))  # ex. "08:00-17:00"
    perimetre_habituel: Mapped[str] = mapped_column(String(255))  # zones/ressources habituelles
    date_calcul: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    utilisateur: Mapped["Utilisateur"] = relationship()


class ScoreAnomalie(Base):
    __tablename__ = "scores_anomalie"

    id_score: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_entree_journal: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("journal_acces.id_entree")
    )
    id_profil_reference: Mapped[int] = mapped_column(
        ForeignKey("profils_comportementaux.id_profil")
    )
    z_score: Mapped[float] = mapped_column(Float)
    methode_utilisee: Mapped[str] = mapped_column(String(50))  # z-score, carte-de-controle...
    date_calcul: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    entree_journal: Mapped["JournalAcces"] = relationship()
    profil_reference: Mapped["ProfilComportemental"] = relationship()