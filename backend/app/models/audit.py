from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class JournalAcces(Base):
    __tablename__ = "journal_acces"

    id_entree: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_utilisateur: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id_utilisateur"))
    id_ressource: Mapped[int] = mapped_column(ForeignKey("ressources_sensibles.id_ressource"))
    type_action: Mapped[str] = mapped_column(String(30))  # consultation, modification, export
    horodatage: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    adresse_ip: Mapped[str] = mapped_column(String(45))
    # SHA-256 -> toujours 64 caractères hexadécimaux
    hash_entree: Mapped[str] = mapped_column(String(64), unique=True)
    hash_precedent: Mapped[str] = mapped_column(String(64))

    utilisateur: Mapped["Utilisateur"] = relationship()
    ressource: Mapped["RessourceSensible"] = relationship()