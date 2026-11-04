import os
import threading
import time
from collections import deque

import requests
from dotenv import load_dotenv


load_dotenv("backend/.env")


# ============================================================
# CONFIGURACIÓN
# ============================================================

LIMITES_POR_DEFECTO = "20:1,100:120"

MAX_REINTENTOS_429 = 3

ESPERA_MAXIMA_RETRY_AFTER = 15

ESPERA_RETRY_AFTER_POR_DEFECTO = 1


# ============================================================
# EXCEPCIÓN PARA LÍMITE DE RIOT API
# ============================================================

class RiotRateLimitException(Exception):

    def __init__(
        self,
        mensaje,
        retry_after=None
    ):
        self.mensaje = mensaje
        self.retry_after = retry_after

        super().__init__(
            mensaje
        )


# ============================================================
# LIMITADOR DE VENTANA DESLIZANTE
# ============================================================

def parsear_limites(
    texto: str
):
    """
    Convierte "20:1,100:120" en [(20, 1.0), (100, 120.0)]:
    cantidad máxima de solicitudes por ventana de segundos.
    """

    limites = []

    for parte in texto.split(","):

        parte = parte.strip()

        if not parte:
            continue

        try:

            cantidad, segundos = parte.split(":")

            cantidad = int(cantidad)
            segundos = float(segundos)

        except ValueError:

            print(
                "RIOT_LIMITES inválido, se ignora:",
                parte
            )

            continue

        if cantidad > 0 and segundos > 0:

            limites.append(
                (cantidad, segundos)
            )

    if not limites and texto != LIMITES_POR_DEFECTO:

        return parsear_limites(
            LIMITES_POR_DEFECTO
        )

    return limites


class LimitadorVentanaDeslizante:
    """
    Garantiza que en cualquier ventana de N segundos
    no se superen las solicitudes permitidas.
    Es seguro entre hilos.
    """

    def __init__(
        self,
        limites
    ):
        self.limites = limites

        self._historial = [
            deque()
            for _ in limites
        ]

        self._lock = threading.Lock()


    def esperar_turno(self):

        while True:

            with self._lock:

                ahora = time.monotonic()

                espera = 0.0

                for (cantidad, segundos), historial in zip(
                    self.limites,
                    self._historial
                ):

                    while (
                        historial
                        and
                        ahora - historial[0] >= segundos
                    ):
                        historial.popleft()

                    if len(historial) >= cantidad:

                        espera = max(
                            espera,
                            segundos - (ahora - historial[0])
                        )

                if espera <= 0:

                    for historial in self._historial:
                        historial.append(ahora)

                    return

            time.sleep(
                espera
            )


limitador = LimitadorVentanaDeslizante(
    parsear_limites(
        os.getenv(
            "RIOT_LIMITES",
            LIMITES_POR_DEFECTO
        )
    )
)


# ============================================================
# SESIÓN HTTP (UNA POR HILO, REUTILIZA CONEXIONES)
# ============================================================

_datos_hilo = threading.local()


def obtener_sesion():

    sesion = getattr(
        _datos_hilo,
        "sesion",
        None
    )

    if sesion is None:

        sesion = requests.Session()

        _datos_hilo.sesion = sesion

    return sesion


# ============================================================
# GET A RIOT API CON LIMITADOR Y REINTENTOS ANTE 429
# ============================================================

def segundos_retry_after(
    retry_after
):

    if retry_after is None:
        return ESPERA_RETRY_AFTER_POR_DEFECTO

    try:
        return max(
            float(retry_after),
            0
        )

    except (TypeError, ValueError):
        return ESPERA_RETRY_AFTER_POR_DEFECTO


def riot_get(
    url: str,
    api_key: str,
    params=None,
    timeout=10
):
    """
    Realiza la solicitud respetando el limitador.

    Ante HTTP 429 espera lo indicado en Retry-After
    (máximo 15 s) y reintenta hasta 3 veces. Si Riot pide
    esperar más o se agotan los reintentos, lanza
    RiotRateLimitException.

    El resto de códigos HTTP se devuelven al llamador.
    """

    for intento in range(
        MAX_REINTENTOS_429 + 1
    ):

        limitador.esperar_turno()

        response = obtener_sesion().get(
            url,
            headers={
                "X-Riot-Token":
                    api_key
            },
            params=params,
            timeout=timeout
        )

        if response.status_code != 429:
            return response

        retry_after = (
            response.headers.get(
                "Retry-After"
            )
        )

        espera = segundos_retry_after(
            retry_after
        )

        if (
            intento >= MAX_REINTENTOS_429
            or
            espera > ESPERA_MAXIMA_RETRY_AFTER
        ):

            raise RiotRateLimitException(
                "Se alcanzó el límite de solicitudes de Riot API.",
                retry_after
            )

        time.sleep(
            espera
        )
