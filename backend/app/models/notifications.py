from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Notification(Base):
    """Message adressé à un utilisateur (ex. « ton rapport a été validé »)."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    id_utilisateur: Mapped[int] = mapped_column(
        ForeignKey("utilisateurs.id_utilisateur"), index=True
    )  # destinataire
    type_notification: Mapped[str] = mapped_column(String(40))
    message: Mapped[str] = mapped_column(String(500))
    lien: Mapped[str | None] = mapped_column(String(255))  # page de l'application à ouvrir
    lue: Mapped[bool] = mapped_column(Boolean, default=False)
    date_creation: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    destinataire: Mapped["Utilisateur"] = relationship()