from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class District(Base):
    __tablename__ = "districts"
    id = Column(Integer, primary_key=True)
    nom = Column(String, nullable=False)
    region = Column(String)
    province = Column(String)
    electrifie = Column(Boolean, default=False)


class Mission(Base):
    __tablename__ = "missions"
    id = Column(Integer, primary_key=True)
    titre = Column(String, nullable=False)
    type_mission = Column(String)
    date_debut = Column(DateTime)
    date_fin_prevue = Column(DateTime)
    statut = Column(String, default="planifiee")

    axes = relationship("Axe", back_populates="mission")
    indicateurs = relationship("IndicateurPerformance", back_populates="mission")


class Axe(Base):
    __tablename__ = "axes"
    id = Column(Integer, primary_key=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=False)
    numero_axe = Column(Integer)
    itineraire_principal = Column(String)

    mission = relationship("Mission", back_populates="axes")
    districts = relationship("MissionDistrict", back_populates="axe")
    equipes = relationship("Equipe", back_populates="axe")


class MissionDistrict(Base):
    __tablename__ = "missions_districts"
    id = Column(Integer, primary_key=True)
    axe_id = Column(Integer, ForeignKey("axes.id"), nullable=False)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False)
    ordre_visite = Column(Integer)
    statut = Column(String, default="a_planifier")

    axe = relationship("Axe", back_populates="districts")
    district = relationship("District")
    phases = relationship("Phase", back_populates="mission_district")
    journees = relationship("Journee", back_populates="mission_district")


class Equipe(Base):
    __tablename__ = "equipes"
    id = Column(Integer, primary_key=True)
    axe_id = Column(Integer, ForeignKey("axes.id"), nullable=False)
    type_equipe = Column(String)

    axe = relationship("Axe", back_populates="equipes")
    participants = relationship("Participant", back_populates="equipe")


class Participant(Base):
    __tablename__ = "participants"
    id = Column(Integer, primary_key=True)
    equipe_id = Column(Integer, ForeignKey("equipes.id"), nullable=False)
    nom = Column(String, nullable=False)
    fonction = Column(String)
    id_utilisateur = Column(Integer, ForeignKey("utilisateurs.id_utilisateur"), nullable=True)

    equipe = relationship("Equipe", back_populates="participants")
    utilisateur = relationship("Utilisateur", back_populates="participations")

class TypeActivite(Base):
    __tablename__ = "types_activite"
    id = Column(Integer, primary_key=True)
    libelle = Column(String, nullable=False)  # ex: "Installation serveur", "Formation SII CSB"

    phases = relationship("Phase", back_populates="type_activite")


class Phase(Base):
    __tablename__ = "phases"
    id = Column(Integer, primary_key=True)
    mission_district_id = Column(Integer, ForeignKey("missions_districts.id"), nullable=False)
    type_activite_id = Column(Integer, ForeignKey("types_activite.id"), nullable=False)
    numero_ordre = Column(Integer)
    duree_prevue = Column(String)  # ex: "J1-J2"
    livrable_attendu = Column(String)
    statut = Column(String, default="a_faire")

    mission_district = relationship("MissionDistrict", back_populates="phases")
    type_activite = relationship("TypeActivite", back_populates="phases")
    livrables = relationship("Livrable", back_populates="phase")


class Journee(Base):
    __tablename__ = "journees"
    id = Column(Integer, primary_key=True)
    mission_district_id = Column(Integer, ForeignKey("missions_districts.id"), nullable=False)
    numero_jour = Column(Integer)
    date = Column(Date)
    lieu = Column(String)
    statut = Column(String, default="prevue")

    mission_district = relationship("MissionDistrict", back_populates="journees")


class Livrable(Base):
    __tablename__ = "livrables"
    id = Column(Integer, primary_key=True)
    phase_id = Column(Integer, ForeignKey("phases.id"), nullable=False)
    type_livrable = Column(String)
    date_production = Column(DateTime)
    signe = Column(Boolean, default=False)
    fichier = Column(String)

    phase = relationship("Phase", back_populates="livrables")


class IndicateurPerformance(Base):
    __tablename__ = "indicateurs_performance"
    id = Column(Integer, primary_key=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=False)
    resultat_attendu = Column(String)
    indicateur_mesure = Column(String)
    cible = Column(String)
    valeur_realisee = Column(String)

    mission = relationship("Mission", back_populates="indicateurs")