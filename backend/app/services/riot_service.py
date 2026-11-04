import os
import json
import tempfile
import threading
import time

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from dotenv import load_dotenv


from backend.app.database import DB_ENABLED

from backend.app.services.persistencia_service import (
    equipos_a_participantes,
    guardar_objetivos_partida,
    guardar_partidas_sql,
    leer_equipos_partida,
    leer_partidas_jugador,
    reconstruir_equipos,
)

from backend.app.services.riot_cliente import (
    RiotRateLimitException,
    riot_get,
)

load_dotenv("backend/.env")

RIOT_API_KEY = os.getenv("RIOT_API_KEY")


# ============================================================
# PARTIDAS A ANALIZAR
# ============================================================

COLA_RANKED_SOLO_DUO = 420

MAXIMO_PARTIDAS = 100

HILOS_DESCARGA = 8

DURACION_MINIMA_SEGUNDOS = 300

TEMPORADA_INICIO_POR_DEFECTO = "2026-01-08"


def obtener_inicio_temporada():
    """
    Convierte TEMPORADA_INICIO (AAAA-MM-DD, UTC) en
    segundos epoch para el parámetro startTime de Match-V5.
    """

    texto = (
        os.getenv(
            "TEMPORADA_INICIO",
            TEMPORADA_INICIO_POR_DEFECTO
        )
        .strip()
    )

    try:

        fecha = datetime.strptime(
            texto,
            "%Y-%m-%d"
        )

    except ValueError:

        print(
            "TEMPORADA_INICIO inválida, se usa",
            TEMPORADA_INICIO_POR_DEFECTO,
            ":",
            texto
        )

        fecha = datetime.strptime(
            TEMPORADA_INICIO_POR_DEFECTO,
            "%Y-%m-%d"
        )

    return int(
        fecha
        .replace(tzinfo=timezone.utc)
        .timestamp()
    )


INICIO_TEMPORADA = obtener_inicio_temporada()


# ============================================================
# CONFIGURACIÓN DE REGIONES RIOT
# ============================================================

PLATAFORMAS_RIOT = {

    "BR": {
        "plataforma": "br1",
        "routing": "americas",
    },

    "LAN": {
        "plataforma": "la1",
        "routing": "americas",
    },

    "LAS": {
        "plataforma": "la2",
        "routing": "americas",
    },

    "NA": {
        "plataforma": "na1",
        "routing": "americas",
    },


    "EUW": {
        "plataforma": "euw1",
        "routing": "europe",
    },

    "EUNE": {
        "plataforma": "eun1",
        "routing": "europe",
    },

    "TR": {
        "plataforma": "tr1",
        "routing": "europe",
    },

    "RU": {
        "plataforma": "ru",
        "routing": "europe",
    },


    "KR": {
        "plataforma": "kr",
        "routing": "asia",
    },

    "JP": {
        "plataforma": "jp1",
        "routing": "asia",
    },


    "OCE": {
        "plataforma": "oc1",
        "routing": "sea",
    },

    "PH": {
        "plataforma": "ph2",
        "routing": "sea",
    },

    "SG": {
        "plataforma": "sg2",
        "routing": "sea",
    },

    "TH": {
        "plataforma": "th2",
        "routing": "sea",
    },

    "TW": {
        "plataforma": "tw2",
        "routing": "sea",
    },

    "VN": {
        "plataforma": "vn2",
        "routing": "sea",
    },
}


# ============================================================
# ARCHIVO LOCAL DE PARTIDAS
# ============================================================

RUTA_PARTIDAS = os.path.join(
    os.path.dirname(
        os.path.dirname(__file__)
    ),
    "data",
    "partidas.json"
)


# ============================================================
# CONFIGURACIÓN DE REGIÓN
# ============================================================

def obtener_configuracion_region(
    region: str
):

    region_normalizada = (
        region
        .strip()
        .upper()
    )

    configuracion = (
        PLATAFORMAS_RIOT.get(
            region_normalizada
        )
    )

    if not configuracion:

        raise Exception(
            f"Región no soportada: {region}"
        )

    return configuracion


def obtener_url_regional(
    region: str
):

    configuracion = (
        obtener_configuracion_region(
            region
        )
    )

    routing = (
        configuracion[
            "routing"
        ]
    )

    return (
        f"https://{routing}.api.riotgames.com"
    )


def obtener_url_plataforma(
    region: str
):

    configuracion = (
        obtener_configuracion_region(
            region
        )
    )

    plataforma = (
        configuracion[
            "plataforma"
        ]
    )

    return (
        f"https://{plataforma}.api.riotgames.com"
    )


# ============================================================
# FUNCIONES DE CACHÉ
# ============================================================

def cargar_partidas_guardadas():

    if not os.path.exists(
        RUTA_PARTIDAS
    ):

        return {
            "jugadores": {}
        }

    try:

        with open(
            RUTA_PARTIDAS,
            "r",
            encoding="utf-8"
        ) as archivo:

            return json.load(
                archivo
            )

    except json.JSONDecodeError:

        return {
            "jugadores": {}
        }


# Evita que dos peticiones escriban partidas.json a la vez.
BLOQUEO_PARTIDAS_JSON = threading.Lock()


def guardar_partidas_guardadas(
    datos
):
    """
    Escritura segura: se escribe un archivo temporal en la
    misma carpeta y luego se reemplaza partidas.json, para no
    dejar la caché a medias si el proceso se interrumpe.
    """

    carpeta = os.path.dirname(
        RUTA_PARTIDAS
    )

    os.makedirs(
        carpeta,
        exist_ok=True
    )

    with BLOQUEO_PARTIDAS_JSON:

        descriptor, ruta_temporal = tempfile.mkstemp(
            prefix="partidas_",
            suffix=".tmp",
            dir=carpeta
        )

        try:

            with os.fdopen(
                descriptor,
                "w",
                encoding="utf-8"
            ) as archivo:

                json.dump(
                    datos,
                    archivo,
                    ensure_ascii=False,
                    indent=4
                )

                archivo.flush()

                os.fsync(
                    archivo.fileno()
                )

            # OneDrive o el antivirus pueden bloquear el archivo
            # un instante: se reintenta el reemplazo.
            for intento in range(5):

                try:

                    os.replace(
                        ruta_temporal,
                        RUTA_PARTIDAS
                    )

                    break

                except PermissionError:

                    if intento == 4:
                        raise

                    time.sleep(0.2)

        finally:

            if os.path.exists(
                ruta_temporal
            ):

                os.remove(
                    ruta_temporal
                )


# ============================================================
# FUNCIÓN AUXILIAR PARA VALIDAR API KEY
# ============================================================

def validar_api_key():

    if not RIOT_API_KEY:

        raise Exception(
            "No se encontró RIOT_API_KEY en el archivo .env"
        )


def solicitar_riot(
    url: str,
    params=None,
    timeout=10
):
    """
    GET a Riot API mediante el cliente compartido
    (sesión, limitador y reintentos ante 429).
    """

    validar_api_key()

    return riot_get(
        url,
        RIOT_API_KEY,
        params=params,
        timeout=timeout
    )


# ============================================================
# 1. OBTENER CUENTA POR RIOT ID
# ============================================================

def obtener_cuenta_por_riot_id(
    game_name: str,
    tag_line: str,
    region: str
):

    validar_api_key()

    base_url = (
        obtener_url_regional(
            region
        )
    )

    url = (
        f"{base_url}"
        f"/riot/account/v1/accounts/by-riot-id/"
        f"{game_name}/{tag_line}"
    )

    response = solicitar_riot(
        url,
        timeout=10
    )

    if response.status_code == 200:

        return response.json()

    if response.status_code == 400:

        raise Exception(
            "Solicitud incorrecta a Riot API."
        )

    if response.status_code == 401:

        raise Exception(
            "API Key no autorizada."
        )

    if response.status_code == 403:

        raise Exception(
            "API Key inválida o expirada."
        )

    if response.status_code == 404:

        raise Exception(
            "No se encontró el jugador."
        )

    raise Exception(
        "Error de Riot API. "
        f"Código HTTP: {response.status_code}"
    )

# ============================================================
# VALIDAR JUGADOR EN PLATAFORMA SELECCIONADA
# ============================================================

def validar_jugador_en_region(
    puuid: str,
    region: str
):

    validar_api_key()

    base_url = (
        obtener_url_plataforma(
            region
        )
    )

    url = (
        f"{base_url}"
        f"/lol/summoner/v4/summoners/by-puuid/{puuid}"
    )

    response = solicitar_riot(
        url,
        timeout=10
    )

    if response.status_code == 200:

        return True


    if response.status_code == 404:

        return False


    if response.status_code == 401:

        raise Exception(
            "API Key no autorizada."
        )


    if response.status_code == 403:

        raise Exception(
            "API Key inválida o expirada."
        )


    raise Exception(
        "No se pudo validar la región del jugador. "
        f"Código HTTP: {response.status_code}"
    )

# ============================================================
# 2. OBTENER RANGO DEL JUGADOR
# ============================================================

def obtener_rango_jugador(
    puuid: str,
    region: str
):

    validar_api_key()

    base_url = (
        obtener_url_plataforma(
            region
        )
    )

    url = (
        f"{base_url}"
        f"/lol/league/v4/entries/by-puuid/{puuid}"
    )

    try:

        response = solicitar_riot(
            url,
            timeout=15
        )

        if response.status_code == 401:

            raise Exception(
                "API Key no autorizada."
            )

        if response.status_code == 403:

            raise Exception(
                "API Key inválida o expirada."
            )

        response.raise_for_status()

        ligas = response.json()

        solo_duo = next(
            (
                liga
                for liga in ligas
                if (
                    liga.get(
                        "queueType"
                    )
                    ==
                    "RANKED_SOLO_5x5"
                )
            ),
            None
        )

        if not solo_duo:

            return {
                "clasificado": False,
                "cola": "Solo/Duo",
                "tier": None,
                "division": None,
                "lp": 0,
                "victorias": 0,
                "derrotas": 0
            }

        return {
            "clasificado": True,
            "cola": "Solo/Duo",
            "tier":
                solo_duo.get(
                    "tier"
                ),
            "division":
                solo_duo.get(
                    "rank"
                ),
            "lp":
                solo_duo.get(
                    "leaguePoints",
                    0
                ),
            "victorias":
                solo_duo.get(
                    "wins",
                    0
                ),
            "derrotas":
                solo_duo.get(
                    "losses",
                    0
                )
        }

    except RiotRateLimitException:

        raise

    except Exception as error:

        print(
            "Error obteniendo rango:",
            error
        )

        return {
            "clasificado": False,
            "cola": "Solo/Duo",
            "tier": None,
            "division": None,
            "lp": 0,
            "victorias": 0,
            "derrotas": 0
        }


# ============================================================
# 3. OBTENER IDS DE PARTIDAS POR PUUID
# ============================================================

def obtener_ids_partidas_por_puuid(
    puuid: str,
    region: str,
    start: int = 0,
    count: int = 100,
    queue: int | None = None,
    start_time: int | None = None
):

    validar_api_key()

    base_url = (
        obtener_url_regional(
            region
        )
    )

    url = (
        f"{base_url}"
        f"/lol/match/v5/matches/by-puuid/"
        f"{puuid}/ids"
    )

    params = {
        "start": start,
        "count": min(
            count,
            MAXIMO_PARTIDAS
        )
    }

    if queue is not None:
        params["queue"] = queue

    if start_time is not None:
        params["startTime"] = start_time

    response = solicitar_riot(
        url,
        params=params,
        timeout=10
    )

    if response.status_code == 200:

        return response.json()

    if response.status_code == 400:

        raise Exception(
            "Solicitud incorrecta a Riot API."
        )

    if response.status_code == 401:

        raise Exception(
            "API Key no autorizada."
        )

    if response.status_code == 403:

        raise Exception(
            "API Key inválida o expirada."
        )

    if response.status_code == 404:

        raise Exception(
            "No se encontraron partidas para el jugador."
        )

    raise Exception(
        "Error de Riot API. "
        f"Código HTTP: {response.status_code}"
    )


# ============================================================
# 4. OBTENER INFORMACIÓN DE UNA PARTIDA
# ============================================================

def obtener_partida_por_id(
    match_id: str,
    region: str
):

    validar_api_key()

    base_url = (
        obtener_url_regional(
            region
        )
    )

    url = (
        f"{base_url}"
        f"/lol/match/v5/matches/{match_id}"
    )

    response = solicitar_riot(
        url,
        timeout=10
    )

    if response.status_code == 200:

        return response.json()

    if response.status_code == 400:

        raise Exception(
            "Solicitud incorrecta a Riot API."
        )

    if response.status_code == 401:

        raise Exception(
            "API Key no autorizada."
        )

    if response.status_code == 403:

        raise Exception(
            "API Key inválida o expirada."
        )

    if response.status_code == 404:

        raise Exception(
            "No se encontró la partida."
        )

    raise Exception(
        "Error de Riot API. "
        f"Código HTTP: {response.status_code}"
    )


# ============================================================
# AUXILIAR - KDA
# ============================================================

def calcular_kda(
    kills,
    deaths,
    assists
):
    """
    Calcula el KDA redondeado a 2 decimales.
    Si no hay muertes, el KDA es kills + asistencias.
    """

    if deaths > 0:

        kda = (
            kills
            +
            assists
        ) / deaths

    else:

        kda = (
            kills
            +
            assists
        )

    return round(
        kda,
        2
    )


# ============================================================
# AUXILIAR - REMAKE
# ============================================================

def es_remake(
    partida: dict
):
    """
    Una partida es remake si dura menos de 300 segundos
    o si algún participante terminó por rendición temprana.
    """

    info = partida.get(
        "info",
        {}
    )

    if (
        (info.get("gameDuration") or 0)
        <
        DURACION_MINIMA_SEGUNDOS
    ):
        return True

    return any(
        participante.get(
            "gameEndedInEarlySurrender",
            False
        )
        for participante in info.get(
            "participants",
            []
        )
    )


# ============================================================
# AUXILIAR - OBJETIVOS POR EQUIPO
# ============================================================

def extraer_objetivos_equipos(
    partida: dict
):
    """
    Objetivos de info.teams[] por team_id ("100" / "200"):
    kills, torres, dragones, barones, heraldos, larvas (solo
    si Riot las envía) y oro total (suma de goldEarned).

    Se guardan por team_id y no como aliados/rivales porque
    la misma partida puede pertenecer a varios jugadores.
    Devuelve None si la partida no trae info.teams.
    """

    info = partida.get(
        "info",
        {}
    )

    equipos = info.get(
        "teams"
    ) or []

    if not equipos:
        return None

    objetivos = {}

    for equipo in equipos:

        team_id = equipo.get(
            "teamId"
        )

        if team_id is None:
            continue

        datos_objetivos = equipo.get(
            "objectives"
        ) or {}

        def kills_objetivo(clave):

            return (
                datos_objetivos.get(clave)
                or {}
            ).get(
                "kills",
                0
            ) or 0

        detalle = {

            "kills":
                kills_objetivo("champion"),

            "torres":
                kills_objetivo("tower"),

            "dragones":
                kills_objetivo("dragon"),

            "barones":
                kills_objetivo("baron"),

            "heraldos":
                kills_objetivo("riftHerald"),

            "oro":
                sum(
                    participante.get("goldEarned", 0) or 0
                    for participante in info.get(
                        "participants",
                        []
                    )
                    if participante.get("teamId") == team_id
                ),
        }

        if "horde" in datos_objetivos:

            detalle["larvas"] = kills_objetivo(
                "horde"
            )

        objetivos[str(team_id)] = detalle

    return objetivos or None


# ============================================================
# 5. EXTRAER ESTADÍSTICAS DEL JUGADOR
# ============================================================

def extraer_estadisticas_jugador(
    partida: dict,
    puuid: str
):
    """
    Extrae las estadísticas principales del jugador
    y también identifica al rival del equipo contrario
    que ocupó la misma posición.
    """

    info = partida.get(
        "info",
        {}
    )

    participantes = info.get(
        "participants",
        []
    )

    if not participantes:

        raise Exception(
            "La partida no contiene participantes."
        )


    # ========================================================
    # BUSCAR JUGADOR
    # ========================================================

    jugador = None

    for participante in participantes:

        if (
            participante.get(
                "puuid"
            )
            ==
            puuid
        ):

            jugador = participante

            break


    if not jugador:

        raise Exception(
            "El jugador no se encuentra en esta partida."
        )


    # ========================================================
    # DATOS PRINCIPALES
    # ========================================================

    team_id_jugador = (
        jugador.get(
            "teamId"
        )
    )

    posicion = (
        jugador.get(
            "teamPosition"
        )
    )


    # ========================================================
    # DETALLE COMPLETO DE LOS DOS EQUIPOS
    # ========================================================

    equipos_detalle = {
        "aliados": [],
        "rivales": [],
    }


    for participante in participantes:

        participante_kills = (
            participante.get(
                "kills",
                0
            )
        )

        participante_deaths = (
            participante.get(
                "deaths",
                0
            )
        )

        participante_assists = (
            participante.get(
                "assists",
                0
            )
        )


        participante_cs = (
            participante.get(
                "totalMinionsKilled",
                0
            )
            +
            participante.get(
                "neutralMinionsKilled",
                0
            )
        )


        participante_detalle = {

            "puuid":
                participante.get(
                    "puuid"
                ),

            "nombre":
                participante.get(
                    "riotIdGameName"
                ),

            "tag":
                participante.get(
                    "riotIdTagline"
                ),

            "team_id":
                participante.get(
                    "teamId"
                ),

            "victoria":
                participante.get(
                    "win",
                    False
                ),

            "posicion":
                participante.get(
                    "teamPosition"
                ),

            "campeon": {

                "id":
                    participante.get(
                        "championId"
                    ),

                "nombre":
                    participante.get(
                        "championName"
                    ),

                "nivel":
                    participante.get(
                        "champLevel"
                    ),
            },

            "combate": {

                "kills":
                    participante_kills,

                "muertes":
                    participante_deaths,

                "asistencias":
                    participante_assists,

                "kda":
                    calcular_kda(
                        participante_kills,
                        participante_deaths,
                        participante_assists
                    ),
            },

            "recursos": {

                "cs":
                    participante_cs,

                "oro":
                    participante.get(
                        "goldEarned",
                        0
                    ),
            },

            "daño": {

                "campeones":
                    participante.get(
                        "totalDamageDealtToChampions",
                        0
                    ),
            },

            "vision": {

                "score":
                    participante.get(
                        "visionScore",
                        0
                    ),

                "wards":
                    participante.get(
                        "wardsPlaced",
                        0
                    ),

                # None si Riot no envía el dato.
                "control_wards":
                    participante.get(
                        "visionWardsBoughtInGame"
                    ),
            },

            "objetos": [

                participante.get(
                    "item0",
                    0
                ),

                participante.get(
                    "item1",
                    0
                ),

                participante.get(
                    "item2",
                    0
                ),

                participante.get(
                    "item3",
                    0
                ),

                participante.get(
                    "item4",
                    0
                ),

                participante.get(
                    "item5",
                    0
                ),

                participante.get(
                    "item6",
                    0
                ),

            ],

            "es_jugador":
                participante.get(
                    "puuid"
                )
                ==
                puuid,
        }


        if (
            participante.get(
                "teamId"
            )
            ==
            team_id_jugador
        ):

            equipos_detalle[
                "aliados"
            ].append(
                participante_detalle
            )

        else:

            equipos_detalle[
                "rivales"
            ].append(
                participante_detalle
            )

    champion_name = (
        jugador.get(
            "championName"
        )
    )

    champion_id = (
        jugador.get(
            "championId"
        )
    )


    # ========================================================
    # RIVAL DE LA MISMA POSICIÓN
    # ========================================================

    rival_rol = None

    if posicion:

        for participante in participantes:

            if (
                participante.get(
                    "puuid"
                )
                ==
                puuid
            ):
                continue

            if (
                participante.get(
                    "teamId"
                )
                ==
                team_id_jugador
            ):
                continue

            if (
                participante.get(
                    "teamPosition"
                )
                !=
                posicion
            ):
                continue


            rival_kills = (
                participante.get(
                    "kills",
                    0
                )
            )

            rival_deaths = (
                participante.get(
                    "deaths",
                    0
                )
            )

            rival_assists = (
                participante.get(
                    "assists",
                    0
                )
            )


            rival_rol = {

                "puuid":
                    participante.get(
                        "puuid"
                    ),

                "nombre":
                    participante.get(
                        "riotIdGameName"
                    ),

                "tag":
                    participante.get(
                        "riotIdTagline"
                    ),

                "team_id":
                    participante.get(
                        "teamId"
                    ),

                "posicion":
                    participante.get(
                        "teamPosition"
                    ),

                "campeon": {

                    "id":
                        participante.get(
                            "championId"
                        ),

                    "nombre":
                        participante.get(
                            "championName"
                        ),

                    "nivel":
                        participante.get(
                            "champLevel"
                        )
                },

                "combate": {

                    "kills":
                        rival_kills,

                    "muertes":
                        rival_deaths,

                    "asistencias":
                        rival_assists,

                    "kda":
                        calcular_kda(
                            rival_kills,
                            rival_deaths,
                            rival_assists
                        )
                },

                "resultado": {

                    "victoria":
                        participante.get(
                            "win",
                            False
                        )
                }
            }

            break


    # ========================================================
    # DURACIÓN
    # ========================================================

    game_duration = (
        info.get(
            "gameDuration",
            0
        )
    )

    minutos = (
        game_duration / 60
        if game_duration
        else 0
    )


    # ========================================================
    # COMBATE
    # ========================================================

    kills = (
        jugador.get(
            "kills",
            0
        )
    )

    deaths = (
        jugador.get(
            "deaths",
            0
        )
    )

    assists = (
        jugador.get(
            "assists",
            0
        )
    )


    # ========================================================
    # FARMEO
    # ========================================================

    cs = (
        jugador.get(
            "totalMinionsKilled",
            0
        )
        +
        jugador.get(
            "neutralMinionsKilled",
            0
        )
    )

    cs_por_minuto = (
        cs / minutos
        if minutos > 0
        else 0
    )


    # ========================================================
    # ECONOMÍA
    # ========================================================

    oro = (
        jugador.get(
            "goldEarned",
            0
        )
    )

    oro_por_minuto = (
        oro / minutos
        if minutos > 0
        else 0
    )


    # ========================================================
    # DAÑO
    # ========================================================

    daño = (
        jugador.get(
            "totalDamageDealtToChampions",
            0
        )
    )

    daño_por_minuto = (
        daño / minutos
        if minutos > 0
        else 0
    )


    # ========================================================
    # DESAFÍOS (bloque "challenges" de Riot)
    # ========================================================

    desafios = (
        jugador.get(
            "challenges"
        )
        or {}
    )

    cs_linea_10 = desafios.get(
        "laneMinionsFirst10Minutes"
    )

    cs_jungla_10 = desafios.get(
        "jungleCsBefore10Minutes"
    )

    cs_10_minutos = (
        round(
            (cs_linea_10 or 0)
            + (cs_jungla_10 or 0),
            2
        )
        if cs_linea_10 is not None
        or cs_jungla_10 is not None
        else None
    )


    # ========================================================
    # RESPUESTA
    # ========================================================

    return {

        "jugador": {

            "puuid":
                puuid,

            "nombre":
                jugador.get(
                    "riotIdGameName"
                ),

            "tag":
                jugador.get(
                    "riotIdTagline"
                ),

            "team_id":
                team_id_jugador
        },


        "partida": {

            "match_id":
                partida.get(
                    "metadata",
                    {}
                ).get(
                    "matchId"
                ),

            "modo":
                info.get(
                    "gameMode"
                ),

            "queue_id":
                info.get(
                    "queueId"
                ),

            "posicion":
                posicion,

            "duracion_segundos":
                game_duration,

            "duracion_minutos":
                round(
                    minutos,
                    2
                ),

            "game_creation":
                info.get(
                    "gameCreation"
                ),

            "game_end_timestamp":
                info.get(
                    "gameEndTimestamp"
                ),

            "version_parche":
                info.get(
                    "gameVersion"
                )
        },


        "remake":
            es_remake(
                partida
            ),


        "resultado": {

            "victoria":
                jugador.get(
                    "win",
                    False
                )
        },


        "campeon": {

            "id":
                champion_id,

            "nombre":
                champion_name,

            "nivel":
                jugador.get(
                    "champLevel"
                )
        },


        "combate": {

            "kills":
                kills,

            "muertes":
                deaths,

            "asistencias":
                assists,

            "kda":
                calcular_kda(
                    kills,
                    deaths,
                    assists
                ),

            # Fracción 0-1 de las kills del equipo en las que
            # participó el jugador (challenges.killParticipation).
            # None si Riot no envía el dato.
            "participacion_kills":
                (
                    jugador.get(
                        "challenges"
                    )
                    or {}
                ).get(
                    "killParticipation"
                ),

            # Fracción 0-1 del daño a campeones del equipo
            # (challenges.teamDamagePercentage). None si no viene.
            "porcentaje_daño_equipo":
                desafios.get(
                    "teamDamagePercentage"
                )
        },


        "farmeo": {

            "cs":
                cs,

            "cs_por_minuto":
                round(
                    cs_por_minuto,
                    2
                ),

            # Súbditos de línea + CS de jungla antes del minuto 10
            # (challenges). None si Riot no envía ninguno de los dos.
            "cs_10_minutos":
                cs_10_minutos
        },


        "economia": {

            "oro":
                oro,

            "oro_por_minuto":
                round(
                    oro_por_minuto,
                    2
                )
        },


        "daño": {

            "daño_campeones":
                daño,

            "daño_por_minuto":
                round(
                    daño_por_minuto,
                    2
                )
        },


        "vision": {

            "vision_score":
                jugador.get(
                    "visionScore",
                    0
                ),

            "wards_colocados":
                jugador.get(
                    "wardsPlaced",
                    0
                ),

            "wards_eliminados":
                jugador.get(
                    "wardsKilled",
                    0
                ),

            # None si Riot no envía el dato (no se confunde con 0 compradas).
            "control_wards":
                jugador.get(
                    "visionWardsBoughtInGame"
                )
        },


        "rival_rol":
            rival_rol,
        "equipos":
            equipos_detalle,

        # Por team_id; no se envía en POST /api/analisis.
        "objetivos":
            extraer_objetivos_equipos(
                partida
            )
    }


# ============================================================
# 6. DESCARGA PARALELA DE PARTIDAS
# ============================================================

def descargar_partidas(
    match_ids: list,
    puuid: str,
    region: str
):
    """
    Descarga en paralelo (máximo 8 hilos) las partidas
    indicadas. El limitador compartido controla el ritmo.

    Devuelve (descargadas, errores), ambos por match_id.
    Si Riot sigue respondiendo 429 tras los reintentos,
    no se inician más descargas.
    """

    descargadas = {}
    errores = {}

    if not match_ids:
        return descargadas, errores

    detener = threading.Event()


    def descargar(
        match_id
    ):

        if detener.is_set():
            return None

        partida_completa = (
            obtener_partida_por_id(
                match_id=match_id,
                region=region
            )
        )

        return extraer_estadisticas_jugador(
            partida_completa,
            puuid
        )


    with ThreadPoolExecutor(
        max_workers=min(
            HILOS_DESCARGA,
            len(match_ids)
        )
    ) as ejecutor:

        futuros = {
            ejecutor.submit(
                descargar,
                match_id
            ): match_id
            for match_id in match_ids
        }

        for futuro in as_completed(
            futuros
        ):

            match_id = futuros[
                futuro
            ]

            try:

                estadisticas = futuro.result()

                if estadisticas is not None:

                    descargadas[
                        match_id
                    ] = estadisticas

            except RiotRateLimitException as error:

                detener.set()

                errores[match_id] = {

                    "match_id":
                        match_id,

                    "error":
                        error.mensaje,

                    "retry_after":
                        error.retry_after
                }

            except Exception as error:

                errores[match_id] = {

                    "match_id":
                        match_id,

                    "error":
                        str(
                            error
                        )
                }

    return descargadas, errores


# ============================================================
# 7. CACHÉ LOCAL (partidas.json)
# ============================================================

def cache_json_actualizado(
    partida_guardada
):
    """
    Una partida del caché sirve solo si tiene el formato
    actual (rival, equipos y marca de remake).
    """

    return (
        isinstance(
            partida_guardada,
            dict
        )
        and
        "rival_rol" in partida_guardada
        and
        "equipos" in partida_guardada
        and
        "remake" in partida_guardada
    )


def actualizar_cache_json(
    datos: dict,
    clave_jugador: str,
    puuid: str,
    region: str,
    partidas_guardadas: dict,
    resultados: list
):

    jugadores = datos.setdefault(
        "jugadores",
        {}
    )

    jugador_guardado = jugadores.get(
        clave_jugador,
        {}
    )

    nombre = jugador_guardado.get(
        "nombre"
    )

    tag = jugador_guardado.get(
        "tag"
    )

    for partida in resultados:

        datos_jugador = partida.get(
            "jugador"
        )

        if not datos_jugador:
            continue

        nombre = datos_jugador.get(
            "nombre"
        )

        tag = datos_jugador.get(
            "tag"
        )

        break

    jugadores[clave_jugador] = {

        "puuid":
            puuid,

        "region":
            region.upper(),

        "nombre":
            nombre,

        "tag":
            tag,

        "partidas":
            partidas_guardadas
    }

    guardar_partidas_guardadas(
        datos
    )


# ============================================================
# 8. OBTENER PARTIDAS RANKED DE LA TEMPORADA
# ============================================================

def obtener_estadisticas_ultimas_partidas(
    puuid: str,
    region: str,
    count: int = MAXIMO_PARTIDAS
):
    """
    Obtiene hasta 100 partidas Ranked Solo/Dúo desde el
    inicio de temporada (TEMPORADA_INICIO).

    Caché:
        - DB_ENABLED=true  → SQL Server.
        - DB_ENABLED=false → partidas.json.

    Solo se descargan de Riot las partidas que no estén
    en el caché. Los remakes se conservan marcados con
    "remake": True.

    Devuelve:
        {
            "partidas": [...],   # en el orden de Riot
            "carga": {
                "desde_bd": n,
                "descargadas": n,
                "remakes": n,
                "cache": "sql_server" | "partidas.json"
            }
        }
    """

    clave_jugador = (
        f"{region.upper()}:{puuid}"
    )


    # ========================================================
    # IDS DE LA TEMPORADA (RANKED SOLO/DÚO)
    # ========================================================

    partidas_ids = (
        obtener_ids_partidas_por_puuid(
            puuid=puuid,
            region=region,
            start=0,
            count=count,
            queue=COLA_RANKED_SOLO_DUO,
            start_time=INICIO_TEMPORADA
        )
    )


    # ========================================================
    # LEER CACHÉ
    # ========================================================

    datos_json = None
    partidas_guardadas = {}

    if DB_ENABLED:

        try:

            en_cache = leer_partidas_jugador(
                puuid=puuid,
                match_ids=partidas_ids
            )

        except Exception as error:

            # Si la BD falla, se descarga todo desde Riot.
            print(
                "Error leyendo partidas de SQL Server:",
                error
            )

            en_cache = {}

    else:

        datos_json = cargar_partidas_guardadas()

        partidas_guardadas = (
            datos_json
            .setdefault(
                "jugadores",
                {}
            )
            .get(
                clave_jugador,
                {}
            )
            .get(
                "partidas",
                {}
            )
        )

        en_cache = {
            match_id: partidas_guardadas[match_id]
            for match_id in partidas_ids
            if cache_json_actualizado(
                partidas_guardadas.get(
                    match_id
                )
            )
        }


    # ========================================================
    # DESCARGAR SOLO LAS QUE FALTAN
    # ========================================================

    faltantes = [
        match_id
        for match_id in partidas_ids
        if match_id not in en_cache
    ]

    descargadas, errores = descargar_partidas(
        faltantes,
        puuid,
        region
    )


    resultados = []

    for match_id in partidas_ids:

        if match_id in en_cache:
            resultados.append(
                en_cache[match_id]
            )

        elif match_id in descargadas:
            resultados.append(
                descargadas[match_id]
            )

        elif match_id in errores:
            resultados.append(
                errores[match_id]
            )


    # ========================================================
    # GUARDAR LAS NUEVAS
    # ========================================================

    if DB_ENABLED:

        try:

            guardar_partidas_sql(
                puuid=puuid,
                region=region,
                partidas=list(
                    descargadas.values()
                ),
            )

        except Exception as error:

            # La persistencia no debe impedir que el análisis
            # continúe si SQL Server presenta un problema.
            print(
                "Error guardando partidas en SQL Server:",
                error
            )

    else:

        partidas_guardadas.update(
            descargadas
        )

        actualizar_cache_json(
            datos=datos_json,
            clave_jugador=clave_jugador,
            puuid=puuid,
            region=region,
            partidas_guardadas=partidas_guardadas,
            resultados=[
                partida
                for partida in resultados
                if "error" not in partida
            ]
        )


    return {

        "partidas":
            resultados,

        "carga": {

            "desde_bd":
                len(en_cache),

            "descargadas":
                len(descargadas),

            "remakes":
                sum(
                    1
                    for partida in resultados
                    if partida.get("remake")
                ),

            "cache":
                "sql_server"
                if DB_ENABLED
                else "partidas.json"
        }
    }


# ============================================================
# 9. DETALLE DE UNA PARTIDA (10 PARTICIPANTES)
# ============================================================

class PartidaRemakeException(Exception):
    """La partida es un remake: no tiene detalle válido."""


MENSAJE_REMAKE = (
    "Esta partida es un remake y no tiene detalle válido."
)


def objetivos_relativos(
    objetivos_por_equipo,
    team_id_jugador
):
    """
    Convierte los objetivos por team_id en
    {"aliados", "rivales"} para el jugador que consulta.
    """

    if not objetivos_por_equipo or team_id_jugador is None:
        return None

    aliados = objetivos_por_equipo.get(
        str(team_id_jugador)
    )

    rivales = next(
        (
            valor
            for clave, valor in objetivos_por_equipo.items()
            if clave != str(team_id_jugador)
        ),
        None
    )

    if aliados is None or rivales is None:
        return None

    return {
        "aliados": aliados,
        "rivales": rivales,
    }


def formatear_oro_k(
    oro
):
    """1834 → "1.8k" (redondeo a 0.1k)."""

    return f"{oro / 1000:.1f}k"


def generar_resumen_partida(
    equipos: dict
):
    """
    Resumen de 2 o 3 frases construido con reglas (sin IA).
    Solo afirma lo que los datos confirman:
    - Sin rival de línea identificado no compara el oro.
    - Si hay empate en daño o visión no dice "el que más".
    """

    aliados = equipos.get(
        "aliados",
        []
    )

    rivales = equipos.get(
        "rivales",
        []
    )

    jugador = next(
        (
            participante
            for participante in aliados
            if participante.get("es_jugador")
        ),
        None
    )

    if jugador is None:
        return None

    combate = jugador.get(
        "combate",
        {}
    )

    kills = combate.get("kills", 0) or 0
    muertes = combate.get("muertes", 0) or 0
    asistencias = combate.get("asistencias", 0) or 0

    campeon = (
        jugador.get("campeon")
        or {}
    ).get(
        "nombre"
    )

    frases = []


    # 1) Resultado y KDA
    frases.append(
        ("Ganaste" if jugador.get("victoria") else "Perdiste")
        + f" con {kills}/{muertes}/{asistencias}"
        + (f" jugando {campeon}" if campeon else "")
        + "."
    )


    # 2) Diferencia de oro con el rival de línea
    posicion = jugador.get(
        "posicion"
    )

    rival = next(
        (
            participante
            for participante in rivales
            if posicion
            and participante.get("posicion") == posicion
        ),
        None
    )

    if rival is not None:

        oro_jugador = (
            jugador.get("recursos") or {}
        ).get("oro", 0) or 0

        oro_rival = (
            rival.get("recursos") or {}
        ).get("oro", 0) or 0

        diferencia = oro_jugador - oro_rival

        campeon_rival = (
            rival.get("campeon")
            or {}
        ).get(
            "nombre"
        )

        texto_rival = (
            f"tu rival de línea ({campeon_rival})"
            if campeon_rival
            else "tu rival de línea"
        )

        diferencia_k = formatear_oro_k(
            abs(diferencia)
        )

        if diferencia_k == "0.0k":

            frases.append(
                "Terminaste con prácticamente el mismo oro "
                f"que {texto_rival}."
            )

        else:

            frases.append(
                f"Terminaste con {diferencia_k} de oro "
                + ("más" if diferencia > 0 else "menos")
                + f" que {texto_rival}."
            )


    # 3) Máximo del equipo en daño o visión (solo sin empate)
    def es_maximo_unico(valor_de):

        valor_jugador = valor_de(jugador)

        return valor_jugador > 0 and all(
            valor_de(otro) < valor_jugador
            for otro in aliados
            if otro is not jugador
        )

    mas_daño = es_maximo_unico(
        lambda participante: (
            participante.get("daño") or {}
        ).get("campeones", 0) or 0
    )

    mas_vision = es_maximo_unico(
        lambda participante: (
            participante.get("vision") or {}
        ).get("score", 0) or 0
    )

    if mas_daño and mas_vision:

        frases.append(
            "Fuiste el jugador con más daño y más visión "
            "de tu equipo."
        )

    elif mas_daño:

        frases.append(
            "Fuiste el jugador con más daño de tu equipo."
        )

    elif mas_vision:

        frases.append(
            "Fuiste el jugador con más visión de tu equipo."
        )

    else:

        kills_equipo = sum(
            (participante.get("combate") or {}).get("kills", 0) or 0
            for participante in aliados
        )

        if kills_equipo > 0:

            participacion = round(
                (kills + asistencias)
                / kills_equipo
                * 100
            )

            frases.append(
                f"Participaste en el {participacion} % "
                "de las kills de tu equipo."
            )

    return " ".join(
        frases
    )


def construir_detalle_partida(
    base: dict,
    origen: str,
    equipos: dict,
    objetivos_por_equipo,
    duracion_segundos,
    game_creation,
    version_parche=None
):
    """
    Respuesta de GET /api/partida/{match_id}.
    "objetivos" es None si no se pudieron obtener.
    """

    jugador = next(
        (
            participante
            for participante in equipos.get("aliados", [])
            if participante.get("es_jugador")
        ),
        {}
    )

    return {
        **base,
        "origen": origen,
        "remake": False,
        "resultado": {
            "victoria": bool(
                jugador.get("victoria", False)
            ),
        },
        "duracion_segundos": duracion_segundos or 0,
        "game_creation": game_creation,
        # Respaldo del frontend para la versión de Data Dragon.
        "version_parche": version_parche,
        "equipos": equipos,
        "objetivos": objetivos_relativos(
            objetivos_por_equipo,
            jugador.get("team_id"),
        ),
        "resumen": generar_resumen_partida(
            equipos
        ),
    }


def intentar_descargar_estadisticas(
    match_id: str,
    puuid: str,
    region: str
):
    """
    Pide la partida a Riot (con el limitador compartido de
    riot_cliente). Ante cualquier error (429, clave vencida,
    sin conexión...) devuelve None en lugar de fallar.
    """

    try:

        return extraer_estadisticas_jugador(
            obtener_partida_por_id(
                match_id=match_id,
                region=region
            ),
            puuid
        )

    except Exception as error:

        print(
            "No se pudieron obtener los objetivos de "
            f"{match_id}:",
            error
        )

        return None


def obtener_detalle_partida(
    match_id: str,
    puuid: str,
    region: str
):
    """
    Devuelve el detalle de la partida relativo al jugador:
    equipos, objetivos, duración, fecha, resultado y resumen.

    1. Busca la partida en el caché (BD o partidas.json).
    2. Si es un remake, lanza PartidaRemakeException sin
       consultar a Riot.
    3. Si está guardada sin objetivos, la pide una vez a Riot
       y la guarda; si Riot falla, responde lo guardado con
       "objetivos": None.
    4. Si no está guardada, la pide a Riot.
    """

    base = {
        "match_id": match_id,
        "puuid": puuid,
        "region": region,
    }


    if DB_ENABLED:

        try:

            guardada = leer_equipos_partida(
                match_id=match_id,
                puuid=puuid
            )

        except Exception as error:

            print(
                "Error leyendo la partida de SQL Server:",
                error
            )

            guardada = None

        if guardada:

            if guardada["remake"]:

                raise PartidaRemakeException(
                    MENSAJE_REMAKE
                )

            objetivos = guardada["objetivos"]
            participantes = guardada["participantes"]

            if objetivos is None:

                descargada = intentar_descargar_estadisticas(
                    match_id,
                    puuid,
                    region
                )

                if (
                    descargada is not None
                    and descargada.get("objetivos")
                ):

                    objetivos = descargada["objetivos"]

                    participantes = equipos_a_participantes(
                        descargada["equipos"]
                    )

                    try:

                        guardar_objetivos_partida(
                            match_id=match_id,
                            participantes=participantes,
                            objetivos=objetivos,
                        )

                    except Exception as error:

                        print(
                            "Error guardando objetivos en "
                            "SQL Server:",
                            error
                        )

            return construir_detalle_partida(
                base=base,
                origen="sql_server",
                equipos=reconstruir_equipos(
                    participantes,
                    puuid
                ),
                objetivos_por_equipo=objetivos,
                duracion_segundos=guardada["duracion_segundos"],
                game_creation=guardada["game_creation"],
                version_parche=guardada.get("version_parche"),
            )

    else:

        datos_json = cargar_partidas_guardadas()

        jugador_json = (
            datos_json
            .get(
                "jugadores",
                {}
            )
            .get(
                f"{region.upper()}:{puuid}",
                {}
            )
        )

        partida_json = (
            jugador_json
            .get(
                "partidas",
                {}
            )
            .get(
                match_id
            )
        )

        if cache_json_actualizado(
            partida_json
        ):

            if partida_json["remake"]:

                raise PartidaRemakeException(
                    MENSAJE_REMAKE
                )

            if not partida_json.get("objetivos"):

                descargada = intentar_descargar_estadisticas(
                    match_id,
                    puuid,
                    region
                )

                if (
                    descargada is not None
                    and descargada.get("objetivos")
                ):

                    partida_json = descargada

                    jugador_json["partidas"][match_id] = descargada

                    try:

                        guardar_partidas_guardadas(
                            datos_json
                        )

                    except Exception as error:

                        print(
                            "Error guardando partidas.json:",
                            error
                        )

            datos_partida = partida_json.get(
                "partida",
                {}
            )

            return construir_detalle_partida(
                base=base,
                origen="partidas.json",
                equipos=partida_json["equipos"],
                objetivos_por_equipo=partida_json.get(
                    "objetivos"
                ),
                duracion_segundos=datos_partida.get(
                    "duracion_segundos"
                ),
                game_creation=datos_partida.get(
                    "game_creation"
                ),
                version_parche=datos_partida.get(
                    "version_parche"
                ),
            )


    # No está guardada: se pide a Riot (los errores se propagan).
    estadisticas = extraer_estadisticas_jugador(
        obtener_partida_por_id(
            match_id=match_id,
            region=region
        ),
        puuid
    )

    if estadisticas["remake"]:

        raise PartidaRemakeException(
            MENSAJE_REMAKE
        )

    return construir_detalle_partida(
        base=base,
        origen="riot",
        equipos=estadisticas["equipos"],
        objetivos_por_equipo=estadisticas["objetivos"],
        duracion_segundos=estadisticas["partida"].get(
            "duracion_segundos"
        ),
        game_creation=estadisticas["partida"].get(
            "game_creation"
        ),
        version_parche=estadisticas["partida"].get(
            "version_parche"
        ),
    )
