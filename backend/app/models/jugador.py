from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class Jugador(Base):

    __tablename__ = "Jugadores"

    jugador_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    puuid: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    riot_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    tag_line: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    region: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )

    fecha_ultima_actualizacion: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
    )

    estadisticas = relationship(
        "EstadisticaPartida",
        back_populates="jugador",
    )