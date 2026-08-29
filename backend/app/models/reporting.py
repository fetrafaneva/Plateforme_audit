from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RapportAudit(Base):
    __tablename__ = "rapports_audit"

    id_rapport: Mapped[int] = mapped_column(primary_key=True)
    id_service: Mapped[int | None] = mapped_column(ForeignKey("services_communes.id_service"))
    periode_couverte: Mapped[str] = mapped_column(String(20))
    contenu: Mapped[str] = mapped_column(Text)  # synthèse/texte du rapport
    date_generation: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    service: Mapped["ServiceCommune | None"] = relationship()


class BenchmarkingService(Base):
    __tablename__ = "benchmarking_services"

    id_benchmark: Mapped[int] = mapped_column(primary_key=True)
    id_service: Mapped[int] = mapped_column(ForeignKey("services_communes.id_service"))
    periode: Mapped[str] = mapped_column(String(20))
    score_risque_moyen: Mapped[float] = mapped_column(Float)
    rang: Mapped[int | None] = mapped_column(Integer)
    date_calcul: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    service: Mapped["ServiceCommune"] = relationship()