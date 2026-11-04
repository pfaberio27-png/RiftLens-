import json
import os
import re
import threading
import time

import requests


# ============================================================
# DATA DRAGON (íconos de campeones)
# ============================================================
#
# La versión actual se consulta una sola vez en versions.json
# y se guarda en memoria. Si la consulta falla se usa la
# versión de la partida (version_parche) o la última conocida,
# guardada en backend/app/data/data_dragon_version.json.

URL_DATA_DRAGON = "https://ddragon.leagueoflegends.com"

URL_VERSIONES = f"{URL_DATA_DRAGON}/api/versions.json"

TIMEOUT_VERSIONES = 3

# Tras un fallo no se vuelve a consultar hasta pasado este tiempo
ESPERA_TRAS_FALLO_SEGUNDOS = 300

RUTA_ULTIMA_VERSION = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "data_dragon_version.json",
)


_version_en_memoria = None

_ultimo_fallo = 0.0

_bloqueo = threading.Lock()


def version_desde_parche(version_parche):
    """
    "16.21.712.4153" (gameVersion de Riot) → "16.21.1"
    (formato de Data Dragon). None si no es válida.
    """

    coincidencia = re.match(
        r"^(\d+)\.(\d+)",
        version_parche or ""
    )

    if not coincidencia:
        return None

    return f"{coincidencia.group(1)}.{coincidencia.group(2)}.1"


def leer_ultima_version_conocida():

    try:

        with open(
            RUTA_ULTIMA_VERSION,
            "r",
            encoding="utf-8"
        ) as archivo:

            return json.load(archivo).get("version")

    except (OSError, ValueError, AttributeError):
        return None


def guardar_ultima_version_conocida(version):

    ruta_temporal = f"{RUTA_ULTIMA_VERSION}.tmp"

    try:

        with open(
            ruta_temporal,
            "w",
            encoding="utf-8"
        ) as archivo:

            json.dump({"version": version}, archivo)

        os.replace(
            ruta_temporal,
            RUTA_ULTIMA_VERSION
        )

    except OSError as error:

        print(
            "No se pudo guardar la versión de Data Dragon:",
            error
        )


def obtener_version_data_dragon(version_parche=None):
    """
    Devuelve la versión de Data Dragon para los íconos:
    1. La versión actual (versions.json), una sola vez.
    2. Si falla: version_parche de la partida.
    3. Si tampoco hay: la última versión conocida.
    Devuelve None si no hay ninguna.
    """

    global _version_en_memoria, _ultimo_fallo

    if _version_en_memoria:
        return _version_en_memoria

    with _bloqueo:

        if _version_en_memoria:
            return _version_en_memoria

        if time.time() - _ultimo_fallo >= ESPERA_TRAS_FALLO_SEGUNDOS:

            try:

                respuesta = requests.get(
                    URL_VERSIONES,
                    timeout=TIMEOUT_VERSIONES
                )

                respuesta.raise_for_status()

                versiones = respuesta.json()

                if (
                    isinstance(versiones, list)
                    and versiones
                    and isinstance(versiones[0], str)
                ):

                    _version_en_memoria = versiones[0]

                    guardar_ultima_version_conocida(
                        _version_en_memoria
                    )

                    return _version_en_memoria

                raise ValueError("versions.json no válido")

            except (requests.RequestException, ValueError) as error:

                _ultimo_fallo = time.time()

                print(
                    "No se pudo consultar la versión de Data Dragon:",
                    error
                )

    return (
        version_desde_parche(version_parche)
        or leer_ultima_version_conocida()
    )


def version_parche_mas_reciente(partidas):
    """
    version_parche de la primera partida que la tenga
    (las partidas llegan de la más reciente a la más antigua).
    """

    for partida in partidas or []:

        version = (
            partida.get("partida")
            or {}
        ).get("version_parche")

        if version:
            return version

    return None


def url_icono_campeon(version, nombre_campeon):
    """
    URL del ícono del campeón, o None si falta la versión
    o el nombre.
    """

    if not version or not nombre_campeon:
        return None

    return (
        f"{URL_DATA_DRAGON}/cdn/{version}"
        f"/img/champion/{nombre_campeon}.png"
    )
