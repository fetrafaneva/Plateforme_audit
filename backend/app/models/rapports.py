from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RapportMission(Base):
    """Rapport de fin de mission d'un axe, rédigé par le chef d'équipe.

    Statuts : brouillon -> soumis -> valide, ou soumis -> a_corriger -> soumis.
    """

    __tablename__ = "rapports_mission"
    __table_args__ = (UniqueConstraint("axe_id", name="uq_rapports_mission_axe"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    axe_id: Mapped[int] = mapped_column(ForeignKey("axes.id"))
    id_auteur: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id_utilisateur"))
    statut: Mapped[str] = mapped_column(String(20), default="brouillon")

    # 1-2. Contexte et justification
    contexte: Mapped[str | None] = mapped_column(Text)
    justification: Mapped[str | None] = mapped_column(Text)
    # 3.1 Itinéraire réel
    itineraire_reel: Mapped[str | None] = mapped_column(Text)
    # 3.2 Travaux techniques
    inventaire_materiel: Mapped[str | None] = mapped_column(Text)
    configuration_technique: Mapped[str | None] = mapped_column(Text)
    tests_securite: Mapped[str | None] = mapped_column(Text)
    # 3.3 Formations
    nb_participants_formes: Mapped[int | None] = mapped_column(Integer)
    profil_participants: Mapped[str | None] = mapped_column(String(255))
    themes_formation: Mapped[str | None] = mapped_column(Text)
    evaluation_formation: Mapped[str | None] = mapped_column(Text)
    # 6. Bilan
    points_forts: Mapped[str | None] = mapped_column(Text)
    lecons_apprises: Mapped[str | None] = mapped_column(Text)
    bonnes_pratiques: Mapped[str | None] = mapped_column(Text)
    # 7. Conclusion et recommandations (une recommandation par ligne)
    conclusion: Mapped[str | None] = mapped_column(Text)
    recommandations: Mapped[str | None] = mapped_column(Text)

    date_creation: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    date_modification: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    date_soumission: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    id_validateur: Mapped[int | None] = mapped_column(ForeignKey("utilisateurs.id_utilisateur"))
    date_validation: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    commentaire_validation: Mapped[str | None] = mapped_column(Text)

    axe: Mapped["Axe"] = relationship()
    auteur: Mapped["Utilisateur"] = relationship(foreign_keys=[id_auteur])
    validateur: Mapped["Utilisateur | None"] = relationship(foreign_keys=[id_validateur])
    difficultes: Mapped[list["RapportDifficulte"]] = relationship(
        back_populates="rapport", cascade="all, delete-orphan", order_by="RapportDifficulte.id"
    )
    pieces: Mapped[list["PieceJointe"]] = relationship(
        back_populates="rapport", cascade="all, delete-orphan", order_by="PieceJointe.id"
    )


class RapportDifficulte(Base):
    """Section 5 : une difficulté rencontrée et la solution apportée."""

    __tablename__ = "rapport_difficultes"

    id: Mapped[int] = mapped_column(primary_key=True)
    id_rapport: Mapped[int] = mapped_column(ForeignKey("rapports_mission.id"))
    categorie: Mapped[str] = mapped_column(String(100))  # ex. Électricité, Logiciel
    description: Mapped[str] = mapped_column(Text)
    solution: Mapped[str | None] = mapped_column(Text)

    rapport: Mapped["RapportMission"] = relationship(back_populates="difficultes")


class PieceJointe(Base):
    """Annexe du rapport : fiche signée, fiche de présence, photo, etc.

    Le fichier est stocké sur disque (settings.uploads_dir) ; la base garde ses
    métadonnées et son empreinte SHA-256 pour détecter une altération.
    """

    __tablename__ = "pieces_jointes"

    id: Mapped[int] = mapped_column(primary_key=True)
    id_rapport: Mapped[int] = mapped_column(ForeignKey("rapports_mission.id"))
    id_mission_district: Mapped[int | None] = mapped_column(ForeignKey("missions_districts.id"))
    type_piece: Mapped[str] = mapped_column(String(30))
    nom_original: Mapped[str] = mapped_column(String(255))
    chemin_stockage: Mapped[str] = mapped_column(String(500))
    type_mime: Mapped[str] = mapped_column(String(100))
    taille: Mapped[int] = mapped_column(Integer)
    empreinte_sha256: Mapped[str] = mapped_column(String(64))
    legende: Mapped[str | None] = mapped_column(String(255))
    id_televerseur: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id_utilisateur"))
    date_depot: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    rapport: Mapped["RapportMission"] = relationship(back_populates="pieces")
    mission_district: Mapped["MissionDistrict | None"] = relationship()
    televerseur: Mapped["Utilisateur"] = relationship()