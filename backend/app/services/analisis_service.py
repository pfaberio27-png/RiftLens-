import json
import os
from collections import Counter

from backend.app.services.kmeans_service import analizar_patrones_kmeans

from backend.app.services.data_dragon import (
    obtener_version_data_dragon,
    url_icono_campeon,
    version_parche_mas_reciente,
)

# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

RUTA_REFERENCIA_PROFESIONAL = os.path.join(
    BASE_DIR,
    "data",
    "referencia_profesional.json"
)


# ============================================================
# EQUIVALENCIAS DE POSICIONES RIOT -> SISTEMA
# ============================================================

EQUIVALENCIAS_ROLES = {
    "TOP": "TOP",

    "JUNGLE": "JUNGLE",
    "JNG": "JUNGLE",

    "MIDDLE": "MID",
    "MID": "MID",

    "BOTTOM": "ADC",
    "BOT": "ADC",
    "ADC": "ADC",

    "UTILITY": "SUPPORT",
    "SUPPORT": "SUPPORT",
    "SUP": "SUPPORT"
}


# ============================================================
# NOMBRES DE MÉTRICAS
# ============================================================

NOMBRES_METRICAS = {
    "win_rate": "Win Rate",
    "kda": "KDA",
    "cs_por_minuto": "CS por minuto",
    "oro_por_minuto": "Oro por minuto",
    "daño_por_minuto": "Daño por minuto",
    "vision_score": "Puntuación de visión"
}


# ============================================================
# CARGAR REFERENCIA PROFESIONAL
# ============================================================

def cargar_referencia_profesional():
    """
    Carga las referencias profesionales generadas
    a partir del dataset de Oracle's Elixir.
    """

    if not os.path.exists(RUTA_REFERENCIA_PROFESIONAL):
        raise FileNotFoundError(
            "No se encontró el archivo referencia_profesional.json "
            f"en la ruta: {RUTA_REFERENCIA_PROFESIONAL}"
        )

    try:
        with open(
            RUTA_REFERENCIA_PROFESIONAL,
            "r",
            encoding="utf-8"
        ) as archivo:
            datos = json.load(archivo)

    except json.JSONDecodeError as error:
        raise Exception(
            "El archivo referencia_profesional.json "
            "no contiene un JSON válido."
        ) from error

    if "roles" not in datos:
        raise Exception(
            "El archivo referencia_profesional.json "
            "no contiene la propiedad 'roles'."
        )

    return datos


# ============================================================
# NORMALIZAR POSICIÓN
# ============================================================

def normalizar_rol(posicion):
    """
    Convierte la posición entregada por Riot Games
    al formato utilizado por el sistema.

    Ejemplos:
        MIDDLE  -> MID
        BOTTOM  -> ADC
        UTILITY -> SUPPORT
    """

    if not posicion:
        return None

    posicion = str(posicion).strip().upper()

    return EQUIVALENCIAS_ROLES.get(posicion)


# ============================================================
# FILTRAR PARTIDAS VÁLIDAS
# ============================================================

def obtener_partidas_historial(partidas):
    """
    Elimina registros con errores o formatos inválidos.
    Conserva los remakes (para el historial).
    """

    if isinstance(partidas, dict):
        partidas = list(partidas.values())

    if not isinstance(partidas, list):
        return []

    return [
        partida
        for partida in partidas
        if isinstance(partida, dict)
        and "error" not in partida
    ]


def obtener_partidas_validas(partidas):
    """
    Partidas usadas en los cálculos: sin errores
    ni remakes.
    """

    return [
        partida
        for partida in obtener_partidas_historial(partidas)
        if not partida.get("remake", False)
    ]


# ============================================================
# DISTRIBUCIÓN DE ROLES
# ============================================================

def obtener_distribucion_roles(partidas):
    """
    Cuenta cuántas partidas jugó el usuario
    en cada posición.
    """

    partidas_validas = obtener_partidas_validas(partidas)

    contador = Counter()

    for partida in partidas_validas:

        posicion = (
            partida
            .get("partida", {})
            .get("posicion")
        )

        rol = normalizar_rol(posicion)

        if rol:
            contador[rol] += 1

    total_con_rol = sum(contador.values())

    distribucion = {}

    for rol in [
        "TOP",
        "JUNGLE",
        "MID",
        "ADC",
        "SUPPORT"
    ]:

        cantidad = contador.get(rol, 0)

        porcentaje = (
            (cantidad / total_con_rol) * 100
            if total_con_rol > 0
            else 0
        )

        distribucion[rol] = {
            "partidas": cantidad,
            "porcentaje": round(porcentaje, 2)
        }

    return distribucion


# ============================================================
# DETERMINAR ROL PRINCIPAL
# ============================================================

def determinar_rol_principal(partidas):
    """
    Determina el rol predominante del jugador
    según sus partidas recientes.
    """

    partidas_validas = obtener_partidas_validas(partidas)

    contador = Counter()

    for partida in partidas_validas:

        posicion = (
            partida
            .get("partida", {})
            .get("posicion")
        )

        rol = normalizar_rol(posicion)

        if rol:
            contador[rol] += 1

    if not contador:
        raise Exception(
            "No fue posible determinar el rol principal "
            "del jugador con las partidas disponibles."
        )

    rol_principal, cantidad = contador.most_common(1)[0]

    return rol_principal


# ============================================================
# FILTRAR PARTIDAS POR ROL
# ============================================================

def filtrar_partidas_por_rol(partidas, rol):
    """
    Selecciona únicamente las partidas correspondientes
    al rol que será comparado contra la referencia profesional.
    """

    partidas_validas = obtener_partidas_validas(partidas)

    rol = normalizar_rol(rol) or str(rol).upper()

    resultado = []

    for partida in partidas_validas:

        posicion = (
            partida
            .get("partida", {})
            .get("posicion")
        )

        rol_partida = normalizar_rol(posicion)

        if rol_partida == rol:
            resultado.append(partida)

    return resultado


# ============================================================
# CALCULAR PROMEDIOS DEL JUGADOR
# ============================================================

def calcular_promedios(partidas):
    """
    Calcula las estadísticas promedio de las
    partidas proporcionadas.
    """

    partidas_validas = obtener_partidas_validas(partidas)

    if not partidas_validas:
        raise Exception(
            "No existen partidas válidas para realizar el análisis."
        )

    cantidad = len(partidas_validas)

    # --------------------------------------------------------
    # RESULTADOS
    # --------------------------------------------------------

    victorias = sum(
        1
        for partida in partidas_validas
        if partida.get(
            "resultado",
            {}
        ).get(
            "victoria",
            False
        )
    )

    derrotas = cantidad - victorias

    win_rate = (
        (victorias / cantidad) * 100
        if cantidad > 0
        else 0
    )

    # --------------------------------------------------------
    # COMBATE
    # --------------------------------------------------------

    kills_total = sum(
        float(
            partida.get(
                "combate",
                {}
            ).get(
                "kills",
                0
            ) or 0
        )
        for partida in partidas_validas
    )

    muertes_total = sum(
        float(
            partida.get(
                "combate",
                {}
            ).get(
                "muertes",
                0
            ) or 0
        )
        for partida in partidas_validas
    )

    asistencias_total = sum(
        float(
            partida.get(
                "combate",
                {}
            ).get(
                "asistencias",
                0
            ) or 0
        )
        for partida in partidas_validas
    )

    kda_total = sum(
        float(
            partida.get(
                "combate",
                {}
            ).get(
                "kda",
                0
            ) or 0
        )
        for partida in partidas_validas
    )

    # --------------------------------------------------------
    # FARMEO
    # --------------------------------------------------------

    cs_total = sum(
        float(
            partida.get(
                "farmeo",
                {}
            ).get(
                "cs",
                0
            ) or 0
        )
        for partida in partidas_validas
    )

    cs_por_minuto_total = sum(
        float(
            partida.get(
                "farmeo",
                {}
            ).get(
                "cs_por_minuto",
                0
            ) or 0
        )
        for partida in partidas_validas
    )

    # --------------------------------------------------------
    # ECONOMÍA
    # --------------------------------------------------------

    oro_total = sum(
        float(
            partida.get(
                "economia",
                {}
            ).get(
                "oro",
                0
            ) or 0
        )
        for partida in partidas_validas
    )

    oro_por_minuto_total = sum(
        float(
            partida.get(
                "economia",
                {}
            ).get(
                "oro_por_minuto",
                0
            ) or 0
        )
        for partida in partidas_validas
    )

    # --------------------------------------------------------
    # DAÑO
    # --------------------------------------------------------

    daño_total = sum(
        float(
            partida.get(
                "daño",
                {}
            ).get(
                "daño_campeones",
                0
            ) or 0
        )
        for partida in partidas_validas
    )

    daño_por_minuto_total = sum(
        float(
            partida.get(
                "daño",
                {}
            ).get(
                "daño_por_minuto",
                0
            ) or 0
        )
        for partida in partidas_validas
    )

    # --------------------------------------------------------
    # VISIÓN
    # --------------------------------------------------------

    vision_total = sum(
        float(
            partida.get(
                "vision",
                {}
            ).get(
                "vision_score",
                0
            ) or 0
        )
        for partida in partidas_validas
    )

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    return {

        "partidas_analizadas": cantidad,

        "resultados": {
            "victorias": victorias,
            "derrotas": derrotas,
            "win_rate": round(
                win_rate,
                2
            )
        },

        "combate": {
            "kills_promedio": round(
                kills_total / cantidad,
                2
            ),
            "muertes_promedio": round(
                muertes_total / cantidad,
                2
            ),
            "asistencias_promedio": round(
                asistencias_total / cantidad,
                2
            ),
            "kda_promedio": round(
                kda_total / cantidad,
                2
            )
        },

        "farmeo": {
            "cs_promedio": round(
                cs_total / cantidad,
                2
            ),
            "cs_por_minuto_promedio": round(
                cs_por_minuto_total / cantidad,
                2
            )
        },

        "economia": {
            "oro_promedio": round(
                oro_total / cantidad,
                2
            ),
            "oro_por_minuto_promedio": round(
                oro_por_minuto_total / cantidad,
                2
            )
        },

        "daño": {
            "daño_promedio": round(
                daño_total / cantidad,
                2
            ),
            "daño_por_minuto_promedio": round(
                daño_por_minuto_total / cantidad,
                2
            )
        },

        "vision": {
            "vision_score_promedio": round(
                vision_total / cantidad,
                2
            )
        }
    }


# ============================================================
# OBTENER REFERENCIA DE UN ROL
# ============================================================

def obtener_referencia_por_rol(rol):
    """
    Obtiene los valores profesionales correspondientes
    al rol principal del jugador.
    """

    datos = cargar_referencia_profesional()

    roles = datos.get(
        "roles",
        {}
    )

    rol = normalizar_rol(rol) or str(rol).upper()

    if rol not in roles:
        raise Exception(
            f"No existe una referencia profesional para el rol {rol}."
        )

    return roles[rol]


# ============================================================
# PORCENTAJE RESPECTO A REFERENCIA
# ============================================================

def calcular_porcentaje_comparacion(
    valor_jugador,
    valor_referencia
):
    """
    Calcula qué porcentaje representa el valor del jugador
    con respecto al valor profesional.
    """

    valor_jugador = float(
        valor_jugador or 0
    )

    valor_referencia = float(
        valor_referencia or 0
    )

    if valor_referencia <= 0:
        return 0

    porcentaje = (
        valor_jugador
        / valor_referencia
    ) * 100

    return round(
        porcentaje,
        2
    )


# ============================================================
# DIFERENCIA PORCENTUAL
# ============================================================

def calcular_diferencia_porcentual(
    valor_jugador,
    valor_referencia
):
    """
    Calcula cuánto se encuentra el jugador por encima
    o por debajo de la referencia profesional.
    """

    valor_jugador = float(
        valor_jugador or 0
    )

    valor_referencia = float(
        valor_referencia or 0
    )

    if valor_referencia <= 0:
        return 0

    diferencia = (
        (
            valor_jugador
            - valor_referencia
        )
        / valor_referencia
    ) * 100

    return round(
        diferencia,
        2
    )


# ============================================================
# EXTRAER MÉTRICAS COMPARABLES
# ============================================================

def extraer_metricas_comparables(metricas_jugador):
    """
    Convierte la estructura completa de estadísticas
    en las seis métricas usadas en la comparación.
    """

    return {

        "win_rate":
            metricas_jugador[
                "resultados"
            ][
                "win_rate"
            ],

        "kda":
            metricas_jugador[
                "combate"
            ][
                "kda_promedio"
            ],

        "cs_por_minuto":
            metricas_jugador[
                "farmeo"
            ][
                "cs_por_minuto_promedio"
            ],

        "oro_por_minuto":
            metricas_jugador[
                "economia"
            ][
                "oro_por_minuto_promedio"
            ],

        "daño_por_minuto":
            metricas_jugador[
                "daño"
            ][
                "daño_por_minuto_promedio"
            ],

        "vision_score":
            metricas_jugador[
                "vision"
            ][
                "vision_score_promedio"
            ]
    }


# ============================================================
# COMPARAR CONTRA REFERENCIA PROFESIONAL
# ============================================================

def comparar_con_referencia(
    metricas_jugador,
    referencia_profesional
):
    """
    Compara las seis métricas principales del jugador
    contra el estándar profesional correspondiente a su rol.
    """

    jugador = extraer_metricas_comparables(
        metricas_jugador
    )

    resultados = {}

    for metrica, valor_jugador in jugador.items():

        valor_referencia = float(
            referencia_profesional.get(
                metrica,
                0
            ) or 0
        )

        diferencia = (
            float(valor_jugador)
            - valor_referencia
        )

        diferencia_porcentual = (
            calcular_diferencia_porcentual(
                valor_jugador,
                valor_referencia
            )
        )

        porcentaje_referencia = (
            calcular_porcentaje_comparacion(
                valor_jugador,
                valor_referencia
            )
        )

        if diferencia_porcentual >= 5:
            estado = "superior"

        elif diferencia_porcentual <= -5:
            estado = "inferior"

        else:
            estado = "similar"

        resultados[metrica] = {

            "nombre":
                NOMBRES_METRICAS.get(
                    metrica,
                    metrica
                ),

            "jugador":
                round(
                    float(valor_jugador),
                    2
                ),

            "referencia":
                round(
                    valor_referencia,
                    2
                ),

            "diferencia":
                round(
                    diferencia,
                    2
                ),

            "diferencia_porcentual":
                diferencia_porcentual,

            "porcentaje_referencia":
                porcentaje_referencia,

            "estado":
                estado
        }

    return resultados


# ============================================================
# CALCULAR SCORE GENERAL
# ============================================================

def calcular_score(comparacion):
    """
    Genera un indicador general de rendimiento
    entre 0 y 100.

    Alcanzar o superar el estándar profesional
    equivale a 100 puntos en una métrica.
    """

    if not comparacion:
        return 0

    puntuaciones = []

    for metrica in NOMBRES_METRICAS.keys():

        if metrica not in comparacion:
            continue

        porcentaje = float(
            comparacion[
                metrica
            ].get(
                "porcentaje_referencia",
                0
            ) or 0
        )

        puntuacion = max(
            0,
            min(
                porcentaje,
                100
            )
        )

        puntuaciones.append(
            puntuacion
        )

    if not puntuaciones:
        return 0

    score = (
        sum(puntuaciones)
        / len(puntuaciones)
    )

    return round(
        score,
        2
    )


# ============================================================
# CLASIFICACIÓN DEL SCORE
# ============================================================

def clasificar_score(score):
    """
    Devuelve una clasificación descriptiva
    para el score general.
    """

    score = float(
        score or 0
    )

    if score >= 90:
        return "Muy cercano al nivel profesional"

    if score >= 75:
        return "Rendimiento alto"

    if score >= 60:
        return "Rendimiento intermedio"

    if score >= 40:
        return "Rendimiento en desarrollo"

    return "Rendimiento inicial"


# ============================================================
# FORTALEZAS, DEBILIDADES Y MÉTRICAS SIMILARES
# ============================================================

def detectar_fortalezas_debilidades(comparacion):
    """
    Clasifica las métricas según su diferencia
    con la referencia profesional.

    >= +5%  -> fortaleza
    <= -5%  -> debilidad
    entre ambos -> similar
    """

    fortalezas = []
    debilidades = []
    similares = []

    for metrica, datos in comparacion.items():

        diferencia = float(
            datos.get(
                "diferencia_porcentual",
                0
            ) or 0
        )

        elemento = {
            "metrica": metrica,
            "nombre": NOMBRES_METRICAS.get(
                metrica,
                metrica
            ),
            "jugador": datos.get(
                "jugador"
            ),
            "referencia": datos.get(
                "referencia"
            ),
            "diferencia_porcentual": diferencia
        }

        if diferencia >= 5:

            fortalezas.append(
                elemento
            )

        elif diferencia <= -5:

            debilidades.append(
                elemento
            )

        else:

            similares.append(
                elemento
            )

    fortalezas.sort(
        key=lambda item:
            item["diferencia_porcentual"],
        reverse=True
    )

    debilidades.sort(
        key=lambda item:
            item["diferencia_porcentual"]
    )

    return {
        "fortalezas": fortalezas,
        "debilidades": debilidades,
        "similares": similares
    }


# ============================================================
# CAMPEÓN INSIGNIA
# ============================================================

def elegir_campeon_insignia(analisis_campeones):
    """
    Elige el campeón insignia a partir del análisis por campeón
    de las partidas del rol principal.

    1. Entre los campeones con al menos MINIMO_PARTIDAS partidas,
       el de mayor win rate (empate: el de más partidas).
    2. Si ninguno llega al mínimo, el más jugado
       (empate: el de mayor win rate).
    """

    MINIMO_PARTIDAS = 5

    if not analisis_campeones:

        return {
            "nombre": None,
            "partidas": 0,
            "win_rate": None,
            "criterio": None
        }

    candidatos = [
        campeon
        for campeon in analisis_campeones
        if campeon["partidas"] >= MINIMO_PARTIDAS
    ]

    if candidatos:

        elegido = max(
            candidatos,
            key=lambda campeon: (
                campeon["win_rate"],
                campeon["partidas"]
            )
        )

        criterio = "mejor_win_rate"

    else:

        elegido = max(
            analisis_campeones,
            key=lambda campeon: (
                campeon["partidas"],
                campeon["win_rate"]
            )
        )

        criterio = "mas_jugado"

    return {
        "nombre": elegido["campeon"]["nombre"],
        "partidas": elegido["partidas"],
        "win_rate": elegido["win_rate"],
        "criterio": criterio
    }


# ============================================================
# PARTICIPACIÓN EN KILLS
# ============================================================

def calcular_participacion_kills(partidas):
    """
    Devuelve la lista de participaciones en kills (fracción 0-1)
    de las partidas que permiten obtener el dato.

    - Usa combate.participacion_kills (challenges.killParticipation
      de Riot) si la partida lo trae.
    - Si no, la calcula con el bloque "equipos":
      (kills + asistencias del jugador) / kills de sus aliados.
      Si el equipo no hizo kills, toma 0.
    - Si tampoco hay "equipos", la partida se omite.
    """

    valores = []

    for partida in partidas:

        combate = partida.get(
            "combate",
            {}
        )

        participacion = combate.get(
            "participacion_kills"
        )

        if participacion is None:

            aliados = (
                partida.get("equipos")
                or {}
            ).get(
                "aliados"
            ) or []

            if not aliados:
                continue

            kills_equipo = sum(
                (aliado.get("combate") or {}).get("kills", 0) or 0
                for aliado in aliados
            )

            participacion = (
                (
                    (combate.get("kills", 0) or 0)
                    + (combate.get("asistencias", 0) or 0)
                )
                / kills_equipo
                if kills_equipo > 0
                else 0
            )

        valores.append(
            float(participacion)
        )

    return valores


# ============================================================
# MÉTRICAS ADICIONALES (SIN REFERENCIA PROFESIONAL)
# ============================================================

# Métricas que no existen en la referencia profesional; se
# comparan solo contra el promedio general del propio jugador.
# clave -> (nombre visible, unidad, menor_es_mejor)
METRICAS_ADICIONALES = {
    "participacion_kills": (
        "Participación en asesinatos", "%", False
    ),
    "porcentaje_daño_equipo": (
        "% del daño del equipo", "%", False
    ),
    "muertes_por_10_min": (
        "Muertes cada 10 minutos", "", True
    ),
    "vision_por_minuto": (
        "Visión por minuto", "", False
    ),
    "control_wards": (
        "Wards de control comprados", "", False
    ),
    "cs_10_minutos": (
        "CS a los 10 minutos", "", False
    ),
    "diferencia_oro_rival": (
        "Diferencia de oro con tu rival de línea "
        "(al final de la partida)",
        "",
        False
    ),
}


def calcular_porcentaje_daño_equipo(partida):
    """
    Fracción 0-1 del daño a campeones del equipo.

    - Usa combate.porcentaje_daño_equipo
      (challenges.teamDamagePercentage) si viene.
    - Si no, la calcula con el daño de los aliados guardado
      en "equipos" (el jugador está incluido en aliados).
    - Si tampoco hay "equipos", devuelve None.
    """

    porcentaje = (
        partida.get("combate") or {}
    ).get(
        "porcentaje_daño_equipo"
    )

    if porcentaje is not None:
        return float(porcentaje)

    aliados = (
        partida.get("equipos")
        or {}
    ).get(
        "aliados"
    ) or []

    if not aliados:
        return None

    daño_equipo = sum(
        (aliado.get("daño") or {}).get("campeones", 0) or 0
        for aliado in aliados
    )

    if daño_equipo <= 0:
        return 0.0

    daño_jugador = (
        partida.get("daño") or {}
    ).get(
        "daño_campeones",
        0
    ) or 0

    return daño_jugador / daño_equipo


def calcular_diferencia_oro_rival(partida):
    """
    Oro final del jugador menos el oro final del rival de su
    misma posición (tomado de equipos.rivales).
    None si no hay posición, equipos o rival.
    """

    posicion = (
        partida.get("partida") or {}
    ).get(
        "posicion"
    )

    if not posicion:
        return None

    rivales = (
        partida.get("equipos")
        or {}
    ).get(
        "rivales"
    ) or []

    rival = next(
        (
            participante
            for participante in rivales
            if participante.get("posicion") == posicion
        ),
        None
    )

    if rival is None:
        return None

    oro_jugador = (
        partida.get("economia") or {}
    ).get(
        "oro"
    )

    oro_rival = (
        rival.get("recursos") or {}
    ).get(
        "oro"
    )

    if oro_jugador is None or oro_rival is None:
        return None

    return float(oro_jugador) - float(oro_rival)


def obtener_valor_metrica_adicional(partida, metrica):
    """
    Valor de una métrica adicional en una partida,
    o None si la partida no trae el dato.
    """

    duracion = float(
        (
            partida.get("partida") or {}
        ).get(
            "duracion_minutos"
        ) or 0
    )

    if metrica == "participacion_kills":

        valores = calcular_participacion_kills([partida])

        return valores[0] * 100 if valores else None

    if metrica == "porcentaje_daño_equipo":

        valor = calcular_porcentaje_daño_equipo(partida)

        return valor * 100 if valor is not None else None

    if metrica == "muertes_por_10_min":

        muertes = (
            partida.get("combate") or {}
        ).get(
            "muertes"
        )

        if muertes is None or duracion <= 0:
            return None

        return float(muertes) / duracion * 10

    if metrica == "vision_por_minuto":

        vision = (
            partida.get("vision") or {}
        ).get(
            "vision_score"
        )

        if vision is None or duracion <= 0:
            return None

        return float(vision) / duracion

    if metrica == "control_wards":

        valor = (
            partida.get("vision") or {}
        ).get(
            "control_wards"
        )

        return float(valor) if valor is not None else None

    if metrica == "cs_10_minutos":

        valor = (
            partida.get("farmeo") or {}
        ).get(
            "cs_10_minutos"
        )

        return float(valor) if valor is not None else None

    if metrica == "diferencia_oro_rival":

        return calcular_diferencia_oro_rival(partida)

    return None


def calcular_metricas_adicionales(partidas):
    """
    Promedio de cada métrica adicional usando solo las partidas
    válidas que traen el dato. Si ninguna lo trae, valor = None
    (no se inventan valores).
    """

    partidas_validas = obtener_partidas_validas(partidas)

    resultado = {}

    for metrica, (nombre, unidad, menor_es_mejor) in (
        METRICAS_ADICIONALES.items()
    ):

        valores = [
            valor
            for valor in (
                obtener_valor_metrica_adicional(
                    partida,
                    metrica
                )
                for partida in partidas_validas
            )
            if valor is not None
        ]

        resultado[metrica] = {
            "nombre": nombre,
            "valor": (
                round(sum(valores) / len(valores), 2)
                if valores
                else None
            ),
            "unidad": unidad,
            "menor_es_mejor": menor_es_mejor,
            "partidas_con_dato": len(valores),
        }

    return resultado


def comparar_con_promedio_propio(
    metricas_campeon,
    metricas_generales
):
    """
    Compara las métricas adicionales del campeón insignia con
    los promedios generales del propio jugador.

    estado: "superior" (mejor), "inferior" (peor) o "similar",
    con el mismo umbral de ±5 %. En las métricas con
    menor_es_mejor el estado se invierte. Si falta alguno de
    los dos valores, diferencia y estado son None.
    """

    resultados = {}

    for metrica, datos_campeon in metricas_campeon.items():

        datos_generales = metricas_generales.get(
            metrica,
            {}
        )

        valor_jugador = datos_campeon.get("valor")
        valor_referencia = datos_generales.get("valor")
        menor_es_mejor = datos_campeon.get("menor_es_mejor", False)

        diferencia = None
        diferencia_porcentual = None
        estado = None

        if valor_jugador is not None and valor_referencia is not None:

            diferencia = round(
                valor_jugador - valor_referencia,
                2
            )

            # Se divide por el valor absoluto para que el signo
            # sea correcto con referencias negativas (diferencia
            # de oro).
            if valor_referencia != 0:

                diferencia_porcentual = round(
                    diferencia / abs(valor_referencia) * 100,
                    2
                )

            elif diferencia == 0:

                diferencia_porcentual = 0.0

            if diferencia_porcentual is not None:

                mejora = (
                    -diferencia_porcentual
                    if menor_es_mejor
                    else diferencia_porcentual
                )

                if mejora >= 5:
                    estado = "superior"

                elif mejora <= -5:
                    estado = "inferior"

                else:
                    estado = "similar"

        resultados[metrica] = {
            "nombre": datos_campeon.get("nombre"),
            "jugador": valor_jugador,
            "referencia": valor_referencia,
            "diferencia": diferencia,
            "diferencia_porcentual": diferencia_porcentual,
            "estado": estado,
            "unidad": datos_campeon.get("unidad"),
            "menor_es_mejor": menor_es_mejor,
            "partidas_con_dato": datos_campeon.get(
                "partidas_con_dato"
            ),
            "partidas_con_dato_referencia": datos_generales.get(
                "partidas_con_dato"
            ),
        }

    return resultados


# ============================================================
# ETIQUETAS DE CUALIDADES Y RESUMEN DEL JUGADOR
# ============================================================

def generar_etiquetas(comparacion, rol, partidas):
    """
    Genera las etiquetas de cualidades del jugador y una frase
    de resumen. Todas las reglas están en esta función y se
    basan en reglas fijas (sin inteligencia artificial).

    Devuelve:
        {
            "etiquetas": [{texto, tipo, motivo}],
            "resumen_jugador": str
        }
    """

    # --------------------------------------------------------
    # CONSTANTES
    # --------------------------------------------------------

    # Umbral frente a la referencia profesional del rol
    # (el mismo de fortalezas y debilidades).
    UMBRAL_PORCENTUAL = 5

    # Participación en kills (fracción 0-1).
    UMBRAL_PARTICIPACION_ALTA = 0.55
    UMBRAL_PARTICIPACION_BAJA = 0.40

    # Mínimo de partidas con el dato de participación
    # para mostrar su etiqueta.
    MINIMO_PARTIDAS_PARTICIPACION = 5

    # Con KDA bajo: "Muere mucho" solo si el promedio de muertes
    # por partida llega a este valor; si no, "KDA bajo".
    MUERTES_PARA_MUERE_MUCHO = 6

    MAXIMO_ETIQUETAS = 6

    NOMBRES_ROLES = {
        "TOP": "Top",
        "JUNGLE": "Jungla",
        "MID": "Mid",
        "ADC": "ADC",
        "SUPPORT": "Support"
    }

    nombre_rol = NOMBRES_ROLES.get(
        rol,
        rol
    )

    # --------------------------------------------------------
    # REGLAS FRENTE A LA REFERENCIA PROFESIONAL
    # --------------------------------------------------------
    # métrica: (nombre en el motivo,
    #           etiqueta positiva, frase positiva del resumen,
    #           etiqueta negativa, aspecto a mejorar del resumen)

    REGLAS_REFERENCIA = {
        "cs_por_minuto": (
            "CS/min",
            "Buen farmeo", "buen farmeo",
            "Farmeo bajo", "el farmeo"
        ),
        "daño_por_minuto": (
            "daño/min",
            "Mucho daño", "mucho daño",
            "Poco daño", "el daño"
        ),
        "vision_score": (
            "puntuación de visión",
            "Buen control de visión", "buen control de visión",
            "Poca visión", "la visión"
        ),
        "kda": (
            "KDA",
            "Juega seguro", "un juego seguro",
            "Muere mucho", "las muertes"
        ),
        "oro_por_minuto": (
            "oro/min",
            "Buena economía", "buena economía",
            "Economía baja", "la economía"
        ),
        "win_rate": (
            "win rate",
            "Gana seguido", "buen win rate",
            "Racha difícil", "el win rate"
        )
    }

    candidatas = []

    for metrica, regla in REGLAS_REFERENCIA.items():

        datos = comparacion.get(
            metrica
        )

        if not datos:
            continue

        (
            nombre_metrica,
            texto_positivo,
            frase_positiva,
            texto_negativo,
            aspecto_mejorar
        ) = regla

        diferencia = float(
            datos.get(
                "diferencia_porcentual",
                0
            ) or 0
        )

        if diferencia >= UMBRAL_PORCENTUAL:

            candidatas.append({
                "texto": texto_positivo,
                "tipo": "positiva",
                "motivo": (
                    f"Tu {nombre_metrica} es "
                    f"{abs(diferencia):.0f} % mayor que el "
                    f"promedio pro de {nombre_rol}"
                ),
                "diferencia": diferencia,
                "frase_resumen": frase_positiva
            })

        elif diferencia <= -UMBRAL_PORCENTUAL:

            # KDA bajo: distingue si el problema son las muertes.
            if metrica == "kda":

                muertes_promedio = (
                    sum(
                        (p.get("combate") or {}).get("muertes", 0) or 0
                        for p in partidas
                    )
                    / len(partidas)
                    if partidas
                    else 0
                )

                if muertes_promedio < MUERTES_PARA_MUERE_MUCHO:
                    texto_negativo = "KDA bajo"
                    aspecto_mejorar = "el KDA"

            candidatas.append({
                "texto": texto_negativo,
                "tipo": "negativa",
                "motivo": (
                    f"Tu {nombre_metrica} es "
                    f"{abs(diferencia):.0f} % menor que el "
                    f"promedio pro de {nombre_rol}"
                ),
                "diferencia": diferencia,
                "frase_resumen": aspecto_mejorar
            })

    # --------------------------------------------------------
    # REGLA DE PARTICIPACIÓN EN KILLS
    # --------------------------------------------------------
    # La referencia profesional no tiene este dato: se compara
    # contra umbrales fijos. Para ordenarla junto a las demás,
    # la diferencia se mide en % frente al umbral superado.

    participaciones = calcular_participacion_kills(
        partidas
    )

    if len(participaciones) >= MINIMO_PARTIDAS_PARTICIPACION:

        promedio = (
            sum(participaciones)
            / len(participaciones)
        )

        motivo = (
            f"Participas en el {promedio * 100:.0f} % "
            f"de las kills de tu equipo"
        )

        if promedio >= UMBRAL_PARTICIPACION_ALTA:

            candidatas.append({
                "texto": "Presente en las peleas",
                "tipo": "positiva",
                "motivo": motivo,
                "diferencia": (
                    (promedio - UMBRAL_PARTICIPACION_ALTA)
                    / UMBRAL_PARTICIPACION_ALTA
                    * 100
                ),
                "frase_resumen": "presencia en las peleas"
            })

        elif promedio <= UMBRAL_PARTICIPACION_BAJA:

            candidatas.append({
                "texto": "Poco presente en peleas",
                "tipo": "negativa",
                "motivo": motivo,
                "diferencia": (
                    (promedio - UMBRAL_PARTICIPACION_BAJA)
                    / UMBRAL_PARTICIPACION_BAJA
                    * 100
                ),
                "frase_resumen": "la participación en peleas"
            })

    # --------------------------------------------------------
    # ORDEN Y LÍMITE
    # --------------------------------------------------------
    # Primero las positivas con mayor diferencia y luego las
    # negativas con mayor diferencia (la más negativa primero).

    positivas = sorted(
        [e for e in candidatas if e["tipo"] == "positiva"],
        key=lambda e: e["diferencia"],
        reverse=True
    )

    negativas = sorted(
        [e for e in candidatas if e["tipo"] == "negativa"],
        key=lambda e: e["diferencia"]
    )

    seleccionadas = (
        positivas + negativas
    )[:MAXIMO_ETIQUETAS]

    # --------------------------------------------------------
    # RESUMEN DEL JUGADOR
    # --------------------------------------------------------
    # Usa hasta dos cualidades y dos aspectos a mejorar
    # de las etiquetas seleccionadas.

    def unir(frases):
        return " y ".join(frases)

    frases_positivas = [
        e["frase_resumen"]
        for e in seleccionadas
        if e["tipo"] == "positiva"
    ][:2]

    frases_mejorar = [
        e["frase_resumen"]
        for e in seleccionadas
        if e["tipo"] == "negativa"
    ][:2]

    if frases_positivas:
        inicio = (
            f"Jugador de {nombre_rol} con "
            f"{unir(frases_positivas)}"
        )

    else:
        inicio = (
            f"Jugador de {nombre_rol} sin fortalezas destacadas"
        )

    if len(frases_mejorar) == 1:
        final = f"; su punto a mejorar es {frases_mejorar[0]}."

    elif frases_mejorar:
        final = (
            f"; sus puntos a mejorar son "
            f"{unir(frases_mejorar)}."
        )

    elif frases_positivas:
        final = "; no muestra puntos débiles destacados."

    else:
        inicio = (
            f"Jugador de {nombre_rol} con un rendimiento "
            f"similar al promedio profesional en todas las métricas"
        )
        final = "."

    resumen_jugador = inicio + final

    # Solo se envían los campos públicos de cada etiqueta.
    etiquetas = [
        {
            "texto": e["texto"],
            "tipo": e["tipo"],
            "motivo": e["motivo"]
        }
        for e in seleccionadas
    ]

    return {
        "etiquetas": etiquetas,
        "resumen_jugador": resumen_jugador
    }


# ============================================================
# CATÁLOGO DE RECOMENDACIONES
# ============================================================

RUTA_RECOMENDACIONES = os.path.join(
    BASE_DIR,
    "data",
    "recomendaciones.json"
)

METRICAS_RECOMENDACION = {
    "kda",
    "cs_por_minuto",
    "oro_por_minuto",
    "daño_por_minuto",
    "vision_score",
    "win_rate",
    "general"
}

ROLES_RECOMENDACION = {
    "TODOS", "TOP", "JUNGLE", "MID", "ADC", "SUPPORT"
}

NIVELES_RECOMENDACION = {
    "leve", "moderada", "alta", "cualquiera", "sin_debilidades"
}

DATOS_CONDICION = {
    "muertes_promedio",
    "control_wards_promedio",
    "campeones_distintos_rol"
}

OPERADORES_CONDICION = {
    ">=": lambda a, b: a >= b,
    ">": lambda a, b: a > b,
    "<=": lambda a, b: a <= b,
    "<": lambda a, b: a < b,
    "==": lambda a, b: a == b
}

# Peso de cada métrica en el puntaje de prioridad.
PESOS_RECOMENDACION = {
    "kda": 1.2,
    "cs_por_minuto": 1.1,
    "vision_score": 1.0,
    "daño_por_minuto": 1.0,
    "oro_por_minuto": 0.9,
    "win_rate": 0.8
}

MAXIMO_RECOMENDACIONES = 6
MAXIMO_POR_METRICA = 2

_catalogo_recomendaciones = None


def _validar_recomendacion(item):
    """
    Devuelve None si la recomendación es válida
    o un texto con el motivo si no lo es.
    """

    if not isinstance(item, dict):
        return "no es un objeto"

    for campo in ("id", "titulo", "texto"):
        if not isinstance(item.get(campo), str) or not item[campo].strip():
            return f"campo '{campo}' ausente o vacío"

    if item.get("metrica") not in METRICAS_RECOMENDACION:
        return f"métrica desconocida: {item.get('metrica')}"

    roles = item.get("roles")

    if (
        not isinstance(roles, list)
        or not roles
        or any(rol not in ROLES_RECOMENDACION for rol in roles)
    ):
        return f"roles inválidos: {roles}"

    if item.get("nivel") not in NIVELES_RECOMENDACION:
        return f"nivel desconocido: {item.get('nivel')}"

    condicion = item.get("condicion")

    if condicion is not None:

        if (
            not isinstance(condicion, dict)
            or condicion.get("dato") not in DATOS_CONDICION
            or condicion.get("operador") not in OPERADORES_CONDICION
            or isinstance(condicion.get("valor"), bool)
            or not isinstance(condicion.get("valor"), (int, float))
        ):
            return f"condición inválida: {condicion}"

    return None


def cargar_catalogo_recomendaciones():
    """
    Carga y valida el catálogo de recomendaciones.
    Si el archivo falta o es inválido, registra el problema
    en el log y devuelve una lista vacía para que el
    análisis continúe sin recomendaciones.
    """

    global _catalogo_recomendaciones

    if _catalogo_recomendaciones is not None:
        return _catalogo_recomendaciones

    catalogo = []

    try:
        with open(RUTA_RECOMENDACIONES, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)

        items = (
            datos.get("recomendaciones")
            if isinstance(datos, dict)
            else None
        )

        if not isinstance(items, list):
            raise ValueError(
                "falta la lista 'recomendaciones'"
            )

        ids = set()

        for posicion, item in enumerate(items):

            error = _validar_recomendacion(item)

            if error is None and item["id"] in ids:
                error = f"id duplicado: {item['id']}"

            if error:
                print(
                    "[recomendaciones] Se omite la entrada "
                    f"{posicion}: {error}"
                )
                continue

            ids.add(item["id"])
            catalogo.append(item)

    except FileNotFoundError:
        print(
            "[recomendaciones] No se encontró el catálogo en "
            f"{RUTA_RECOMENDACIONES}. No se mostrarán recomendaciones."
        )

    except (json.JSONDecodeError, ValueError) as error:
        print(
            "[recomendaciones] Catálogo inválido "
            f"({error}). No se mostrarán recomendaciones."
        )

    _catalogo_recomendaciones = catalogo

    return catalogo


# ============================================================
# SELECCIONAR RECOMENDACIONES
# ============================================================

def calcular_nivel_brecha(brecha):
    """
    leve: 5 a <15 %, moderada: 15 a 30 %, alta: >30 %.
    """

    if brecha > 30:
        return "alta"

    if brecha >= 15:
        return "moderada"

    return "leve"


def calcular_datos_condicion(partidas_rol):
    """
    Datos usados por las condiciones del catálogo,
    calculados sobre las partidas válidas del rol principal.
    Si un dato no está disponible queda en None.
    """

    muertes = [
        float(m)
        for m in (
            (partida.get("combate") or {}).get("muertes")
            for partida in partidas_rol
        )
        if m is not None
    ]

    control_wards = [
        float(c)
        for c in (
            (partida.get("vision") or {}).get("control_wards")
            for partida in partidas_rol
        )
        if c is not None
    ]

    campeones = {
        nombre
        for nombre in (
            (partida.get("campeon") or {}).get("nombre")
            for partida in partidas_rol
        )
        if nombre
    }

    return {
        "muertes_promedio":
            sum(muertes) / len(muertes) if muertes else None,
        "control_wards_promedio":
            sum(control_wards) / len(control_wards)
            if control_wards else None,
        "campeones_distintos_rol":
            len(campeones) if campeones else None
    }


def condicion_cumplida(condicion, datos):
    """
    Evalúa la condición de una recomendación.
    Un dato no disponible se considera no cumplido.
    """

    valor = datos.get(condicion["dato"])

    if valor is None:
        return False

    return OPERADORES_CONDICION[condicion["operador"]](
        valor,
        condicion["valor"]
    )


def _formatear_recomendacion(item, diferencia_porcentual, puntaje):

    metrica = item["metrica"]

    return {
        "id": item["id"],
        "metrica": metrica,
        "nombre": NOMBRES_METRICAS.get(metrica, "General"),
        "diferencia_porcentual": diferencia_porcentual,
        "titulo": item["titulo"],
        "recomendacion": item["texto"],
        "puntaje": puntaje
    }


def seleccionar_recomendaciones(analisis, catalogo=None):
    """
    Elige recomendaciones del catálogo según las debilidades
    del jugador frente a la referencia profesional de su rol.

    analisis: {
        "comparacion": resultado de comparar_con_referencia,
        "rol_principal": rol del jugador,
        "partidas_rol": partidas válidas del rol principal
    }

    El resultado es determinista: mismo análisis,
    mismas recomendaciones.
    """

    if catalogo is None:
        catalogo = cargar_catalogo_recomendaciones()

    comparacion = analisis.get("comparacion") or {}
    rol = analisis.get("rol_principal")
    datos = calcular_datos_condicion(
        analisis.get("partidas_rol") or []
    )

    # Debilidades: diferencia <= -5 %, brecha en valor absoluto.
    debilidades = {}

    for metrica, valores in comparacion.items():

        diferencia = (valores or {}).get("diferencia_porcentual")

        if diferencia is not None and float(diferencia) <= -5:
            debilidades[metrica] = {
                "diferencia_porcentual": diferencia,
                "brecha": abs(float(diferencia))
            }

    # Sin debilidades: recomendaciones generales.
    if not debilidades:

        generales = sorted(
            (
                item for item in catalogo
                if item["nivel"] == "sin_debilidades"
            ),
            key=lambda item: item["id"]
        )[:3]

        seleccion = [
            _formatear_recomendacion(item, None, 0.0)
            for item in generales
        ]

    else:

        candidatas = []

        for item in catalogo:

            debilidad = debilidades.get(item["metrica"])

            if debilidad is None:
                continue

            especifica = "TODOS" not in item["roles"]

            if especifica and rol not in item["roles"]:
                continue

            nivel = calcular_nivel_brecha(debilidad["brecha"])

            if item["nivel"] not in (nivel, "cualquiera"):
                continue

            condicion = item.get("condicion")

            if condicion and not condicion_cumplida(condicion, datos):
                continue

            puntaje = (
                debilidad["brecha"]
                * PESOS_RECOMENDACION.get(item["metrica"], 1.0)
            )

            if especifica:
                puntaje += 10

            if condicion:
                puntaje += 15

            candidatas.append(
                _formatear_recomendacion(
                    item,
                    debilidad["diferencia_porcentual"],
                    round(puntaje, 2)
                )
            )

        candidatas.sort(
            key=lambda rec: (-rec["puntaje"], rec["id"])
        )

        seleccion = []
        por_metrica = Counter()

        for rec in candidatas:

            if por_metrica[rec["metrica"]] >= MAXIMO_POR_METRICA:
                continue

            seleccion.append(rec)
            por_metrica[rec["metrica"]] += 1

            if len(seleccion) >= MAXIMO_RECOMENDACIONES:
                break

    for posicion, rec in enumerate(seleccion):
        rec["prioridad"] = (
            "alta" if posicion < 2
            else "media" if posicion < 4
            else "baja"
        )

    return seleccion


# ============================================================
# ANÁLISIS POR CAMPEÓN
# ============================================================

def analizar_por_campeon(partidas):
    """
    Agrupa las partidas del jugador por campeón y calcula
    estadísticas de rendimiento para cada campeón utilizado.

    Métricas:
        - partidas
        - victorias
        - derrotas
        - win rate
        - KDA
        - CS por minuto
        - oro por minuto
        - daño por minuto
        - vision score
    """

    partidas_validas = obtener_partidas_validas(partidas)

    if not partidas_validas:
        return []

    # Versión actual de Data Dragon para los íconos
    version_iconos = obtener_version_data_dragon(
        version_parche_mas_reciente(partidas_validas)
    )

    # --------------------------------------------------------
    # AGRUPAR PARTIDAS POR CAMPEÓN
    # --------------------------------------------------------

    grupos_campeones = {}

    for partida in partidas_validas:

        campeon = partida.get(
            "campeon",
            {}
        )

        nombre_campeon = campeon.get(
            "nombre"
        )

        if not nombre_campeon:
            continue

        if nombre_campeon not in grupos_campeones:
            grupos_campeones[nombre_campeon] = []

        grupos_campeones[nombre_campeon].append(
            partida
        )

    # --------------------------------------------------------
    # CALCULAR ESTADÍSTICAS POR CAMPEÓN
    # --------------------------------------------------------

    resultado = []

    for nombre_campeon, partidas_campeon in grupos_campeones.items():

        estadisticas = calcular_promedios(
            partidas_campeon
        )

        cantidad = len(
            partidas_campeon
        )

        porcentaje_uso = (
            cantidad
            / len(partidas_validas)
        ) * 100

        resultado.append({

            "campeon": {
                "nombre":
                    nombre_campeon,

                "imagen_icono":
                    url_icono_campeon(
                        version_iconos,
                        nombre_campeon
                    ),

                "imagen_splash":
                    (
                        "https://ddragon.leagueoflegends.com/"
                        f"cdn/img/champion/splash/{nombre_campeon}_0.jpg"
                    )
            },

            "partidas":
                cantidad,

            "porcentaje_uso":
                round(
                    porcentaje_uso,
                    2
                ),

            "victorias":
                estadisticas[
                    "resultados"
                ][
                    "victorias"
                ],

            "derrotas":
                estadisticas[
                    "resultados"
                ][
                    "derrotas"
                ],

            "win_rate":
                estadisticas[
                    "resultados"
                ][
                    "win_rate"
                ],

            "kda":
                estadisticas[
                    "combate"
                ][
                    "kda_promedio"
                ],

            "kills_promedio":
                estadisticas[
                    "combate"
                ][
                    "kills_promedio"
                ],

            "muertes_promedio":
                estadisticas[
                    "combate"
                ][
                    "muertes_promedio"
                ],

            "asistencias_promedio":
                estadisticas[
                    "combate"
                ][
                    "asistencias_promedio"
                ],

            "cs_por_minuto":
                estadisticas[
                    "farmeo"
                ][
                    "cs_por_minuto_promedio"
                ],

            "oro_por_minuto":
                estadisticas[
                    "economia"
                ][
                    "oro_por_minuto_promedio"
                ],

            "daño_por_minuto":
                estadisticas[
                    "daño"
                ][
                    "daño_por_minuto_promedio"
                ],

            "vision_score":
                estadisticas[
                    "vision"
                ][
                    "vision_score_promedio"
                ]
        })

    # --------------------------------------------------------
    # ORDENAR POR CANTIDAD DE PARTIDAS
    # --------------------------------------------------------

    resultado.sort(
        key=lambda item: (
            item["partidas"],
            item["win_rate"]
        ),
        reverse=True
    )

    return resultado

# ============================================================
# ANÁLISIS POR POSICIÓN
# ============================================================

def analizar_por_posicion(partidas):
    """
    Calcula el rendimiento del jugador de forma independiente
    para cada posición utilizada en las partidas analizadas.

    Permite comparar:
        - cantidad de partidas
        - porcentaje de uso
        - victorias
        - derrotas
        - win rate
        - KDA
        - kills promedio
        - muertes promedio
        - asistencias promedio
        - CS por minuto
        - oro por minuto
        - daño por minuto
        - vision score
    """

    partidas_validas = obtener_partidas_validas(
        partidas
    )

    roles = [
        "TOP",
        "JUNGLE",
        "MID",
        "ADC",
        "SUPPORT"
    ]

    total_partidas = len(
        partidas_validas
    )

    resultado = {}


    for rol in roles:

        partidas_rol = filtrar_partidas_por_rol(
            partidas_validas,
            rol
        )

        cantidad = len(
            partidas_rol
        )


        # --------------------------------------------------------
        # SIN PARTIDAS EN EL ROL
        # --------------------------------------------------------

        if cantidad == 0:

            resultado[rol] = {

                "rol":
                    rol,

                "disponible":
                    False,

                "partidas":
                    0,

                "porcentaje":
                    0,

                "victorias":
                    0,

                "derrotas":
                    0,

                "win_rate":
                    0,

                "kda":
                    0,

                "kills_promedio":
                    0,

                "muertes_promedio":
                    0,

                "asistencias_promedio":
                    0,

                "cs_por_minuto":
                    0,

                "oro_por_minuto":
                    0,

                "daño_por_minuto":
                    0,

                "vision_score":
                    0
            }

            continue


        # --------------------------------------------------------
        # ESTADÍSTICAS DEL ROL
        # --------------------------------------------------------

        estadisticas = calcular_promedios(
            partidas_rol
        )


        porcentaje = (
            (
                cantidad
                / total_partidas
            )
            * 100
            if total_partidas > 0
            else 0
        )


        resultado[rol] = {

            "rol":
                rol,

            "disponible":
                True,

            "partidas":
                cantidad,

            "porcentaje":
                round(
                    porcentaje,
                    2
                ),

            "victorias":
                estadisticas[
                    "resultados"
                ][
                    "victorias"
                ],

            "derrotas":
                estadisticas[
                    "resultados"
                ][
                    "derrotas"
                ],

            "win_rate":
                estadisticas[
                    "resultados"
                ][
                    "win_rate"
                ],

            "kda":
                estadisticas[
                    "combate"
                ][
                    "kda_promedio"
                ],

            "kills_promedio":
                estadisticas[
                    "combate"
                ][
                    "kills_promedio"
                ],

            "muertes_promedio":
                estadisticas[
                    "combate"
                ][
                    "muertes_promedio"
                ],

            "asistencias_promedio":
                estadisticas[
                    "combate"
                ][
                    "asistencias_promedio"
                ],

            "cs_por_minuto":
                estadisticas[
                    "farmeo"
                ][
                    "cs_por_minuto_promedio"
                ],

            "oro_por_minuto":
                estadisticas[
                    "economia"
                ][
                    "oro_por_minuto_promedio"
                ],

            "daño_por_minuto":
                estadisticas[
                    "daño"
                ][
                    "daño_por_minuto_promedio"
                ],

            "vision_score":
                estadisticas[
                    "vision"
                ][
                    "vision_score_promedio"
                ]
        }


    return resultado


# ============================================================
# RENDIMIENTO POR ROL Y CAMPEÓN (sección interactiva)
# ============================================================

def resumir_partida(partida):
    """
    Resumen corto de una partida. El frontend abre la ventana
    de detalle con match_id (sin duplicar la partida completa).
    """

    datos_partida = partida.get("partida") or {}
    combate = partida.get("combate") or {}

    return {
        "match_id": datos_partida.get("match_id"),
        "victoria": (
            partida.get("resultado") or {}
        ).get("victoria", False),
        "kills": combate.get("kills", 0),
        "muertes": combate.get("muertes", 0),
        "asistencias": combate.get("asistencias", 0),
        "kda": round(
            float(combate.get("kda", 0) or 0),
            2
        ),
        "fecha": datos_partida.get("game_creation"),
        "duracion_minutos": datos_partida.get(
            "duracion_minutos"
        ),
    }


def analizar_roles_y_campeones(partidas, rol_principal):
    """
    Datos de la sección interactiva de roles y campeones.
    Solo usa partidas válidas (sin remakes).

    - 5 roles (TOP, JUNGLE, MID, ADC, SUPPORT) con partidas,
      % de uso (sobre las partidas con rol: suman 100 %) y
      promedios del rol.
    - Por rol, sus campeones: el insignia del rol primero
      (misma regla que elegir_campeon_insignia) y luego por
      partidas (empate: win rate).
    - Por campeón: promedios, participación en asesinatos,
      mejor y peor partida por KDA, siempre distintas
      (empate: la más reciente; con una sola partida,
      peor_partida = None) y sus
      últimas 5 partidas.
    """

    partidas_validas = obtener_partidas_validas(partidas)

    # La lista llega de la más reciente a la más antigua;
    # el índice desempata si falta game_creation.
    total = len(partidas_validas)

    recencia = {
        id(partida): (
            (partida.get("partida") or {}).get("game_creation")
            or 0,
            total - indice,
        )
        for indice, partida in enumerate(partidas_validas)
    }

    distribucion = obtener_distribucion_roles(
        partidas_validas
    )

    roles = []

    for rol in [
        "TOP",
        "JUNGLE",
        "MID",
        "ADC",
        "SUPPORT"
    ]:

        partidas_rol = filtrar_partidas_por_rol(
            partidas_validas,
            rol
        )

        datos_rol = {
            "rol": rol,
            "disponible": bool(partidas_rol),
            "es_principal": rol == rol_principal,
            "partidas": len(partidas_rol),
            "porcentaje_uso": round(
                distribucion[rol]["porcentaje"],
                1
            ),
            "victorias": 0,
            "derrotas": 0,
            "win_rate": 0,
            "kda": 0,
            "cs_por_minuto": 0,
            "daño_por_minuto": 0,
            "vision_score": 0,
            "campeones": [],
        }

        if not partidas_rol:
            roles.append(datos_rol)
            continue

        estadisticas = calcular_promedios(partidas_rol)

        datos_rol.update({
            "victorias":
                estadisticas["resultados"]["victorias"],
            "derrotas":
                estadisticas["resultados"]["derrotas"],
            "win_rate": round(
                estadisticas["resultados"]["win_rate"],
                1
            ),
            "kda": round(
                estadisticas["combate"]["kda_promedio"],
                2
            ),
            "cs_por_minuto":
                estadisticas["farmeo"]["cs_por_minuto_promedio"],
            "daño_por_minuto":
                estadisticas["daño"]["daño_por_minuto_promedio"],
            "vision_score":
                estadisticas["vision"]["vision_score_promedio"],
        })

        # ----------------------------------------------------
        # CAMPEONES DEL ROL
        # ----------------------------------------------------

        analisis_campeones = analizar_por_campeon(
            partidas_rol
        )

        insignia_rol = elegir_campeon_insignia(
            analisis_campeones
        )["nombre"]

        # analizar_por_campeon ya ordena por partidas
        # (empate: win rate); sort es estable.
        analisis_campeones.sort(
            key=lambda item:
                item["campeon"]["nombre"] != insignia_rol
        )

        campeones = []

        for item in analisis_campeones:

            nombre = item["campeon"]["nombre"]

            partidas_campeon = [
                partida
                for partida in partidas_rol
                if (partida.get("campeon") or {}).get("nombre")
                == nombre
            ]

            participaciones = calcular_participacion_kills(
                partidas_campeon
            )

            # Mejor: mayor KDA; peor: menor KDA (las dos son
            # partidas distintas). En empate, la más reciente.
            def kda_partida(partida):
                return float(
                    (partida.get("combate") or {}).get("kda", 0)
                    or 0
                )

            mejor = max(
                partidas_campeon,
                key=lambda partida: (
                    kda_partida(partida),
                    recencia[id(partida)]
                )
            )

            # La peor se elige entre las demás, para no
            # repetir la mejor si todas empatan en KDA.
            peor = (
                min(
                    [
                        partida
                        for partida in partidas_campeon
                        if partida is not mejor
                    ],
                    key=lambda partida: (
                        kda_partida(partida),
                        tuple(
                            -valor
                            for valor in recencia[id(partida)]
                        )
                    )
                )
                if len(partidas_campeon) > 1
                else None
            )

            ultimas = sorted(
                partidas_campeon,
                key=lambda partida: recencia[id(partida)],
                reverse=True
            )[:5]

            campeones.append({
                "campeon": {
                    "nombre": nombre,
                    "imagen_icono":
                        item["campeon"]["imagen_icono"],
                },
                "es_insignia": nombre == insignia_rol,
                "partidas": item["partidas"],
                "victorias": item["victorias"],
                "derrotas": item["derrotas"],
                "win_rate": round(item["win_rate"], 1),
                "kda": round(item["kda"], 2),
                "kills_promedio": item["kills_promedio"],
                "muertes_promedio": item["muertes_promedio"],
                "asistencias_promedio":
                    item["asistencias_promedio"],
                "cs_por_minuto": item["cs_por_minuto"],
                "oro_por_minuto": item["oro_por_minuto"],
                "daño_por_minuto": item["daño_por_minuto"],
                "vision_score": item["vision_score"],
                "participacion_kills": {
                    "valor": (
                        round(
                            sum(participaciones)
                            / len(participaciones)
                            * 100,
                            1
                        )
                        if participaciones
                        else None
                    ),
                    "partidas_con_dato": len(participaciones),
                },
                "mejor_partida": resumir_partida(mejor),
                "peor_partida": (
                    resumir_partida(peor)
                    if peor is not None
                    else None
                ),
                "ultimas_partidas": [
                    resumir_partida(partida)
                    for partida in ultimas
                ],
            })

        datos_rol["campeones"] = campeones

        roles.append(datos_rol)

    return {
        "rol_principal": rol_principal,
        "roles": roles,
    }


# ============================================================
# HU13 - DATOS PARA GRÁFICOS DE RENDIMIENTO
# ============================================================

def generar_datos_graficos(partidas):
    """
    Prepara la evolución del rendimiento del jugador
    para su visualización mediante gráficos.

    Las partidas recibidas deben corresponder al rol
    que se desea analizar.

    Genera por partida:
        - KDA
        - CS por minuto
        - oro por minuto
        - daño por minuto
        - vision score
        - resultado

    También calcula:
        - win rate acumulado
        - resumen mínimo, máximo y promedio
    """

    partidas_validas = obtener_partidas_validas(
        partidas
    )

    if not partidas_validas:

        return {
            "disponible": False,
            "cantidad_partidas": 0,
            "partidas": [],
            "resumen": {}
        }


    # ========================================================
    # ORDEN CRONOLÓGICO
    # ========================================================
    #
    # Riot devuelve normalmente las partidas desde la más
    # reciente hacia la más antigua.
    #
    # Para visualizar evolución:
    #
    # antigua -------------------------------> reciente
    #
    # invertimos la lista.
    # ========================================================

    partidas_cronologicas = list(
        reversed(
            partidas_validas
        )
    )


    # ========================================================
    # VARIABLES
    # ========================================================

    datos_graficos = []

    victorias_acumuladas = 0


    valores_kda = []
    valores_cs = []
    valores_oro = []
    valores_daño = []
    valores_vision = []


    # ========================================================
    # PROCESAR PARTIDAS
    # ========================================================

    for indice, partida in enumerate(
        partidas_cronologicas,
        start=1
    ):

        datos_partida = partida.get(
            "partida",
            {}
        )

        resultado = partida.get(
            "resultado",
            {}
        )

        campeon = partida.get(
            "campeon",
            {}
        )

        combate = partida.get(
            "combate",
            {}
        )

        farmeo = partida.get(
            "farmeo",
            {}
        )

        economia = partida.get(
            "economia",
            {}
        )

        daño = partida.get(
            "daño",
            {}
        )

        vision = partida.get(
            "vision",
            {}
        )


        # ----------------------------------------------------
        # RESULTADO
        # ----------------------------------------------------

        victoria = bool(
            resultado.get(
                "victoria",
                False
            )
        )


        if victoria:
            victorias_acumuladas += 1


        win_rate_acumulado = (
            victorias_acumuladas
            / indice
        ) * 100


        # ----------------------------------------------------
        # MÉTRICAS
        # ----------------------------------------------------

        kda = float(
            combate.get(
                "kda",
                0
            ) or 0
        )

        cs_por_minuto = float(
            farmeo.get(
                "cs_por_minuto",
                0
            ) or 0
        )

        oro_por_minuto = float(
            economia.get(
                "oro_por_minuto",
                0
            ) or 0
        )

        daño_por_minuto = float(
            daño.get(
                "daño_por_minuto",
                0
            ) or 0
        )

        vision_score = float(
            vision.get(
                "vision_score",
                0
            ) or 0
        )


        # ----------------------------------------------------
        # GUARDAR PARA RESUMEN
        # ----------------------------------------------------

        valores_kda.append(
            kda
        )

        valores_cs.append(
            cs_por_minuto
        )

        valores_oro.append(
            oro_por_minuto
        )

        valores_daño.append(
            daño_por_minuto
        )

        valores_vision.append(
            vision_score
        )


        # ----------------------------------------------------
        # REGISTRO DEL GRÁFICO
        # ----------------------------------------------------

        datos_graficos.append({

            "numero":
                indice,

            "match_id":
                datos_partida.get(
                    "match_id"
                ),

            "campeon":
                campeon.get(
                    "nombre",
                    "Desconocido"
                ),

            "victoria":
                victoria,

            "kda":
                round(
                    kda,
                    2
                ),

            "cs_por_minuto":
                round(
                    cs_por_minuto,
                    2
                ),

            "oro_por_minuto":
                round(
                    oro_por_minuto,
                    2
                ),

            "daño_por_minuto":
                round(
                    daño_por_minuto,
                    2
                ),

            "vision_score":
                round(
                    vision_score,
                    2
                ),

            "win_rate_acumulado":
                round(
                    win_rate_acumulado,
                    2
                )
        })


    # ========================================================
    # FUNCIÓN INTERNA PARA RESUMEN
    # ========================================================

    def calcular_resumen(
        valores
    ):

        if not valores:

            return {
                "promedio": 0,
                "minimo": 0,
                "maximo": 0
            }


        return {

            "promedio":
                round(
                    sum(valores)
                    / len(valores),
                    2
                ),

            "minimo":
                round(
                    min(valores),
                    2
                ),

            "maximo":
                round(
                    max(valores),
                    2
                )
        }


    # ========================================================
    # RESPUESTA
    # ========================================================

    return {

        "disponible":
            True,

        "cantidad_partidas":
            len(
                datos_graficos
            ),

        "orden":
            "cronologico",

        "partidas":
            datos_graficos,

        "resumen": {

            "kda":
                calcular_resumen(
                    valores_kda
                ),

            "cs_por_minuto":
                calcular_resumen(
                    valores_cs
                ),

            "oro_por_minuto":
                calcular_resumen(
                    valores_oro
                ),

            "daño_por_minuto":
                calcular_resumen(
                    valores_daño
                ),

            "vision_score":
                calcular_resumen(
                    valores_vision
                )
        }
    }

# ============================================================
# ANÁLISIS COMPLETO DEL JUGADOR
# ============================================================

def analizar_jugador_con_referencia(
    partidas,
    puuid=None,
    nombre=None,
    tag=None,
    rango=None
):
    """
    Función principal del análisis individual del jugador.

    Flujo:

    1. Valida partidas.
    2. Determina el rol principal.
    3. Filtra partidas de ese rol.
    4. Calcula estadísticas.
    5. Determina campeón insignia.
    6. Prepara partidas recientes para frontend.
    7. Carga referencia profesional.
    8. Compara métricas.
    9. Calcula score.
    10. Detecta fortalezas y debilidades.
    11. Genera recomendaciones.
    """

    # ========================================================
    # PARTIDAS VÁLIDAS
    # ========================================================

    partidas_validas = obtener_partidas_validas(
        partidas
    )

    if not partidas_validas:
        raise Exception(
            "No existen partidas válidas para analizar al jugador."
        )

    # Versión actual de Data Dragon para los íconos
    version_iconos = obtener_version_data_dragon(
        version_parche_mas_reciente(partidas_validas)
    )


    # ========================================================
    # DISTRIBUCIÓN DE ROLES
    # ========================================================

    distribucion_roles = obtener_distribucion_roles(
        partidas_validas
    )

    # ========================================================
    # ANÁLISIS POR POSICIÓN
    # ========================================================

    analisis_posiciones = analizar_por_posicion(
        partidas_validas
    )


    # ========================================================
    # ROL PRINCIPAL
    # ========================================================

    rol_principal = determinar_rol_principal(
        partidas_validas
    )


    # ========================================================
    # SECCIÓN INTERACTIVA: ROLES Y CAMPEONES
    # ========================================================

    rendimiento_roles = analizar_roles_y_campeones(
        partidas_validas,
        rol_principal
    )


    # ========================================================
    # PARTIDAS DEL ROL PRINCIPAL
    # ========================================================

    partidas_rol = filtrar_partidas_por_rol(
        partidas_validas,
        rol_principal
    )

    if not partidas_rol:
        raise Exception(
            f"No existen partidas válidas para el rol {rol_principal}."
        )


    # ========================================================
    # ESTADÍSTICAS DEL JUGADOR
    # ========================================================

    estadisticas = calcular_promedios(
        partidas_rol
    )

    # ========================================================
    # GRÁFICOS DE RENDIMIENTO
    # ========================================================

    graficos_rendimiento = generar_datos_graficos(
        partidas_rol
    )

    # ========================================================
    # MINERÍA DE DATOS - K-MEANS
    # ========================================================

    mineria_datos = analizar_patrones_kmeans(
        partidas_rol
    )

    # ========================================================
    # ANÁLISIS POR CAMPEÓN
    # ========================================================
    
    analisis_campeones = analizar_por_campeon(
        partidas_rol
    )


    # ========================================================
    # CAMPEÓN INSIGNIA
    # ========================================================

    seleccion_insignia = elegir_campeon_insignia(
        analisis_campeones
    )

    campeon_insignia = seleccion_insignia["nombre"]
    partidas_campeon_insignia = seleccion_insignia["partidas"]
    win_rate_campeon_insignia = seleccion_insignia["win_rate"]
    criterio_campeon_insignia = seleccion_insignia["criterio"]


    # ========================================================
    # ESTADÍSTICAS DEL CAMPEÓN INSIGNIA
    # ========================================================

    partidas_insignia = []

    if campeon_insignia:

        for partida in partidas_rol:

            nombre_campeon = (
                partida
                .get(
                    "campeon",
                    {}
                )
                .get(
                    "nombre"
                )
            )

            if nombre_campeon == campeon_insignia:
                partidas_insignia.append(
                    partida
                )


    if partidas_insignia:

        estadisticas_campeon_insignia = (
            calcular_promedios(
                partidas_insignia
            )
        )

    else:

        estadisticas_campeon_insignia = None


    # ========================================================
    # PARTIDAS RECIENTES PARA EL FRONTEND
    # ========================================================

    partidas_recientes = []


    # El historial incluye los remakes, marcados con "remake".
    for partida in obtener_partidas_historial(partidas):

        # ----------------------------------------------------
        # BLOQUES PRINCIPALES
        # ----------------------------------------------------

        datos_partida = partida.get(
            "partida",
            {}
        )

        resultado = partida.get(
            "resultado",
            {}
        )

        campeon = partida.get(
            "campeon",
            {}
        )

        combate = partida.get(
            "combate",
            {}
        )

        farmeo = partida.get(
            "farmeo",
            {}
        )

        economia = partida.get(
            "economia",
            {}
        )

        daño = partida.get(
            "daño",
            {}
        )

        vision = partida.get(
            "vision",
            {}
        )

        rival_rol = partida.get(
            "rival_rol",
            {}
        )


        # ----------------------------------------------------
        # CAMPEÓN DEL JUGADOR
        # ----------------------------------------------------

        nombre_campeon = campeon.get(
            "nombre",
            "Desconocido"
        )


        # ----------------------------------------------------
        # ROL NORMALIZADO DEL JUGADOR
        # ----------------------------------------------------

        rol_partida = normalizar_rol(
            datos_partida.get(
                "posicion"
            )
        )


        # ----------------------------------------------------
        # RIVAL DEL MISMO ROL
        # ----------------------------------------------------

        rival_frontend = None


        if isinstance(
            rival_rol,
            dict
        ):

            rival_campeon = rival_rol.get(
                "campeon",
                {}
            )

            rival_combate = rival_rol.get(
                "combate",
                {}
            )

            rival_resultado = rival_rol.get(
                "resultado",
                {}
            )

            nombre_campeon_rival = (
                rival_campeon.get(
                    "nombre"
                )
            )


            rival_frontend = {

                "puuid":
                    rival_rol.get(
                        "puuid"
                    ),

                "nombre":
                    rival_rol.get(
                        "nombre"
                    ),

                "tag":
                    rival_rol.get(
                        "tag"
                    ),

                "team_id":
                    rival_rol.get(
                        "team_id"
                    ),

                "rol":
                    normalizar_rol(
                        rival_rol.get(
                            "posicion"
                        )
                    ),

                "campeon": {

                    "id":
                        rival_campeon.get(
                            "id"
                        ),

                    "nombre":
                        nombre_campeon_rival,

                    "nivel":
                        rival_campeon.get(
                            "nivel",
                            0
                        ),

                    "imagen_icono":
                        url_icono_campeon(
                            version_iconos,
                            nombre_campeon_rival
                        ),

                    "imagen_splash":
                        (
                            "https://ddragon.leagueoflegends.com/"
                            f"cdn/img/champion/splash/{nombre_campeon_rival}_0.jpg"
                            if nombre_campeon_rival
                            else None
                        )
                },

                "combate": {

                    "kills":
                        rival_combate.get(
                            "kills",
                            0
                        ),

                    "muertes":
                        rival_combate.get(
                            "muertes",
                            0
                        ),

                    "asistencias":
                        rival_combate.get(
                            "asistencias",
                            0
                        ),

                    "kda":
                        rival_combate.get(
                            "kda",
                            0
                        )
                },

                "resultado": {

                    "victoria":
                        rival_resultado.get(
                            "victoria",
                            False
                        )
                }
            }


        # ----------------------------------------------------
        # RESPUESTA DE LA PARTIDA RECIENTE
        # ----------------------------------------------------

        partidas_recientes.append({

            "match_id":
                datos_partida.get(
                    "match_id"
                ),

            "modo":
                datos_partida.get(
                    "modo"
                ),

            "queue_id":
                datos_partida.get(
                    "queue_id"
                ),

            "rol":
                rol_partida,

            "duracion_segundos":
                datos_partida.get(
                    "duracion_segundos",
                    0
                ),

            "duracion_minutos":
                datos_partida.get(
                    "duracion_minutos",
                    0
                ),

            "victoria":
                resultado.get(
                    "victoria",
                    False
                ),

            "campeon": {

                "id":
                    campeon.get(
                        "id"
                    ),

                "nombre":
                    nombre_campeon,

                "nivel":
                    campeon.get(
                        "nivel",
                        0
                    ),

                "imagen_icono":
                    url_icono_campeon(
                        version_iconos,
                        nombre_campeon
                    ),

                "imagen_splash":
                    (
                        "https://ddragon.leagueoflegends.com/"
                        f"cdn/img/champion/splash/{nombre_campeon}_0.jpg"
                    )
            },

            "combate": {

                "kills":
                    combate.get(
                        "kills",
                        0
                    ),

                "muertes":
                    combate.get(
                        "muertes",
                        0
                    ),

                "asistencias":
                    combate.get(
                        "asistencias",
                        0
                    ),

                "kda":
                    combate.get(
                        "kda",
                        0
                    )
            },

            "farmeo": {

                "cs":
                    farmeo.get(
                        "cs",
                        0
                    ),

                "cs_por_minuto":
                    farmeo.get(
                        "cs_por_minuto",
                        0
                    )
            },

            "economia": {

                "oro":
                    economia.get(
                        "oro",
                        0
                    ),

                "oro_por_minuto":
                    economia.get(
                        "oro_por_minuto",
                        0
                    )
            },

            "daño": {

                "daño_campeones":
                    daño.get(
                        "daño_campeones",
                        0
                    ),

                "daño_por_minuto":
                    daño.get(
                        "daño_por_minuto",
                        0
                    )
            },

            "vision": {

                "vision_score":
                    vision.get(
                        "vision_score",
                        0
                    )
            },

            # Los 10 participantes ya no se envían aquí: el
            # detalle se pide a GET /api/partida/{match_id}.
            "rival_rol":
                rival_frontend,

            "remake":
                bool(
                    partida.get(
                        "remake",
                        False
                    )
                )
        })


    # ========================================================
    # FORMA RECIENTE (SIN REMAKES)
    # ========================================================

    partidas_forma_reciente = [
        partida
        for partida in partidas_recientes
        if not partida["remake"]
    ][:10]
    
    forma_reciente = []
    
    for partida in partidas_forma_reciente:
        forma_reciente.append(
            "V"
            if partida["victoria"]
            else "D"
        )
    
        victorias_recientes = sum(
        1
        for partida in partidas_forma_reciente
        if partida["victoria"]
        )

        derrotas_recientes = (
            len(partidas_forma_reciente)
            - victorias_recientes
        )
    # ========================================================
    # REFERENCIA PROFESIONAL
    # ========================================================

    datos_referencia = cargar_referencia_profesional()

    referencia_rol = obtener_referencia_por_rol(
        rol_principal
    )


    # ========================================================
    # COMPARACIÓN
    # ========================================================

    comparacion = comparar_con_referencia(
        estadisticas,
        referencia_rol
    )


    # ========================================================
    # MÉTRICAS ADICIONALES Y COMPARACIONES DEL INSIGNIA
    # ========================================================
    # No alimentan el score ni las fortalezas/debilidades.

    # Promedios generales: todas las partidas válidas.
    metricas_adicionales = calcular_metricas_adicionales(
        partidas_validas
    )

    if partidas_insignia:

        comparacion_profesional_insignia = (
            comparar_con_referencia(
                estadisticas_campeon_insignia,
                referencia_rol
            )
        )

        comparacion_adicional_insignia = (
            comparar_con_promedio_propio(
                calcular_metricas_adicionales(
                    partidas_insignia
                ),
                metricas_adicionales
            )
        )

    else:

        comparacion_profesional_insignia = None
        comparacion_adicional_insignia = None


    # ========================================================
    # SCORE
    # ========================================================

    score = calcular_score(
        comparacion
    )

    clasificacion = clasificar_score(
        score
    )


    # ========================================================
    # FORTALEZAS / DEBILIDADES
    # ========================================================

    evaluacion = detectar_fortalezas_debilidades(
        comparacion
    )


    # ========================================================
    # RECOMENDACIONES
    # ========================================================

    recomendaciones = seleccionar_recomendaciones({
        "comparacion": comparacion,
        "rol_principal": rol_principal,
        "partidas_rol": partidas_rol
    })


    # ========================================================
    # ETIQUETAS DE CUALIDADES Y RESUMEN
    # ========================================================

    perfil_jugador = generar_etiquetas(
        comparacion,
        rol_principal,
        partidas_rol
    )


    # ========================================================
    # RESPUESTA FINAL
    # ========================================================

    return {

        # ----------------------------------------------------
        # JUGADOR
        # ----------------------------------------------------

        "jugador": {

            "puuid":
                puuid,

            "nombre":
                nombre,

            "tag":
                tag,

            "riot_id":
                (
                    f"{nombre}#{tag}"
                    if nombre and tag
                    else None
                ),
            "rango":
               rango
        },


        # ----------------------------------------------------
        # CAMPEÓN INSIGNIA
        # ----------------------------------------------------

        "campeon_insignia": {

            "nombre":
                campeon_insignia,

            "partidas":
                partidas_campeon_insignia,

            "win_rate":
                win_rate_campeon_insignia,

            # "mejor_win_rate" o "mas_jugado"
            "criterio":
                criterio_campeon_insignia,

            "imagen_icono":
                url_icono_campeon(
                    version_iconos,
                    campeon_insignia
                ),

            "imagen_splash":
                (
                    "https://ddragon.leagueoflegends.com/"
                    f"cdn/img/champion/splash/{campeon_insignia}_0.jpg"
                    if campeon_insignia
                    else None
                ),

            "estadisticas":
                estadisticas_campeon_insignia,

            # 6 métricas del insignia vs referencia del rol.
            "comparacion_profesional":
                comparacion_profesional_insignia,

            # Métricas sin referencia profesional:
            # insignia vs promedios generales del jugador.
            "comparacion_adicional":
                comparacion_adicional_insignia
        },


        # ----------------------------------------------------
        # MÉTRICAS ADICIONALES (promedios generales)
        # ----------------------------------------------------

        "metricas_adicionales":
            metricas_adicionales,


        # ----------------------------------------------------
        # MUESTRA
        # ----------------------------------------------------

        "muestra": {

            "partidas_obtenidas":
                len(partidas_validas),

            "partidas_analizadas":
                len(partidas_rol),

            "rol_principal":
                rol_principal,

            "distribucion_roles":
                distribucion_roles
        },


        # ----------------------------------------------------
        # FORMA RECIENTE
        # ----------------------------------------------------

        "forma_reciente": {

            "resultados":
                forma_reciente,

            "victorias":
                victorias_recientes,

            "derrotas":
                derrotas_recientes,

            "cantidad":
                len(partidas_forma_reciente)
        },


        # ----------------------------------------------------
        # PARTIDAS RECIENTES
        # ----------------------------------------------------

        "partidas_recientes":
            partidas_recientes,


        # ----------------------------------------------------
        # REFERENCIA PROFESIONAL
        # ----------------------------------------------------

        "referencia_profesional": {

            "fuente":
                datos_referencia.get(
                    "fuente"
                ),

            "dataset":
                datos_referencia.get(
                    "dataset"
                ),

            "temporada":
                datos_referencia.get(
                    "temporada"
                ),

            "tipo_referencia":
                datos_referencia.get(
                    "tipo_referencia"
                ),

            "ligas":
                datos_referencia.get(
                    "ligas",
                    []
                ),

            "rol":
                rol_principal,

            "partidas_referencia":
                referencia_rol.get(
                    "partidas"
                ),

            "metricas": {

                "win_rate":
                    referencia_rol.get(
                        "win_rate"
                    ),

                "kda":
                    referencia_rol.get(
                        "kda"
                    ),

                "cs_por_minuto":
                    referencia_rol.get(
                        "cs_por_minuto"
                    ),

                "oro_por_minuto":
                    referencia_rol.get(
                        "oro_por_minuto"
                    ),

                "daño_por_minuto":
                    referencia_rol.get(
                        "daño_por_minuto"
                    ),

                "vision_score":
                    referencia_rol.get(
                        "vision_score"
                    )
            }
        },


        # ----------------------------------------------------
        # ESTADÍSTICAS DEL JUGADOR
        # ----------------------------------------------------

        "estadisticas_jugador":
            estadisticas,
        # ----------------------------------------------------
        # ANÁLISIS POR POSICIÓN
        # ----------------------------------------------------

        "analisis_posiciones":
            analisis_posiciones,

        # Sección interactiva de roles y campeones
        # (solo partidas válidas).
        "rendimiento_roles":
            rendimiento_roles,

        # ----------------------------------------------------
        # ANÁLISIS POR CAMPEÓN
        # ----------------------------------------------------
        
        "analisis_campeones":
           analisis_campeones,

        # ========================================================
        # GRÁFICOS DE RENDIMIENTO
        # ========================================================

        "graficos_rendimiento":
            graficos_rendimiento,

            
        # ----------------------------------------------------
        # MINERÍA DE DATOS - K-MEANS
        # ----------------------------------------------------

        "mineria_datos":
            mineria_datos,

        # ----------------------------------------------------
        # COMPARACIÓN
        # ----------------------------------------------------

        "comparacion":
            comparacion,


        # ----------------------------------------------------
        # SCORE
        # ----------------------------------------------------

        "score": {

            "valor":
                score,

            "maximo":
                100,

            "clasificacion":
                clasificacion
        },


        # ----------------------------------------------------
        # FORTALEZAS
        # ----------------------------------------------------

        "fortalezas":
            evaluacion[
                "fortalezas"
            ],


        # ----------------------------------------------------
        # DEBILIDADES
        # ----------------------------------------------------

        "debilidades":
            evaluacion[
                "debilidades"
            ],


        # ----------------------------------------------------
        # MÉTRICAS SIMILARES
        # ----------------------------------------------------

        "metricas_similares":
            evaluacion[
                "similares"
            ],


        # ----------------------------------------------------
        # RECOMENDACIONES
        # ----------------------------------------------------

        "recomendaciones":
            recomendaciones,


        # ----------------------------------------------------
        # ETIQUETAS Y RESUMEN DEL JUGADOR
        # ----------------------------------------------------

        "etiquetas":
            perfil_jugador[
                "etiquetas"
            ],

        "resumen_jugador":
            perfil_jugador[
                "resumen_jugador"
            ]
    }
