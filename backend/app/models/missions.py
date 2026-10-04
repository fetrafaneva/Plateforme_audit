from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
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

    equipe = relationship("Equipe", back_populates="participants")

