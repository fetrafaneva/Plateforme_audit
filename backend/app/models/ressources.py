from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RessourceSensible(Base):
    __tablename__ = "ressources_sensibles"

    id_ressource: Mapped[int] = mapped_column(primary_key=True)
    type_ressource: Mapped[str] = mapped_column(String(100))  # dossier identite, etat civil...
    niveau_sensibilite: Mapped[str] = mapped_column(String(20))
    id_service_proprietaire: Mapped[int] = mapped_column(
        ForeignKey("services_communes.id_service")
    )

    service_proprietaire: Mapped["ServiceCommune"] = relationship()