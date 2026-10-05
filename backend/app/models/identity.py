from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Role(Base):
    __tablename__ = "roles_permissions"

    id_role: Mapped[int] = mapped_column(primary_key=True)
    nom_role: Mapped[str] = mapped_column(String(50), unique=True)
    # agent, auditeur, responsable_hierarchique, administrateur
    niveau_acces: Mapped[str] = mapped_column(String(20))

    utilisateurs: Mapped[list["Utilisateur"]] = relationship(back_populates="role")


class ServiceCommune(Base):
    __tablename__ = "services_communes"

    id_service: Mapped[int] = mapped_column(primary_key=True)
    nom_service: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(30))  # commune, district, ministere
    id_service_parent: Mapped[int | None] = mapped_column(
        ForeignKey("services_communes.id_service")
    )

    parent: Mapped["ServiceCommune | None"] = relationship(remote_side=[id_service])
    utilisateurs: Mapped[list["Utilisateur"]] = relationship(back_populates="service")


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id_utilisateur: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100))
    prenom: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    matricule: Mapped[str] = mapped_column(String(30), unique=True)
    mot_de_passe_hash: Mapped[str] = mapped_column(String(255))
    id_service: Mapped[int] = mapped_column(ForeignKey("services_communes.id_service"))
    participations: Mapped[list["Participant"]] = relationship(back_populates="utilisateur")
    id_role: Mapped[int] = mapped_column(ForeignKey("roles_permissions.id_role"))
    statut: Mapped[str] = mapped_column(String(20), default="actif")
    date_creation: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    service: Mapped["ServiceCommune"] = relationship(back_populates="utilisateurs")
    role: Mapped["Role"] = relationship(back_populates="utilisateurs")