from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    DECIMAL,
    ForeignKey,
    Index,
    Integer,
    String,
    NVARCHAR,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class EstadisticaPartida(Base):

    __tablename__ = "EstadisticasPartida"

    __table_args__ = (
        UniqueConstraint(
            "jugador_id",
            "partida_id",
            name="UQ_Estadistica_Jugador_Partida",
        ),
        Index(
            "IX_Estadisticas_jugador",
            "jugador_id",
        ),
    )

    estadistica_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    jugador_id: Mapped[int] = mapped_column(
        ForeignKey("Jugadores.jugador_id"),
        nullable=False,
    )

    partida_id: Mapped[int] = mapped_column(
        ForeignKey("Partidas.partida_id"),
        nullable=False,
    )

    campeon: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    rol: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    victoria: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    kills: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    deaths: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    assists: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    kda: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
        default=0,
    )

    cs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    cs_por_minuto: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
        default=0,
    )

    oro: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    oro_por_minuto: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
        default=0,
    )

    daño_campeones: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    daño_por_minuto: Mapped[Decimal] = mapped_column(
        DECIMAL(12, 2),
        nullable=False,
        default=0,
    )

    vision_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )

    # Todas las métricas de la partida, para reconstruir
    # el análisis sin volver a llamar a Riot.
    datos_json: Mapped[str | None] = mapped_column(
        NVARCHAR,
        nullable=True,
    )

    jugador = relationship(
        "Jugador",
        back_populates="estadisticas",
    )

    partida = relationship(
        "Partida",
        back_populates="estadisticas",
    )