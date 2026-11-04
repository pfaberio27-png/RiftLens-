from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    Integer,
    String,
    NVARCHAR,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class Partida(Base):

    __tablename__ = "Partidas"

    __table_args__ = (
        Index(
            "IX_Partidas_fecha",
            "fecha_partida",
        ),
    )

    partida_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    match_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
    )

    queue_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    modo: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    duracion_segundos: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    fecha_partida: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )

    es_remake: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )

    version_parche: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    # Los 10 participantes con ítems (sin dividir por equipo).
    equipos_json: Mapped[str | None] = mapped_column(
        NVARCHAR,
        nullable=True,
    )

    estadisticas = relationship(
        "EstadisticaPartida",
        back_populates="partida",
    )