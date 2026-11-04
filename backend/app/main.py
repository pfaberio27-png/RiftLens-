from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.app.services.riot_service import (
    PartidaRemakeException,
    RiotRateLimitException,
    obtener_cuenta_por_riot_id,
    obtener_detalle_partida,
    obtener_estadisticas_ultimas_partidas,
    obtener_rango_jugador,
    validar_jugador_en_region,
)

from backend.app.services.analisis_service import (
    analizar_jugador_con_referencia,
)


# ============================================================
# REGIONES SOPORTADAS
# ============================================================

REGIONES_SOPORTADAS = {
    "BR",
    "LAN",
    "LAS",
    "NA",
    "EUW",
    "EUNE",
    "TR",
    "RU",
    "KR",
    "JP",
    "OCE",
    "PH",
    "SG",
    "TH",
    "TW",
    "VN",
}


# ============================================================
# MODELOS
# ============================================================

class AnalisisJugadorRequest(BaseModel):

    riot_id: str = Field(
        ...,
        min_length=3,
        description="Riot ID del jugador en formato Nombre#TAG",
        examples=["Faker#KR1"],
    )

    region: str = Field(
        default="LAS",
        min_length=2,
        max_length=4,
        description="Región/plataforma del jugador",
        examples=["KR"],
    )


# ============================================================
# CONFIGURACIÓN FASTAPI
# ============================================================

app = FastAPI(
    title="Sistema de Análisis de Rendimiento LOL",
    description=(
        "API para analizar el rendimiento individual de jugadores "
        "de League of Legends y compararlo contra referencias "
        "profesionales obtenidas de Oracle's Elixir."
    ),
    version="2.1.0",
)


# ============================================================
# CONFIGURACIÓN CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://rift-lens-eta.vercel.app",
        "https://riftlensnuevo.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def validar_riot_id(
    riot_id: str,
):
    """
    Valida un Riot ID y devuelve game_name y tag_line.
    """

    riot_id = riot_id.strip()

    if "#" not in riot_id:
        raise HTTPException(
            status_code=400,
            detail=(
                "El Riot ID debe tener el formato Nombre#TAG."
            ),
        )

    game_name, tag_line = riot_id.split(
        "#",
        1,
    )

    game_name = game_name.strip()
    tag_line = tag_line.strip()

    if not game_name or not tag_line:
        raise HTTPException(
            status_code=400,
            detail=(
                "El Riot ID no puede contener campos vacíos."
            ),
        )

    return game_name, tag_line


def validar_region(
    region: str,
):
    """
    Valida y normaliza la región enviada por el cliente.
    """

    region_normalizada = (
        region
        .strip()
        .upper()
    )

    if region_normalizada not in REGIONES_SOPORTADAS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Región no soportada: {region}. "
                f"Regiones disponibles: "
                f"{', '.join(sorted(REGIONES_SOPORTADAS))}."
            ),
        )

    return region_normalizada


def manejar_rate_limit(
    error: RiotRateLimitException,
):
    """
    Convierte la excepción de rate limit de Riot
    en una respuesta HTTP 429.
    """

    detail = error.mensaje

    if error.retry_after:
        detail += (
            f" Espera aproximadamente "
            f"{error.retry_after} segundos "
            f"antes de volver a intentarlo."
        )

    raise HTTPException(
        status_code=429,
        detail=detail,
    )


# ============================================================
# ENDPOINT PRINCIPAL
# ============================================================

@app.get("/")
def inicio():

    return {
        "mensaje": (
            "API del Sistema de Análisis de Rendimiento LOL "
            "funcionando correctamente"
        ),
        "version": "2.1.0",
        "modelo_analisis": (
            "Jugador individual vs referencia profesional por rol"
        ),
        "multirregion": True,
        "regiones_soportadas": sorted(
            REGIONES_SOPORTADAS
        ),
    }


# ============================================================
# DETALLE DE UNA PARTIDA (10 PARTICIPANTES)
# ============================================================

@app.get("/api/partida/{match_id}")
def detalle_partida(

    match_id: str,

    puuid: str = Query(
        ...,
        min_length=1,
        description=(
            "PUUID del jugador; define aliados y rivales"
        ),
    ),

    region: str = Query(
        "LAS",
        description=(
            "Región a la que pertenece la partida"
        ),
    ),
):

    try:

        region = validar_region(
            region
        )

        return obtener_detalle_partida(
            match_id=match_id,
            puuid=puuid,
            region=region,
        )

    except HTTPException:
        raise

    except PartidaRemakeException as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        )

    except RiotRateLimitException as error:
        manejar_rate_limit(
            error
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(
                error
            ),
        )


# ============================================================
# ENDPOINT PRINCIPAL DE ANÁLISIS
# ============================================================

@app.post("/api/analisis")
def analizar_jugador(
    solicitud: AnalisisJugadorRequest,
):

    try:

        # ====================================================
        # VALIDAR DATOS
        # ====================================================

        game_name, tag_line = validar_riot_id(
            solicitud.riot_id
        )

        region = validar_region(
            solicitud.region
        )


        # ====================================================
        # OBTENER CUENTA RIOT
        # ====================================================

        cuenta = obtener_cuenta_por_riot_id(
            game_name=game_name,
            tag_line=tag_line,
            region=region,
        )

        puuid = cuenta.get(
            "puuid"
        )

        if not puuid:

            raise HTTPException(
                status_code=404,
                detail=(
                    "No se pudo obtener el PUUID "
                    "del jugador."
                ),
            )


        # ====================================================
        # VALIDAR PLATAFORMA DEL JUGADOR
        # ====================================================

        jugador_en_region = validar_jugador_en_region(
            puuid=puuid,
            region=region,
        )

        if not jugador_en_region:

            raise HTTPException(
                status_code=404,
                detail=(
                    f" El jugador "
                    f"no pertenece a la región {region}. "
                    "Selecciona la región correcta."
                ),
            )


        # ====================================================
        # DATOS DEL JUGADOR
        # ====================================================

        nombre = cuenta.get(
            "gameName",
            game_name,
        )

        tag = cuenta.get(
            "tagLine",
            tag_line,
        )


        # ====================================================
        # OBTENER RANGO
        # ====================================================

        rango = obtener_rango_jugador(
            puuid=puuid,
            region=region,
        )


        # ====================================================
        # OBTENER PARTIDAS RANKED SOLO/DÚO DE LA TEMPORADA
        # ====================================================

        resultado_partidas = (
            obtener_estadisticas_ultimas_partidas(
                puuid=puuid,
                region=region,
                count=100,
            )
        )

        partidas = resultado_partidas["partidas"]

        carga = resultado_partidas["carga"]


        # ====================================================
        # VALIDAR PARTIDAS
        # ====================================================

        partidas_validas = [
            partida
            for partida in partidas
            if (
                isinstance(
                    partida,
                    dict,
                )
                and
                "error" not in partida
                and
                partida.get(
                    "partida"
                )
            )
        ]

        partidas_remake = sum(
            1
            for partida in partidas_validas
            if partida.get("remake")
        )

        if len(partidas_validas) == partidas_remake:

            # Si todas fallaron por el límite de Riot,
            # se informa como 429 y no como "sin partidas".
            limite = next(
                (
                    partida
                    for partida in partidas
                    if "retry_after" in partida
                ),
                None,
            )

            if limite:

                raise RiotRateLimitException(
                    limite["error"],
                    limite["retry_after"],
                )

            raise HTTPException(
                status_code=404,
                detail=(
                    "Este jugador no tiene partidas "
                    "clasificatorias Solo/Dúo en la "
                    "temporada actual."
                ),
            )


        # ====================================================
        # EJECUTAR ANÁLISIS COMPLETO
        # ====================================================

        analisis = (
            analizar_jugador_con_referencia(
                partidas=partidas_validas,
                puuid=puuid,
                nombre=nombre,
                tag=tag,
                rango=rango,
            )
        )

        return {
            "mensaje": (
                "Análisis de rendimiento realizado "
                "correctamente"
            ),
            "riot_id": (
                f"{nombre}#{tag}"
            ),
            "region": region,
            "partidas_validas": (
                len(partidas_validas)
                - partidas_remake
            ),
            "partidas_remake": partidas_remake,
            "carga": carga,
            "analisis": analisis,
        }


    except HTTPException:

        raise


    except RiotRateLimitException as error:

        manejar_rate_limit(
            error
        )


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(
                error
            ),
        )