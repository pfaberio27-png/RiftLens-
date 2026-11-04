import {
  useId,
  useState,
} from "react";

import type {
  EstadoMetrica,
} from "../types/analisis";

import {
  formatearPorcentajeConSigno,
  formatearValorMetrica,
  obtenerClaseEstado,
} from "../utils/formatters";

import {
  DESCRIPCIONES_METRICAS,
  MINIMO_PARTIDAS_CONFIABLE,
} from "../utils/metricas";



// ============================================================
// AYUDA (tooltip con hover, foco o toque)
// ============================================================

interface AyudaMetricaProps {
  clave: string;
  nombre: string;
}


export function AyudaMetrica({
  clave,
  nombre,
}: AyudaMetricaProps) {

  const id = useId();

  // En celular el tooltip se abre y cierra al tocar.
  const [
    abierta,
    setAbierta,
  ] = useState(false);

  const descripcion =
    DESCRIPCIONES_METRICAS[clave];

  if (!descripcion) {
    return null;
  }

  return (

    <button
      type="button"
      className={
        "metrica-ayuda"
        + (abierta ? " activa" : "")
      }
      aria-label={`Qué es ${nombre}`}
      aria-describedby={id}
      onClick={() =>
        setAbierta(!abierta)
      }
      onBlur={() =>
        setAbierta(false)
      }
    >

      ?

      <span
        id={id}
        role="tooltip"
        className="metrica-ayuda-tooltip"
      >
        {descripcion}
      </span>

    </button>

  );
}


// ============================================================
// GEOMETRÍA DE LA BARRA
// ============================================================

interface GeometriaBarra {
  inicio: number;
  ancho: number;
  marcador: number | null;
  divergente: boolean;
}


// Escala común para tu valor y la referencia. Si alguno es
// negativo (diferencia de oro), la barra parte del centro.
function calcularGeometria(
  jugador: number | null,
  referencia: number | null
): GeometriaBarra | null {

  if (jugador === null) {
    return null;
  }

  const valores = [
    jugador,
    referencia ?? jugador,
  ];

  const maximo = Math.max(
    ...valores.map(Math.abs)
  );

  const divergente =
    Math.min(...valores) < 0;

  if (maximo === 0) {

    return {
      inicio: divergente ? 50 : 0,
      ancho: 0,
      marcador:
        referencia === null
          ? null
          : divergente ? 50 : 0,
      divergente,
    };
  }

  // Margen para que el valor mayor no toque el borde.
  const escala = maximo * 1.15;

  if (divergente) {

    const posicion = (valor: number) =>
      50 + (valor / escala) * 50;

    const posicionJugador =
      posicion(jugador);

    return {
      inicio: Math.min(50, posicionJugador),
      ancho: Math.abs(posicionJugador - 50),
      marcador:
        referencia === null
          ? null
          : posicion(referencia),
      divergente,
    };
  }

  return {
    inicio: 0,
    ancho: (jugador / escala) * 100,
    marcador:
      referencia === null
        ? null
        : (referencia / escala) * 100,
    divergente,
  };
}


// ============================================================
// BARRA DE COMPARACIÓN
// ============================================================

interface ComparisonBarProps {
  clave: string;
  nombre: string;
  jugador: number | null;
  referencia: number | null;
  diferenciaPorcentual: number | null;
  // Ya considera menor_es_mejor: "superior" = mejor.
  estado: EstadoMetrica | null;
  // "Nivel pro" o "Tu promedio".
  etiquetaReferencia: string;
  unidad?: string;
  menorEsMejor?: boolean;
  partidasConDato?: number | null;
}


function ComparisonBar({
  clave,
  nombre,
  jugador,
  referencia,
  diferenciaPorcentual,
  estado,
  etiquetaReferencia,
  unidad = "",
  menorEsMejor = false,
  partidasConDato,
}: ComparisonBarProps) {

  const sinDato =
    jugador === null
    || diferenciaPorcentual === null
    || estado === null;

  const geometria =
    calcularGeometria(
      jugador,
      referencia
    );

  const pocasPartidas =
    partidasConDato !== undefined
    && partidasConDato !== null
    && partidasConDato > 0
    && partidasConDato < MINIMO_PARTIDAS_CONFIABLE;

  const valorJugador =
    formatearValorMetrica(
      clave,
      jugador,
      unidad
    );

  const valorReferencia =
    formatearValorMetrica(
      clave,
      referencia,
      unidad
    );


  return (

    <article className="comparacion-barra">

      <div className="comparacion-barra-head">

        <span className="comparacion-barra-nombre">
          {nombre}
        </span>

        <AyudaMetrica
          clave={clave}
          nombre={nombre}
        />

        {
          pocasPartidas && (
            <span className="comparacion-pocas">
              (pocas partidas)
            </span>
          )
        }

      </div>


      <div className="comparacion-barra-valores">

        <div>
          <span className="comparacion-barra-etiqueta">
            Tú
          </span>
          <strong
            className={
              jugador === null
                ? "comparacion-valor sin-dato"
                : "comparacion-valor"
            }
          >
            {valorJugador}
          </strong>
        </div>

        <div>
          <span className="comparacion-barra-etiqueta">
            {etiquetaReferencia}
          </span>
          <strong
            className={
              referencia === null
                ? "comparacion-referencia sin-dato"
                : "comparacion-referencia"
            }
          >
            {valorReferencia}
          </strong>
        </div>

        <div className="comparacion-barra-diferencia">
          <span className="comparacion-barra-etiqueta">
            Diferencia
          </span>
          <strong
            className={
              sinDato
                ? "sin-dato"
                : obtenerClaseEstado(estado)
            }
          >
            {
              sinDato
                ? "—"
                : formatearPorcentajeConSigno(
                  diferenciaPorcentual
                )
            }
          </strong>
        </div>

      </div>


      <div
        className={
          "comparacion-pista"
          + (
            geometria?.divergente
              ? " divergente"
              : ""
          )
        }
        role="img"
        aria-label={
          `${nombre}: tú ${valorJugador}, `
          + `${etiquetaReferencia.toLowerCase()} ${valorReferencia}`
          + (
            menorEsMejor
              ? ". Menos es mejor"
              : ""
          )
        }
      >

        {
          geometria && (
            <div
              className={
                "comparacion-relleno "
                + (estado ?? "sin-estado")
              }
              style={{
                left: `${geometria.inicio}%`,
                width: `${geometria.ancho}%`,
              }}
            />
          )
        }

        {
          geometria
          && geometria.marcador !== null && (
            <div
              className="comparacion-marcador"
              style={{
                left: `${geometria.marcador}%`,
              }}
            />
          )
        }

      </div>

    </article>

  );
}


export default ComparisonBar;
