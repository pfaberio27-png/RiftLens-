from collections import Counter

import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


VARIABLES_KMEANS = [
    "kda",
    "cs_por_minuto",
    "oro_por_minuto",
    "daño_por_minuto",
    "vision_score",
]


# Mínimo de partidas del rol principal para mostrar los estilos.
MINIMO_PARTIDAS_KMEANS = 10

# Distancia (en desviaciones estándar respecto al promedio del
# propio jugador) a partir de la cual una variable "se aleja".
UMBRAL_Z_ESTILO = 0.5

# Si ninguna variable se aleja, la media decide si el grupo
# está algo por encima o por debajo del nivel del jugador.
UMBRAL_Z_NIVEL = 0.15


# Palabras para nombrar cada variable en lenguaje sencillo:
# (cuantificador si sube, cuantificador si baja, sustantivo).
# Mismo orden que VARIABLES_KMEANS.
PALABRAS_VARIABLES = [
    ("mejor", "peor", "KDA"),
    ("más", "menos", "farmeo"),
    ("más", "menos", "oro"),
    ("más", "menos", "daño"),
    ("más", "menos", "visión"),
]


def _obtener_numero(valor, default=0.0):
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return default


def extraer_vector_partida(partida):
    """
    Convierte una partida en un vector numérico
    para ser utilizado por K-Means.

    Variables:
        - KDA
        - CS por minuto
        - Oro por minuto
        - Daño por minuto
        - Vision Score
    """

    combate = partida.get("combate", {})
    farmeo = partida.get("farmeo", {})
    economia = partida.get("economia", {})
    dano = partida.get("daño", {})
    vision = partida.get("vision", {})

    return [
        _obtener_numero(
            combate.get("kda")
        ),
        _obtener_numero(
            farmeo.get("cs_por_minuto")
        ),
        _obtener_numero(
            economia.get("oro_por_minuto")
        ),
        _obtener_numero(
            dano.get("daño_por_minuto")
        ),
        _obtener_numero(
            vision.get("vision_score")
        ),
    ]


def preparar_datos_kmeans(partidas):
    """
    Extrae la matriz de características de las partidas.
    """

    matriz = []
    indices_validos = []

    for indice, partida in enumerate(partidas):

        if not isinstance(partida, dict):
            continue

        if "error" in partida:
            continue

        vector = extraer_vector_partida(
            partida
        )

        if not all(
            np.isfinite(valor)
            for valor in vector
        ):
            continue

        matriz.append(
            vector
        )

        indices_validos.append(
            indice
        )

    if not matriz:
        return (
            np.empty((0, len(VARIABLES_KMEANS))),
            []
        )

    return (
        np.array(
            matriz,
            dtype=float
        ),
        indices_validos
    )


def evaluar_numero_clusters(
    datos_normalizados,
    max_clusters=6
):
    """
    Evalúa diferentes valores de K mediante
    Silhouette Score.

    Retorna:
        - mejor número de clusters
        - resultados de evaluación
    """

    cantidad = len(
        datos_normalizados
    )

    # Se necesitan suficientes observaciones
    # para evaluar varios clusters.
    if cantidad < 3:
        return None, []

    limite_superior = min(
        max_clusters,
        cantidad - 1
    )

    resultados = []

    mejor_k = None
    mejor_score = -1

    for k in range(
        2,
        limite_superior + 1
    ):

        modelo = KMeans(
            n_clusters=k,
            random_state=42,
            n_init=10
        )

        etiquetas = modelo.fit_predict(
            datos_normalizados
        )

        # Silhouette requiere por lo menos
        # dos clusters realmente presentes.
        if len(set(etiquetas)) < 2:
            continue

        score = silhouette_score(
            datos_normalizados,
            etiquetas
        )

        resultados.append({
            "k": k,
            "silhouette_score": round(
                float(score),
                4
            ),
            "inercia": round(
                float(modelo.inertia_),
                4
            )
        })

        if score > mejor_score:

            mejor_score = score
            mejor_k = k

    return (
        mejor_k,
        resultados
    )


def _calcular_promedio_cluster(
    datos_originales,
    indices
):
    """
    Calcula el centro interpretable de un cluster
    utilizando las unidades originales.
    """

    subconjunto = datos_originales[
        indices
    ]

    promedio = np.mean(
        subconjunto,
        axis=0
    )

    return {
        "kda":
            round(
                float(promedio[0]),
                2
            ),

        "cs_por_minuto":
            round(
                float(promedio[1]),
                2
            ),

        "oro_por_minuto":
            round(
                float(promedio[2]),
                2
            ),

        "daño_por_minuto":
            round(
                float(promedio[3]),
                2
            ),

        "vision_score":
            round(
                float(promedio[4]),
                2
            )
    }


# ============================================================
# INTERPRETACIÓN DE LOS GRUPOS (no interviene en el agrupamiento)
# ============================================================

def _frase_variable(indice, z):
    """
    Devuelve (cuantificador, sustantivo) de una variable
    según si el grupo está por encima o por debajo.
    """

    sube, baja, sustantivo = PALABRAS_VARIABLES[indice]

    return (
        sube if z >= 0 else baja,
        sustantivo
    )


def _unir_frases(frases):
    """
    Une frases (cuantificador, sustantivo):
        - dos con el mismo cuantificador: "más daño y farmeo"
        - en otro caso: "mejor KDA, más daño y menos visión"
    """

    if (
        len(frases) == 2
        and frases[0][0] == frases[1][0]
    ):
        return (
            f"{frases[0][0]} {frases[0][1]} "
            f"y {frases[1][1]}"
        )

    textos = [
        f"{cuantificador} {sustantivo}"
        for cuantificador, sustantivo in frases
    ]

    if len(textos) == 1:
        return textos[0]

    return (
        ", ".join(textos[:-1])
        + " y "
        + textos[-1]
    )


def _tipo_estilo(z):
    """
    Clasifica el grupo según su z-score medio:
    dominante, complicada, por encima / por debajo de su
    nivel, equilibrada o por variables.
    """

    media = float(np.mean(z))

    positivas = int(np.sum(z > 0))
    negativas = int(np.sum(z < 0))

    if media >= UMBRAL_Z_ESTILO and positivas >= 4:
        return "dominante"

    if media <= -UMBRAL_Z_ESTILO and negativas >= 4:
        return "complicada"

    # Todas las variables entre −0,5 y 0,5: decide la media
    if float(np.max(np.abs(z))) < UMBRAL_Z_ESTILO:

        if media <= -UMBRAL_Z_NIVEL:
            return "por_debajo"

        if media >= UMBRAL_Z_NIVEL:
            return "por_encima"

        return "equilibrada"

    return "variables"


def _orden_variables(z, tipo):
    """
    Índices de variables de la más alejada a la menos alejada.
    En dominantes/complicadas se priorizan las del mismo signo.
    Empates: orden fijo de VARIABLES_KMEANS (determinista).
    """

    indices = sorted(
        range(len(z)),
        key=lambda i: (-abs(float(z[i])), i)
    )

    if tipo in ("dominante", "por_encima"):
        return (
            [i for i in indices if z[i] > 0]
            + [i for i in indices if z[i] <= 0]
        )

    if tipo in ("complicada", "por_debajo"):
        return (
            [i for i in indices if z[i] < 0]
            + [i for i in indices if z[i] >= 0]
        )

    return indices


def _candidatos_nombre(z):
    """
    Lista de nombres posibles del grupo, de más simple a más
    detallado. Se usa el siguiente si el nombre se repite.
    """

    tipo = _tipo_estilo(z)

    orden = _orden_variables(z, tipo)

    frases = [
        _frase_variable(i, z[i])
        for i in orden
    ]

    sustantivos = [
        frase[1]
        for frase in frases
    ]

    if tipo == "dominante":
        return [
            "Partidas dominantes",
            f"Partidas dominantes en {sustantivos[0]}",
            (
                f"Partidas dominantes en {sustantivos[0]} "
                f"y {sustantivos[1]}"
            ),
        ]

    if tipo == "complicada":
        return [
            "Partidas complicadas",
            f"Partidas complicadas en {sustantivos[0]}",
            (
                f"Partidas complicadas en {sustantivos[0]} "
                f"y {sustantivos[1]}"
            ),
        ]

    if tipo in ("por_encima", "por_debajo"):

        base = (
            "Partidas por encima de tu nivel"
            if tipo == "por_encima"
            else "Partidas por debajo de tu nivel"
        )

        return [
            base,
            f"{base} en {sustantivos[0]}",
            f"{base} en {sustantivos[0]} y {sustantivos[1]}",
        ]

    if tipo == "equilibrada":
        return [
            "Partidas equilibradas",
            (
                "Partidas equilibradas con "
                f"{_unir_frases(frases[:1])}"
            ),
            (
                "Partidas equilibradas con "
                f"{_unir_frases(frases[:2])}"
            ),
        ]

    return [
        f"Partidas con {_unir_frases(frases[:2])}",
        f"Partidas con {_unir_frases(frases[:3])}",
    ]


def _asignar_nombres(centros_z, ids_cluster):
    """
    Asigna nombres sin repetir. Si dos o más grupos coinciden,
    todos ellos pasan a su siguiente candidato (más detallado).
    Último recurso: se añade "(grupo N)".
    """

    candidatos = {
        cluster_id: _candidatos_nombre(z)
        for cluster_id, z in zip(ids_cluster, centros_z)
    }

    nivel = {
        cluster_id: 0
        for cluster_id in ids_cluster
    }

    def nombre_actual(cluster_id):

        lista = candidatos[cluster_id]

        if nivel[cluster_id] < len(lista):
            return lista[nivel[cluster_id]]

        return f"{lista[0]} (grupo {cluster_id + 1})"

    while True:

        nombres = {
            cluster_id: nombre_actual(cluster_id)
            for cluster_id in ids_cluster
        }

        repetidos = Counter(nombres.values())

        en_conflicto = [
            cluster_id
            for cluster_id in ids_cluster
            if repetidos[nombres[cluster_id]] > 1
            and nivel[cluster_id] <= len(candidatos[cluster_id])
        ]

        if not en_conflicto:
            return nombres

        for cluster_id in en_conflicto:
            nivel[cluster_id] += 1


def _formatear_diferencia(porcentaje):

    if porcentaje is None:
        return ""

    signo = "+" if porcentaje >= 0 else "−"

    return f" ({signo}{abs(porcentaje):.0f} %)"


def _adverbio_diferencia(porcentaje):
    """
    Adverbio según el % de diferencia frente al promedio:
    hasta 15 % "algo", de 15 a 30 % ninguno, más de 30 % "mucho".
    """

    if porcentaje is None:
        return ""

    magnitud = abs(porcentaje)

    if magnitud <= 15:
        return "algo"

    if magnitud <= 30:
        return ""

    return "mucho"


def _detalle_con_adverbio(orden, z, diferencias):
    """
    Detalle de las 2 variables con adverbio según el %:
        "algo menos de daño (−12 %) y de oro (−9 %)"
        "un KDA mucho peor (−34 %) y algo menos de oro (−10 %)"
        "mucho más oro (+35 %) y daño (+55 %)"
    """

    partes = []

    for i in orden:

        cuantificador, sustantivo = _frase_variable(i, z[i])

        partes.append({
            "adverbio": _adverbio_diferencia(diferencias[i]),
            "cuantificador": cuantificador,
            "sustantivo": sustantivo,
            "diferencia": _formatear_diferencia(diferencias[i]),
        })

    def texto_sustantivo(parte):
        # Con "algo" se dice "algo menos de daño"
        preposicion = "de " if parte["adverbio"] == "algo" else ""
        return (
            f"{preposicion}{parte['sustantivo']}"
            f"{parte['diferencia']}"
        )

    def texto_completo(parte):

        adverbio = (
            f"{parte['adverbio']} "
            if parte["adverbio"]
            else ""
        )

        # Concordancia con sustantivo femenino: "mucha más visión"
        if (
            parte["adverbio"] == "mucho"
            and parte["sustantivo"] == "visión"
        ):
            adverbio = "mucha "

        if parte["sustantivo"] == "KDA":
            return (
                f"un KDA {adverbio}{parte['cuantificador']}"
                f"{parte['diferencia']}"
            )

        return (
            f"{adverbio}{parte['cuantificador']} "
            f"{texto_sustantivo(parte)}"
        )

    p0, p1 = partes

    # Mismo adverbio y cuantificador: se dice una sola vez
    if (
        p0["sustantivo"] != "KDA"
        and p1["sustantivo"] != "KDA"
        and p0["adverbio"] == p1["adverbio"]
        and p0["cuantificador"] == p1["cuantificador"]
    ):
        return (
            f"{texto_completo(p0)} y {texto_sustantivo(p1)}"
        )

    return f"{texto_completo(p0)} y {texto_completo(p1)}"


def _describir_grupo(z, diferencias):
    """
    Una frase que explica el grupo frente al promedio del
    propio jugador (diferencias en % de unidades originales).
    """

    tipo = _tipo_estilo(z)

    orden = _orden_variables(z, tipo)[:2]

    if tipo == "equilibrada":
        return (
            "Tu rendimiento en estas partidas está cerca de "
            "tu promedio en las 5 métricas."
        )

    if tipo in ("por_encima", "por_debajo"):
        return (
            "Frente a tu promedio, en estas partidas tienes "
            f"{_detalle_con_adverbio(orden, z, diferencias)}."
        )

    if tipo in ("dominante", "complicada"):

        detalle = " y ".join(
            f"{PALABRAS_VARIABLES[i][2]}"
            f"{_formatear_diferencia(diferencias[i])}"
            for i in orden
        )

        direccion = (
            "por encima"
            if tipo == "dominante"
            else "por debajo"
        )

        return (
            f"Rindes {direccion} de tu promedio en casi todo, "
            f"sobre todo en {detalle}."
        )

    return (
        "Frente a tu promedio, en estas partidas tienes "
        f"{_detalle_con_adverbio(orden, z, diferencias)}."
    )


def _campeones_top(partidas_grupo, limite=3):
    """
    Campeones más usados en el grupo.
    Empates: orden alfabético.
    """

    contador = Counter(
        (partida.get("campeon", {}) or {}).get("nombre")
        or "Desconocido"
        for partida in partidas_grupo
    )

    ordenados = sorted(
        contador.items(),
        key=lambda item: (-item[1], item[0])
    )

    return [
        {
            "nombre": nombre,
            "cantidad": cantidad
        }
        for nombre, cantidad in ordenados[:limite]
    ]


def _es_victoria(partida):

    return bool(
        (partida.get("resultado", {}) or {}).get(
            "victoria",
            False
        )
    )


def _elegir_estilos(clusters):
    """
    Mejor estilo: mayor win rate; estilo a evitar: menor.
    Empate: el grupo con más partidas (y luego el id menor).
    Si todos tienen el mismo win rate no se marca ninguno.
    """

    win_rates = {
        cluster["win_rate"]
        for cluster in clusters
    }

    if len(win_rates) < 2:
        return None, None

    mejor = min(
        clusters,
        key=lambda c: (
            -c["win_rate"],
            -c["cantidad_partidas"],
            c["cluster"]
        )
    )

    peor = min(
        clusters,
        key=lambda c: (
            c["win_rate"],
            -c["cantidad_partidas"],
            c["cluster"]
        )
    )

    return mejor, peor


def _redactar_conclusion(mejor, peor):

    """
    Conclusión descriptiva (sin consejos causales).
    """

    if mejor is None or peor is None:
        return (
            "Ganaste el mismo porcentaje de partidas en "
            "todos tus estilos."
        )

    def plural(cantidad):
        return (
            "1 partida"
            if cantidad == 1
            else f"{cantidad} partidas"
        )

    return (
        f"Ganaste el {mejor['win_rate']:.0f} % de tus partidas "
        f"del estilo «{mejor['nombre']}» "
        f"({plural(mejor['cantidad_partidas'])}) y el "
        f"{peor['win_rate']:.0f} % de las del estilo "
        f"«{peor['nombre']}» "
        f"({plural(peor['cantidad_partidas'])})."
    )


def _respuesta_no_disponible(
    motivo,
    mensaje,
    cantidad,
    evaluacion
):
    """
    Respuesta cuando no se puede aplicar el análisis.
    Conserva los campos de siempre y agrega los nuevos vacíos.
    """

    return {
        "disponible": False,
        "motivo": motivo,
        "mensaje": mensaje,
        "algoritmo": "K-Means",
        "partidas_utilizadas": cantidad,
        "variables": VARIABLES_KMEANS,
        "numero_clusters": 0,
        "evaluacion_clusters": evaluacion,
        "clusters": [],
        "mejor_estilo": None,
        "estilo_a_evitar": None,
        "conclusion": None,
        "pca": {
            "varianza_explicada": [],
            "puntos": []
        }
    }


def analizar_patrones_kmeans(
    partidas,
    max_clusters=6
):
    """
    Aplica K-Means sobre las partidas del rol principal.

    Flujo:
        1. Extrae métricas.
        2. Normaliza mediante StandardScaler.
        3. Evalúa K entre 2 y max_clusters.
        4. Selecciona K mediante Silhouette Score.
        5. Ejecuta K-Means.
        6. Calcula centroides interpretables.
        7. Retorna los patrones encontrados.
    """

    datos, indices_validos = (
        preparar_datos_kmeans(
            partidas
        )
    )

    cantidad = len(
        datos
    )

    if cantidad < MINIMO_PARTIDAS_KMEANS:

        return _respuesta_no_disponible(
            motivo=(
                f"Se necesitan al menos {MINIMO_PARTIDAS_KMEANS} "
                "partidas válidas del rol principal para "
                "aplicar K-Means."
            ),
            mensaje=(
                "Necesitamos al menos "
                f"{MINIMO_PARTIDAS_KMEANS} partidas en tu rol "
                "principal para detectar tus estilos de juego. "
                f"Por ahora tienes {cantidad}: juega algunas más "
                "y vuelve a intentarlo."
            ),
            cantidad=cantidad,
            evaluacion=[]
        )

    # ========================================================
    # NORMALIZACIÓN
    # ========================================================

    scaler = StandardScaler()

    datos_normalizados = (
        scaler.fit_transform(
            datos
        )
    )

    # ========================================================
    # SELECCIÓN DE K
    # ========================================================

    mejor_k, evaluacion = (
        evaluar_numero_clusters(
            datos_normalizados,
            max_clusters=max_clusters
        )
    )

    if mejor_k is None:

        return _respuesta_no_disponible(
            motivo=(
                "No fue posible determinar "
                "un número válido de clusters."
            ),
            mensaje=(
                "Tus partidas son demasiado parecidas entre sí "
                "para separarlas en estilos de juego distintos."
            ),
            cantidad=cantidad,
            evaluacion=evaluacion
        )

    # ========================================================
    # MODELO FINAL
    # ========================================================

    modelo = KMeans(
        n_clusters=mejor_k,
        random_state=42,
        n_init=10
    )

    etiquetas = modelo.fit_predict(
        datos_normalizados
    )

    # ========================================================
    # CLUSTERS
    # ========================================================

    clusters = []

    contador = Counter(
        etiquetas.tolist()
    )

    for cluster_id in sorted(
        contador.keys()
    ):

        indices_cluster = np.where(
            etiquetas == cluster_id
        )[0]

        cantidad_cluster = len(
            indices_cluster
        )

        porcentaje = (
            cantidad_cluster
            / cantidad
        ) * 100

        promedios = (
            _calcular_promedio_cluster(
                datos,
                indices_cluster
            )
        )

        clusters.append({

            "cluster":
                int(cluster_id),

            "cantidad_partidas":
                cantidad_cluster,

            "porcentaje":
                round(
                    porcentaje,
                    2
                ),

            "metricas_promedio":
                promedios
        })

    # ========================================================
    # INTERPRETACIÓN DE LOS GRUPOS
    # ========================================================
    #
    # Todo lo siguiente se calcula DESPUÉS del agrupamiento:
    # la victoria no interviene en K-Means.
    # ========================================================

    partidas_utilizadas = [
        partidas[indice]
        for indice in indices_validos
    ]

    media_jugador = np.mean(
        datos,
        axis=0
    )

    ids_cluster = [
        cluster["cluster"]
        for cluster in clusters
    ]

    # z-score medio de cada grupo (los datos ya están
    # estandarizados respecto al promedio del jugador)
    centros_z = [
        np.mean(
            datos_normalizados[etiquetas == cluster_id],
            axis=0
        )
        for cluster_id in ids_cluster
    ]

    nombres = _asignar_nombres(
        centros_z,
        ids_cluster
    )

    for cluster, z in zip(clusters, centros_z):

        cluster_id = cluster["cluster"]

        indices_cluster = np.where(
            etiquetas == cluster_id
        )[0]

        partidas_grupo = [
            partidas_utilizadas[i]
            for i in indices_cluster
        ]

        victorias = sum(
            _es_victoria(partida)
            for partida in partidas_grupo
        )

        centro_original = np.mean(
            datos[indices_cluster],
            axis=0
        )

        # Diferencia en % frente al promedio del jugador
        diferencias = [
            (
                round(
                    float(
                        (centro_original[i] - media_jugador[i])
                        / abs(media_jugador[i])
                        * 100
                    ),
                    2
                )
                if media_jugador[i] != 0
                else None
            )
            for i in range(len(VARIABLES_KMEANS))
        ]

        cluster["nombre"] = nombres[cluster_id]

        cluster["descripcion"] = _describir_grupo(
            z,
            diferencias
        )

        cluster["win_rate"] = round(
            victorias
            / len(partidas_grupo)
            * 100,
            2
        )

        cluster["campeones_top"] = _campeones_top(
            partidas_grupo
        )

        cluster["es_mejor_estilo"] = False
        cluster["es_estilo_a_evitar"] = False

    mejor_grupo, peor_grupo = _elegir_estilos(
        clusters
    )

    if mejor_grupo is not None:
        mejor_grupo["es_mejor_estilo"] = True

    if peor_grupo is not None:
        peor_grupo["es_estilo_a_evitar"] = True

    conclusion = _redactar_conclusion(
        mejor_grupo,
        peor_grupo
    )

    # ========================================================
    # PCA (SOLO PARA DIBUJAR)
    # ========================================================
    #
    # Proyecta los mismos datos estandarizados a 2 ejes para
    # el gráfico de puntos. No interviene en el agrupamiento.
    # ========================================================

    pca = PCA(
        n_components=2
    )

    coordenadas = pca.fit_transform(
        datos_normalizados
    )

    puntos_pca = []

    for posicion, partida in enumerate(
        partidas_utilizadas
    ):

        puntos_pca.append({

            "x":
                round(
                    float(coordenadas[posicion][0]),
                    4
                ),

            "y":
                round(
                    float(coordenadas[posicion][1]),
                    4
                ),

            "cluster":
                int(etiquetas[posicion]),

            "victoria":
                _es_victoria(partida),

            "campeon":
                (partida.get("campeon", {}) or {}).get(
                    "nombre"
                ),

            "match_id":
                (partida.get("partida", {}) or {}).get(
                    "match_id"
                )
        })

    # ========================================================
    # ASIGNACIÓN PARTIDA -> CLUSTER
    # ========================================================

    asignaciones = []

    for posicion, etiqueta in enumerate(
        etiquetas
    ):

        indice_original = (
            indices_validos[
                posicion
            ]
        )

        partida = partidas[
            indice_original
        ]

        datos_partida = partida.get(
            "partida",
            {}
        )

        campeon = partida.get(
            "campeon",
            {}
        )

        asignaciones.append({

            "indice_partida":
                indice_original,

            "match_id":
                datos_partida.get(
                    "match_id"
                ),

            "campeon":
                campeon.get(
                    "nombre"
                ),

            "cluster":
                int(etiqueta)
        })

    # ========================================================
    # RESULTADO
    # ========================================================

    mejor_silhouette = None

    for resultado in evaluacion:

        if resultado["k"] == mejor_k:

            mejor_silhouette = (
                resultado[
                    "silhouette_score"
                ]
            )

            break

    return {

        "disponible":
            True,

        "algoritmo":
            "K-Means",

        "normalizacion":
            "StandardScaler",

        "criterio_seleccion_k":
            "Silhouette Score",

        "partidas_utilizadas":
            cantidad,

        "variables":
            VARIABLES_KMEANS,

        "numero_clusters":
            mejor_k,

        "silhouette_score":
            mejor_silhouette,

        "evaluacion_clusters":
            evaluacion,

        "clusters":
            clusters,

        "asignaciones":
            asignaciones,

        "mejor_estilo":
            (
                mejor_grupo["cluster"]
                if mejor_grupo is not None
                else None
            ),

        "estilo_a_evitar":
            (
                peor_grupo["cluster"]
                if peor_grupo is not None
                else None
            ),

        "conclusion":
            conclusion,

        "pca": {

            "varianza_explicada": [
                round(float(valor), 4)
                for valor in pca.explained_variance_ratio_
            ],

            "puntos":
                puntos_pca
        }
    }