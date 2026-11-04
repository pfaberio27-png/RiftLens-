import json

from datetime import datetime

from sqlalchemy import select

from backend.app.database import (
    DB_ENABLED,
    SessionLocal,
)

from backend.app.models import (
    EstadisticaPartida,
    Jugador,
    Partida,
)


# ============================================================
# AUXILIAR - TIMESTAMP RIOT → DATETIME
# ============================================================

def convertir_timestamp_riot(timestamp):

    if not timestamp:
        return None

    try:
        return datetime.fromtimestamp(
            timestamp / 1000
        )

    except (TypeError, ValueError, OSError):
        return None


# ============================================================
# AUXILIAR - EQUIPOS ↔ PARTICIPANTES
# ============================================================
#
# Partidas.equipos_json guarda los 10 participantes (y los
# objetivos por team_id) sin
# dividir en aliados/rivales, porque una misma partida
# puede pertenecer a varios jugadores consultados.
# La división se reconstruye para el jugador que consulta.

def equipos_a_participantes(equipos):

    participantes = []

    for participante in (
        equipos.get("aliados", [])
        +
        equipos.get("rivales", [])
    ):

        participantes.append({
            clave: valor
            for clave, valor in participante.items()
            if clave != "es_jugador"
        })

    return participantes


def reconstruir_equipos(
    participantes: list,
    puuid: str
):

    team_id_jugador = next(
        (
            participante.get("team_id")
            for participante in participantes
            if participante.get("puuid") == puuid
        ),
        None
    )

    equipos = {
        "aliados": [],
        "rivales": [],
    }

    for participante in participantes:

        detalle = {
            **participante,
            "es_jugador":
                participante.get("puuid") == puuid,
        }

        if participante.get("team_id") == team_id_jugador:
            equipos["aliados"].append(detalle)

        else:
            equipos["rivales"].append(detalle)

    return equipos


def leer_contenido_equipos_json(equipos_json):
    """
    Devuelve (participantes, objetivos) de Partidas.equipos_json.

    Formato antiguo: lista de participantes (sin objetivos).
    Formato actual: {"participantes": [...], "objetivos": {...}}.
    Los objetivos se guardan por team_id ("100" / "200").
    Si el contenido no es válido devuelve (None, None).
    """

    try:
        contenido = json.loads(equipos_json)

    except (TypeError, ValueError):
        return None, None

    if isinstance(contenido, list):
        return contenido, None

    if isinstance(contenido, dict):
        return (
            contenido.get("participantes") or [],
            contenido.get("objetivos") or None,
        )

    return None, None


def crear_equipos_json(participantes, objetivos):

    return json.dumps(
        {
            "participantes": participantes,
            "objetivos": objetivos,
        },
        ensure_ascii=False,
    )


def bd_disponible():

    return DB_ENABLED and SessionLocal is not None


# ============================================================
# LEER PARTIDAS GUARDADAS DE UN JUGADOR
# ============================================================

def leer_partidas_jugador(
    puuid: str,
    match_ids: list,
):
    """
    Devuelve {match_id: estadisticas} con las partidas del
    jugador que ya están en SQL Server, con el mismo formato
    que extraer_estadisticas_jugador().

    Las filas antiguas sin datos_json o equipos_json no se
    devuelven: se descargarán de nuevo y se actualizarán.
    """

    if not bd_disponible() or not match_ids:
        return {}

    db = SessionLocal()

    try:

        filas = db.execute(
            select(
                Partida.match_id,
                Partida.es_remake,
                Partida.equipos_json,
                EstadisticaPartida.datos_json,
            )
            .join(
                EstadisticaPartida,
                EstadisticaPartida.partida_id
                ==
                Partida.partida_id,
            )
            .join(
                Jugador,
                Jugador.jugador_id
                ==
                EstadisticaPartida.jugador_id,
            )
            .where(
                Jugador.puuid == puuid,
                Partida.match_id.in_(match_ids),
            )
        ).all()

        partidas = {}

        for match_id, es_remake, equipos_json, datos_json in filas:

            if not datos_json or not equipos_json:
                continue

            try:
                datos = json.loads(datos_json)

            except (TypeError, ValueError):
                continue

            participantes, _ = leer_contenido_equipos_json(
                equipos_json
            )

            if participantes is None:
                continue

            datos["remake"] = bool(es_remake)

            datos["equipos"] = reconstruir_equipos(
                participantes,
                puuid,
            )

            partidas[match_id] = datos

        return partidas

    finally:

        db.close()


# ============================================================
# LEER EQUIPOS DE UNA PARTIDA
# ============================================================

def leer_equipos_partida(
    match_id: str,
    puuid: str,
):
    """
    Devuelve el detalle guardado de una partida desde
    Partidas.equipos_json, o None si la partida no está
    guardada o no contiene al jugador:

    {"remake", "duracion_segundos", "game_creation",
     "version_parche", "participantes", "objetivos"}

    "objetivos" es None si la fila tiene el formato antiguo.
    """

    if not bd_disponible():
        return None

    db = SessionLocal()

    try:

        partida = db.scalar(
            select(Partida).where(
                Partida.match_id == match_id
            )
        )

        if partida is None or not partida.equipos_json:
            return None

        participantes, objetivos = leer_contenido_equipos_json(
            partida.equipos_json
        )

        if not participantes or not any(
            participante.get("puuid") == puuid
            for participante in participantes
        ):
            return None

        game_creation = None

        if partida.fecha_partida is not None:

            try:
                game_creation = int(
                    partida.fecha_partida.timestamp() * 1000
                )

            except (OverflowError, OSError, ValueError):
                game_creation = None

        return {
            "remake": bool(partida.es_remake),
            "duracion_segundos": partida.duracion_segundos,
            "game_creation": game_creation,
            "version_parche": partida.version_parche,
            "participantes": participantes,
            "objetivos": objetivos,
        }

    finally:

        db.close()


# ============================================================
# GUARDAR OBJETIVOS DE UNA PARTIDA YA REGISTRADA
# ============================================================

def guardar_objetivos_partida(
    match_id: str,
    participantes: list,
    objetivos: dict,
):
    """
    Reescribe Partidas.equipos_json con el formato actual
    (participantes + objetivos). Devuelve True si se guardó.
    """

    if not bd_disponible():
        return False

    db = SessionLocal()

    try:

        partida = db.scalar(
            select(Partida).where(
                Partida.match_id == match_id
            )
        )

        if partida is None:
            return False

        partida.equipos_json = crear_equipos_json(
            participantes,
            objetivos,
        )

        db.commit()

        return True

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


# ============================================================
# GUARDAR PARTIDAS EN SQL SERVER
# ============================================================

def guardar_partidas_sql(
    puuid: str,
    region: str,
    partidas: list,
):
    """
    Persiste en SQL Server, en una sola transacción, el
    jugador y las partidas descargadas de Riot.

    - Partida nueva → INSERT en Partidas.
    - Partida existente → UPDATE de es_remake,
      version_parche y equipos_json.
    - Estadística nueva → INSERT con datos_json.
    - Estadística existente sin datos_json → UPDATE de
      datos_json (filas guardadas antes de esta versión).
    """

    if not bd_disponible():

        return {
            "habilitado": False,
            "jugador_nuevo": False,
            "partidas_nuevas": 0,
            "estadisticas_nuevas": 0,
            "actualizadas": 0,
            "omitidas": 0,
        }

    resumen = {
        "jugador_nuevo": False,
        "partidas_nuevas": 0,
        "estadisticas_nuevas": 0,
        "actualizadas": 0,
        "omitidas": 0,
    }

    partidas_validas = [
        partida
        for partida in partidas
        if (
            isinstance(partida, dict)
            and
            "error" not in partida
            and
            partida.get("jugador")
            and
            partida.get("partida", {}).get("match_id")
        )
    ]

    if not partidas_validas:
        return resumen

    db = SessionLocal()

    try:

        # ====================================================
        # JUGADOR
        # ====================================================

        datos_jugador = partidas_validas[0].get(
            "jugador",
            {},
        )

        nombre = (
            datos_jugador.get("nombre")
            or "Desconocido"
        )

        tag = (
            datos_jugador.get("tag")
            or "UNKNOWN"
        )

        jugador = db.scalar(
            select(Jugador).where(
                Jugador.puuid == puuid
            )
        )

        if jugador is None:

            jugador = Jugador(
                puuid=puuid,
                riot_name=nombre,
                tag_line=tag,
                region=region.upper(),
            )

            db.add(jugador)

            # Necesitamos jugador_id antes de continuar.
            db.flush()

            resumen["jugador_nuevo"] = True

        else:

            jugador.riot_name = nombre
            jugador.tag_line = tag
            jugador.region = region.upper()
            jugador.fecha_ultima_actualizacion = (
                datetime.now()
            )


        # ====================================================
        # PARTIDAS Y ESTADÍSTICAS YA GUARDADAS
        # ====================================================

        match_ids = [
            datos["partida"]["match_id"]
            for datos in partidas_validas
        ]

        partidas_existentes = {
            partida.match_id: partida
            for partida in db.scalars(
                select(Partida).where(
                    Partida.match_id.in_(match_ids)
                )
            )
        }

        estadisticas_existentes = {
            estadistica.partida_id: estadistica
            for estadistica in db.scalars(
                select(EstadisticaPartida).where(
                    EstadisticaPartida.jugador_id
                    ==
                    jugador.jugador_id
                )
            )
        }


        for datos in partidas_validas:

            datos_partida = datos.get(
                "partida",
                {},
            )

            match_id = datos_partida["match_id"]

            es_remake = bool(
                datos.get("remake", False)
            )

            version_parche = (
                (datos_partida.get("version_parche") or "")[:20]
                or None
            )

            equipos_json = crear_equipos_json(
                equipos_a_participantes(
                    datos.get("equipos", {})
                ),
                datos.get("objetivos"),
            )

            # Equipos y objetivos ya van en Partidas.equipos_json.
            datos_json = json.dumps(
                {
                    clave: valor
                    for clave, valor in datos.items()
                    if clave not in ("equipos", "objetivos")
                },
                ensure_ascii=False,
            )


            # ================================================
            # PARTIDA
            # ================================================

            partida_db = partidas_existentes.get(
                match_id
            )

            if partida_db is None:

                partida_db = Partida(
                    match_id=match_id,
                    queue_id=datos_partida.get(
                        "queue_id"
                    ),
                    modo=datos_partida.get(
                        "modo"
                    ),
                    duracion_segundos=datos_partida.get(
                        "duracion_segundos"
                    ),
                    fecha_partida=convertir_timestamp_riot(
                        datos_partida.get(
                            "game_creation"
                        )
                    ),
                    es_remake=es_remake,
                    version_parche=version_parche,
                    equipos_json=equipos_json,
                )

                db.add(partida_db)

                db.flush()

                partidas_existentes[match_id] = partida_db

                resumen["partidas_nuevas"] += 1

            else:

                partida_db.es_remake = es_remake
                partida_db.version_parche = version_parche
                partida_db.equipos_json = equipos_json


            # ================================================
            # ESTADÍSTICA
            # ================================================

            estadistica_existente = (
                estadisticas_existentes.get(
                    partida_db.partida_id
                )
            )

            if estadistica_existente is not None:

                if estadistica_existente.datos_json:

                    resumen["omitidas"] += 1

                else:

                    estadistica_existente.datos_json = (
                        datos_json
                    )

                    resumen["actualizadas"] += 1

                continue


            resultado = datos.get("resultado", {})
            campeon = datos.get("campeon", {})
            combate = datos.get("combate", {})
            farmeo = datos.get("farmeo", {})
            economia = datos.get("economia", {})
            daño = datos.get("daño", {})
            vision = datos.get("vision", {})

            estadistica = EstadisticaPartida(

                jugador_id=
                    jugador.jugador_id,

                partida_id=
                    partida_db.partida_id,

                campeon=
                    campeon.get("nombre"),

                rol=
                    datos_partida.get(
                        "posicion"
                    ),

                victoria=
                    bool(
                        resultado.get(
                            "victoria",
                            False,
                        )
                    ),

                kills=
                    int(combate.get("kills", 0) or 0),

                deaths=
                    int(combate.get("muertes", 0) or 0),

                assists=
                    int(combate.get("asistencias", 0) or 0),

                kda=
                    float(combate.get("kda", 0) or 0),

                cs=
                    int(farmeo.get("cs", 0) or 0),

                cs_por_minuto=
                    float(farmeo.get("cs_por_minuto", 0) or 0),

                oro=
                    int(economia.get("oro", 0) or 0),

                oro_por_minuto=
                    float(economia.get("oro_por_minuto", 0) or 0),

                daño_campeones=
                    int(daño.get("daño_campeones", 0) or 0),

                daño_por_minuto=
                    float(daño.get("daño_por_minuto", 0) or 0),

                vision_score=
                    int(vision.get("vision_score", 0) or 0),

                datos_json=
                    datos_json,
            )

            db.add(estadistica)

            estadisticas_existentes[
                partida_db.partida_id
            ] = estadistica

            resumen["estadisticas_nuevas"] += 1


        # ====================================================
        # CONFIRMAR TRANSACCIÓN
        # ====================================================

        db.commit()

        return resumen


    except Exception:

        db.rollback()

        raise


    finally:

        db.close()
