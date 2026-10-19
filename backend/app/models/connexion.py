from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EchecConnexion(Base):
    """Une tentative de connexion ratée (sert à bloquer les essais répétés)."""

    __tablename__ = "echecs_connexion"
    __table_args__ = (
        Index("ix_echecs_connexion_email_date", "email", "date_echec"),
        Index("ix_echecs_connexion_ip_date", "adresse_ip", "date_echec"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Adresse saisie, en minuscules, même si aucun compte ne la porte : un attaquant
    # qui essaie des adresses inconnues est ainsi bloqué comme les autres.
    email: Mapped[str] = mapped_column(String(150))
    adresse_ip: Mapped[str] = mapped_column(String(45))
    date_echec: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class DemandeMotDePasse(Base):
    """Demande de nouveau mot de passe, traitée par un administrateur.

    Statuts : en_attente -> traitee (mot de passe temporaire généré) ou rejetee.
    """

    __tablename__ = "demandes_mot_de_passe"

    id: Mapped[int] = mapped_column(primary_key=True)
    id_utilisateur: Mapped[int] = mapped_column(
        ForeignKey("utilisateurs.id_utilisateur"), index=True
    )
    motif: Mapped[str | None] = mapped_column(String(300))
    statut: Mapped[str] = mapped_column(String(20), default="en_attente")
    date_demande: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    id_traitant: Mapped[int | None] = mapped_column(ForeignKey("utilisateurs.id_utilisateur"))
    date_traitement: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    utilisateur: Mapped["Utilisateur"] = relationship(foreign_keys=[id_utilisateur])
    traitant: Mapped["Utilisateur | None"] = relationship(foreign_keys=[id_traitant])