"""
Pruebas de la selección de recomendaciones desde el catálogo.

Ejecutar desde la raíz del proyecto:
    uv run python -m pytest backend/tests
"""

from collections import Counter

import pytest

from backend.app.services.analisis_service import (
    calcular_datos_condicion,
    cargar_catalogo_recomendaciones,
    seleccionar_recomendaciones,
)

ROLES = ["TOP", "JUNGLE", "MID", "ADC", "SUPPORT"]

METRICAS = [
    "win_rate",
    "kda",
    "cs_por_minuto",
    "oro_por_minuto",
    "daño_por_minuto",
    "vision_score",
]


def crear_analisis(rol, diferencias, partidas=None):
    """
    Construye un análisis mínimo: solo se usa la
    diferencia porcentual de cada métrica.
    """

    return {
        "rol_principal": rol,
        "comparacion": {
            metrica: {"diferencia_porcentual": diferencias.get(metrica, 0.0)}
            for metrica in METRICAS
        },
        "partidas_rol": partidas or [],
    }


def partidas_de_prueba(muertes, control_wards, campeones):
    return [
        {
            "combate": {"muertes": muertes},
            "vision": {"control_wards": control_wards},
            "campeon": {"nombre": campeon},
        }
        for campeon in campeones
    ]


# Todas las métricas muy por debajo y todas las condiciones cumplidas:
# el caso con más candidatas posible.
TODAS_DEBILES = {metrica: -40.0 for metrica in METRICAS}
PARTIDAS_CONDICIONES = partidas_de_prueba(
    muertes=8,
    control_wards=0,
    campeones=[f"Campeon{i}" for i in range(7)],
)


def test_catalogo_cargado():
    catalogo = cargar_catalogo_recomendaciones()
    assert len(catalogo) == 40


def test_sin_debilidades_devuelve_las_tres_generales():
    analisis = crear_analisis("MID", {"kda": 10.0, "vision_score": -4.9})

    resultado = seleccionar_recomendaciones(analisis)

    catalogo = cargar_catalogo_recomendaciones()
    generales = sorted(
        item["id"] for item in catalogo
        if item["nivel"] == "sin_debilidades"
    )

    assert [rec["id"] for rec in resultado] == generales
    assert len(resultado) == 3


@pytest.mark.parametrize("diferencia", [-6.0, -20.0, -40.0])
def test_soporte_no_recibe_recomendaciones_de_otros_roles(diferencia):
    catalogo = {
        item["id"]: item for item in cargar_catalogo_recomendaciones()
    }
    analisis = crear_analisis(
        "SUPPORT",
        {metrica: diferencia for metrica in METRICAS},
        PARTIDAS_CONDICIONES,
    )

    resultado = seleccionar_recomendaciones(analisis)

    assert resultado
    for rec in resultado:
        roles = catalogo[rec["id"]]["roles"]
        assert "TODOS" in roles or "SUPPORT" in roles


@pytest.mark.parametrize("rol", ROLES)
def test_limites_por_metrica_y_total(rol):
    analisis = crear_analisis(rol, TODAS_DEBILES, PARTIDAS_CONDICIONES)

    resultado = seleccionar_recomendaciones(analisis)

    assert len(resultado) <= 6
    assert max(Counter(rec["metrica"] for rec in resultado).values()) <= 2


@pytest.mark.parametrize("rol", ROLES)
def test_resultado_determinista(rol):
    diferencias = {
        "kda": -12.0,
        "cs_por_minuto": -22.0,
        "vision_score": -35.0,
        "win_rate": -8.0,
    }

    resultados = [
        seleccionar_recomendaciones(
            crear_analisis(rol, diferencias, PARTIDAS_CONDICIONES)
        )
        for _ in range(5)
    ]

    assert all(resultado == resultados[0] for resultado in resultados)


def test_formato_y_prioridades():
    analisis = crear_analisis("ADC", TODAS_DEBILES, PARTIDAS_CONDICIONES)

    resultado = seleccionar_recomendaciones(analisis)

    campos = {
        "id", "metrica", "nombre", "diferencia_porcentual",
        "recomendacion", "titulo", "prioridad",
    }
    for rec in resultado:
        assert campos <= rec.keys()

    assert [rec["prioridad"] for rec in resultado] == (
        ["alta", "alta", "media", "media", "baja", "baja"][:len(resultado)]
    )


def test_control_wards_sin_dato_no_cumple_condicion():
    partidas = [{"vision": {"control_wards": None}}] * 3

    datos = calcular_datos_condicion(partidas)
    assert datos["control_wards_promedio"] is None

    # VIS-04 exige control_wards_promedio < 1: sin dato no se elige.
    analisis = crear_analisis("ADC", {"vision_score": -40.0}, partidas)
    ids = [rec["id"] for rec in seleccionar_recomendaciones(analisis)]
    assert "VIS-04" not in ids

    # Solo promedia las partidas que tienen el dato.
    partidas_mixtas = partidas + [{"vision": {"control_wards": 2}}]
    assert calcular_datos_condicion(partidas_mixtas)[
        "control_wards_promedio"
    ] == 2


def test_catalogo_ausente_no_rompe():
    analisis = crear_analisis("ADC", TODAS_DEBILES)

    assert seleccionar_recomendaciones(analisis, catalogo=[]) == []
