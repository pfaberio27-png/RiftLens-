import {
  useEffect,
  useRef,
  useState,
} from "react";

import type {
  SyntheticEvent,
} from "react";

import {
  createPortal,
} from "react-dom";

import {
  useCierreAnimado,
} from "../hooks/useCierreAnimado";

import {
  useVersionDataDragon,
} from "../hooks/useVersionDataDragon";

import {
  obtenerDetallePartida,
} from "../services/analisisService";

import {
  urlIconoCampeon,
  urlIconoObjeto,
} from "../services/dataDragon";

import type {
  DetallePartida,
  ObjetivosEquipo,
  PartidaReciente,
  ParticipantePartida,
} from "../types/analisis";

import {
  formatearRol,
} from "../utils/formatters";


interface MatchDetailModalProps {
  partida: PartidaReciente;
  puuid: string;
  region: string;
  onCerrar: () => void;
}


// ============================================================
// FORMATOS
// ============================================================

// 1869 s → "31:09"
const formatearDuracion = (
  segundos: number
) => {

  const total =
    Math.max(0, Math.round(segundos));

  const minutos =
    Math.floor(total / 60);

  const resto =
    total % 60;

  return `${minutos}:${String(resto).padStart(2, "0")}`;

};


const formatearFecha = (
  timestamp: number | null
) => {

  if (!timestamp) {
    return null;
  }

  return new Date(timestamp).toLocaleString(
    "es-PE",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }
  );

};


// 12345 → "12.3k"
const formatearMiles = (
  valor: number
) => `${(valor / 1000).toFixed(1)}k`;


const nombreCompleto = (
  jugador: ParticipantePartida
) =>
  `${jugador.nombre ?? "Jugador"}` +
  (jugador.tag ? `#${jugador.tag}` : "");


const sumar = (
  jugadores: ParticipantePartida[],
  valor: (jugador: ParticipantePartida) => number
) =>
  jugadores.reduce(
    (total, jugador) => total + valor(jugador),
    0
  );


// Ícono que se oculta si Data Dragon no lo tiene
const ocultarSiFalla = (
  event: SyntheticEvent<HTMLImageElement>
) => {

  event.currentTarget.style.visibility =
    "hidden";

};


// ============================================================
// DUELO DE LÍNEA
// ============================================================

interface FilaDuelo {
  etiqueta: string;
  propio: string;
  rival: string;
  diferencia: number;
  textoDiferencia: string;
}


const crearFilasDuelo = (
  jugador: ParticipantePartida,
  rival: ParticipantePartida
): FilaDuelo[] => {

  const conSigno = (
    valor: number,
    texto: string
  ) =>
    valor > 0
      ? `+${texto}`
      : valor < 0
        ? `-${texto}`
        : "0";

  const diferenciaKda =
    jugador.combate.kda - rival.combate.kda;

  const diferenciaCs =
    jugador.recursos.cs - rival.recursos.cs;

  const diferenciaOro =
    jugador.recursos.oro - rival.recursos.oro;

  const diferenciaDano =
    jugador.daño.campeones - rival.daño.campeones;

  const diferenciaVision =
    jugador.vision.score - rival.vision.score;

  return [
    {
      etiqueta: "KDA",
      propio:
        `${jugador.combate.kills}/${jugador.combate.muertes}/` +
        `${jugador.combate.asistencias} · ${jugador.combate.kda.toFixed(2)}`,
      rival:
        `${rival.combate.kills}/${rival.combate.muertes}/` +
        `${rival.combate.asistencias} · ${rival.combate.kda.toFixed(2)}`,
      diferencia: diferenciaKda,
      textoDiferencia: conSigno(
        diferenciaKda,
        Math.abs(diferenciaKda).toFixed(2)
      ),
    },
    {
      etiqueta: "CS",
      propio: String(jugador.recursos.cs),
      rival: String(rival.recursos.cs),
      diferencia: diferenciaCs,
      textoDiferencia: conSigno(
        diferenciaCs,
        String(Math.abs(diferenciaCs))
      ),
    },
    {
      etiqueta: "Oro",
      propio: formatearMiles(jugador.recursos.oro),
      rival: formatearMiles(rival.recursos.oro),
      diferencia: diferenciaOro,
      textoDiferencia: conSigno(
        diferenciaOro,
        formatearMiles(Math.abs(diferenciaOro))
      ),
    },
    {
      etiqueta: "Daño",
      propio: formatearMiles(jugador.daño.campeones),
      rival: formatearMiles(rival.daño.campeones),
      diferencia: diferenciaDano,
      textoDiferencia: conSigno(
        diferenciaDano,
        formatearMiles(Math.abs(diferenciaDano))
      ),
    },
    {
      etiqueta: "Visión",
      propio: String(jugador.vision.score),
      rival: String(rival.vision.score),
      diferencia: diferenciaVision,
      textoDiferencia: conSigno(
        diferenciaVision,
        String(Math.abs(diferenciaVision))
      ),
    },
  ];

};


const claseDiferencia = (
  valor: number
) =>
  valor > 0
    ? "positiva"
    : valor < 0
      ? "negativa"
      : "neutra";


// ============================================================
// COMPONENTE
// ============================================================

function MatchDetailModal({
  partida,
  puuid,
  region,
  onCerrar,
}: MatchDetailModalProps) {

  // Cierre con animación de salida
  const [cerrando, cerrar] =
    useCierreAnimado(onCerrar);

  // Referencia estable para el listener de Esc
  const cerrarRef =
    useRef(cerrar);

  const botonCerrarRef =
    useRef<HTMLButtonElement | null>(null);


  // Detalle pedido a GET /api/partida al abrir la ventana
  const [detalle, setDetalle] =
    useState<DetallePartida | null>(null);

  const [errorDetalle, setErrorDetalle] =
    useState<string | null>(null);

  // Cambia al pulsar "Reintentar" para repetir la petición
  const [intento, setIntento] =
    useState(0);

  const cargando =
    Boolean(partida.match_id) &&
    !detalle &&
    !errorDetalle;


  const versionDataDragon =
    useVersionDataDragon(
      detalle?.version_parche
    );


  useEffect(() => {

    cerrarRef.current = cerrar;

  }, [cerrar]);


  // ----------------------------------------------------------
  // Esc, bloqueo del scroll y devolución del foco
  // ----------------------------------------------------------

  useEffect(() => {

    const elementoPrevio =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;

    const overflowPrevio =
      document.body.style.overflow;

    document.body.style.overflow =
      "hidden";

    botonCerrarRef.current?.focus();

    const manejarEscape = (
      event: KeyboardEvent
    ) => {

      if (event.key === "Escape") {
        cerrarRef.current();
      }

    };

    document.addEventListener(
      "keydown",
      manejarEscape
    );

    return () => {

      document.removeEventListener(
        "keydown",
        manejarEscape
      );

      document.body.style.overflow =
        overflowPrevio;

      // Devuelve el foco a la partida que abrió la ventana
      if (elementoPrevio?.isConnected) {
        elementoPrevio.focus({
          preventScroll: true,
        });
      }

    };

  }, []);


  // ----------------------------------------------------------
  // Petición del detalle
  // ----------------------------------------------------------

  useEffect(() => {

    if (!partida.match_id) {
      return;
    }

    let activo = true;

    obtenerDetallePartida(
      partida.match_id,
      puuid,
      region
    )
      .then((respuesta) => {

        if (activo) {
          setDetalle(respuesta);
        }

      })
      .catch((error: unknown) => {

        if (activo) {

          setErrorDetalle(
            error instanceof Error
              ? error.message
              : "No se pudo cargar el detalle de la partida."
          );

        }

      });

    return () => {
      activo = false;
    };

  }, [partida.match_id, puuid, region, intento]);


  const reintentar = () => {

    setErrorDetalle(null);

    setIntento(
      (valor) => valor + 1
    );

  };


  // ----------------------------------------------------------
  // Datos derivados
  // ----------------------------------------------------------

  const aliados =
    detalle?.equipos.aliados ?? [];

  const rivales =
    detalle?.equipos.rivales ?? [];

  const jugador =
    aliados.find(
      (participante) => participante.es_jugador
    ) ?? null;

  const rivalDeLinea =
    jugador?.posicion
      ? rivales.find(
          (participante) =>
            participante.posicion === jugador.posicion
        ) ?? null
      : null;

  const victoria =
    detalle?.resultado.victoria ??
    partida.victoria;

  const duracion =
    detalle?.duracion_segundos ||
    partida.duracion_segundos;

  const fecha =
    formatearFecha(
      detalle?.game_creation ?? null
    );


  // ----------------------------------------------------------
  // Render de piezas
  // ----------------------------------------------------------

  const renderIconoCampeon = (
    nombre: string | null,
    clase: string
  ) => {

    const src =
      urlIconoCampeon(
        versionDataDragon,
        nombre
      );

    return src ? (

      <img
        src={src}
        alt={nombre ?? "Campeón"}
        className={clase}
        loading="lazy"
        onError={ocultarSiFalla}
      />

    ) : (

      <span
        className={`${clase} vacio`}
        aria-hidden="true"
      />

    );

  };


  const renderObjetos = (
    objetos: number[]
  ) => {

    // Siempre 7 casillas (6 ítems + accesorio)
    const casillas =
      Array.from(
        { length: 7 },
        (_, indice) => objetos[indice] ?? 0
      );

    return (

      <div
        className="modal-items"
        aria-label="Ítems"
      >

        {
          casillas.map((itemId, indice) => {

            const src =
              urlIconoObjeto(
                versionDataDragon,
                itemId
              );

            return (

              <div
                key={indice}
                className={
                  indice === 6
                    ? "modal-item-slot accesorio"
                    : "modal-item-slot"
                }
              >

                {
                  src && (

                    <img
                      src={src}
                      alt={`Ítem ${itemId}`}
                      loading="lazy"
                      onError={ocultarSiFalla}
                    />

                  )
                }

              </div>

            );

          })
        }

      </div>

    );

  };


  const renderJugador = (
    participante: ParticipantePartida
  ) => {

    const nombre =
      nombreCompleto(participante);

    return (

      <li
        key={
          participante.puuid ??
          `${participante.nombre}-${participante.campeon.nombre}`
        }
        className={
          participante.es_jugador
            ? "modal-player-row highlighted"
            : "modal-player-row"
        }
      >

        {
          renderIconoCampeon(
            participante.campeon.nombre,
            "modal-champion-icon"
          )
        }

        <div className="modal-player-name">

          <strong title={nombre}>
            {nombre}
          </strong>

          <span>
            {participante.campeon.nombre ?? "Campeón"}
            {" · "}
            {formatearRol(participante.posicion)}
            {" · Nv. "}
            {participante.campeon.nivel ?? "-"}
          </span>

        </div>

        <div className="modal-player-kda">

          <strong>
            {participante.combate.kills}/
            {participante.combate.muertes}/
            {participante.combate.asistencias}
          </strong>

          <span>
            KDA {participante.combate.kda.toFixed(2)}
          </span>

        </div>

        <dl className="modal-player-stats">

          <div>
            <dt>CS</dt>
            <dd>{participante.recursos.cs}</dd>
          </div>

          <div>
            <dt>Oro</dt>
            <dd>{formatearMiles(participante.recursos.oro)}</dd>
          </div>

          <div>
            <dt>Daño</dt>
            <dd>{formatearMiles(participante.daño.campeones)}</dd>
          </div>

          <div>
            <dt>Visión</dt>
            <dd>{participante.vision.score}</dd>
          </div>

        </dl>

        {
          renderObjetos(
            participante.objetos
          )
        }

      </li>

    );

  };


  const renderObjetivos = (
    objetivos: {
      aliados: ObjetivosEquipo;
      rivales: ObjetivosEquipo;
    }
  ) => {

    const filas: {
      etiqueta: string;
      aliado: string | number;
      rival: string | number;
    }[] = [
      {
        etiqueta: "Oro total",
        aliado: formatearMiles(objetivos.aliados.oro),
        rival: formatearMiles(objetivos.rivales.oro),
      },
      {
        etiqueta: "Torres",
        aliado: objetivos.aliados.torres,
        rival: objetivos.rivales.torres,
      },
      {
        etiqueta: "Dragones",
        aliado: objetivos.aliados.dragones,
        rival: objetivos.rivales.dragones,
      },
      {
        etiqueta: "Barones",
        aliado: objetivos.aliados.barones,
        rival: objetivos.rivales.barones,
      },
    ];

    // Heraldos y larvas solo si vienen en la partida
    if (
      objetivos.aliados.heraldos > 0 ||
      objetivos.rivales.heraldos > 0
    ) {

      filas.push({
        etiqueta: "Heraldos",
        aliado: objetivos.aliados.heraldos,
        rival: objetivos.rivales.heraldos,
      });

    }

    if (
      objetivos.aliados.larvas !== undefined ||
      objetivos.rivales.larvas !== undefined
    ) {

      filas.push({
        etiqueta: "Larvas",
        aliado: objetivos.aliados.larvas ?? 0,
        rival: objetivos.rivales.larvas ?? 0,
      });

    }

    return (

      <div className="match-modal-objetivos">

        {
          filas.map((fila) => (

            <div key={fila.etiqueta}>

              <span className="aliado">{fila.aliado}</span>

              <span className="etiqueta">{fila.etiqueta}</span>

              <span className="rival">{fila.rival}</span>

            </div>

          ))
        }

      </div>

    );

  };


  const renderContenido = (
    datos: DetallePartida
  ) => (

    <div className="match-modal-body">

      {/* b) MARCADOR POR EQUIPO */}

      <section
        className="match-modal-marcador"
        aria-label="Marcador por equipo"
      >

        <div className="match-modal-score">

          <div className="aliado">

            <span>Tu equipo</span>

            <strong>
              {
                datos.objetivos?.aliados.kills ??
                sumar(aliados, (p) => p.combate.kills)
              }
            </strong>

          </div>

          <span className="match-modal-vs">
            <b>VS</b>
          </span>

          <div className="rival">

            <span>Equipo rival</span>

            <strong>
              {
                datos.objetivos?.rivales.kills ??
                sumar(rivales, (p) => p.combate.kills)
              }
            </strong>

          </div>

        </div>

        {
          datos.objetivos ? (

            renderObjetivos(
              datos.objetivos
            )

          ) : (

            <p className="match-modal-aviso">
              Objetivos no disponibles
            </p>

          )
        }

      </section>


      {/* c) DUELO DE LÍNEA */}

      {
        jugador && rivalDeLinea && (

          <section
            className="match-modal-duelo"
            aria-label="Duelo de línea"
          >

            <h3>
              Duelo de línea · {formatearRol(jugador.posicion)}
            </h3>

            <div className="duelo-campeones">

              <div className="duelo-campeon">

                {
                  renderIconoCampeon(
                    jugador.campeon.nombre,
                    "duelo-icono"
                  )
                }

                <div>
                  <strong>{jugador.campeon.nombre}</strong>
                  <span title={nombreCompleto(jugador)}>Tú</span>
                </div>

              </div>

              <span className="duelo-vs">VS</span>

              <div className="duelo-campeon rival">

                {
                  renderIconoCampeon(
                    rivalDeLinea.campeon.nombre,
                    "duelo-icono"
                  )
                }

                <div>
                  <strong>{rivalDeLinea.campeon.nombre}</strong>
                  <span title={nombreCompleto(rivalDeLinea)}>
                    {nombreCompleto(rivalDeLinea)}
                  </span>
                </div>

              </div>

            </div>

            <div className="duelo-filas">

              {
                crearFilasDuelo(jugador, rivalDeLinea).map((fila) => (

                  <div key={fila.etiqueta}>

                    <span className="propio">{fila.propio}</span>

                    <span className="etiqueta">
                      {fila.etiqueta}
                      <span
                        className={
                          `duelo-diferencia ${claseDiferencia(fila.diferencia)}`
                        }
                      >
                        {fila.textoDiferencia}
                      </span>
                    </span>

                    <span className="rival">{fila.rival}</span>

                  </div>

                ))
              }

            </div>

          </section>

        )
      }


      {/* d) LOS 10 JUGADORES */}

      <div className="match-modal-teams">

        <section className="match-modal-team">

          <h3 className="match-modal-team-title">
            Tu equipo
          </h3>

          <ul className="match-modal-player-list">
            {aliados.map(renderJugador)}
          </ul>

        </section>

        <section className="match-modal-team enemy">

          <h3 className="match-modal-team-title">
            Equipo rival
          </h3>

          <ul className="match-modal-player-list">
            {rivales.map(renderJugador)}
          </ul>

        </section>

      </div>


      {/* e) RESUMEN */}

      {
        datos.resumen && (

          <section className="match-modal-resumen">

            <h3>Resumen de la partida</h3>

            <p>{datos.resumen}</p>

          </section>

        )
      }

    </div>

  );


  // ----------------------------------------------------------
  // Ventana
  // ----------------------------------------------------------

  return createPortal(

    <div
      className={`match-modal-backdrop${cerrando ? " cerrando" : ""}`}
      onMouseDown={(event) => {

        // Solo cierra con clic fuera de la ventana
        if (event.target === event.currentTarget) {
          cerrar();
        }

      }}
    >

      <div
        className={`match-modal${cerrando ? " cerrando" : ""}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="match-modal-titulo"
      >

        {/* a) CABECERA */}

        <header className="match-modal-header">

          <div>

            <span
              className={
                victoria
                  ? "match-modal-result win"
                  : "match-modal-result loss"
              }
            >
              {victoria ? "Victoria" : "Derrota"}
            </span>

            <h2 id="match-modal-titulo">
              Detalle de la partida
            </h2>

            <p>
              Clasificatoria Solo/Dúo
              {" · "}
              {formatearDuracion(duracion)}
              {fecha ? ` · ${fecha}` : ""}
            </p>

          </div>

          <button
            ref={botonCerrarRef}
            type="button"
            className="match-modal-close"
            onClick={cerrar}
            aria-label="Cerrar detalle"
          >
            ×
          </button>

        </header>


        {
          detalle ? (

            renderContenido(detalle)

          ) : (

            <div
              className="match-modal-empty"
              role={errorDetalle ? "alert" : "status"}
            >

              {
                cargando && (
                  <span
                    className="match-modal-spinner"
                    aria-hidden="true"
                  />
                )
              }

              <strong>
                {
                  cargando
                    ? "Cargando detalle..."
                    : "No se pudo cargar la partida"
                }
              </strong>

              <p>
                {
                  cargando
                    ? "Consultando la información de los diez participantes."
                    : errorDetalle ??
                      "Esta partida no tiene un identificador válido."
                }
              </p>

              {
                errorDetalle && (

                  <button
                    type="button"
                    className="match-modal-retry"
                    onClick={reintentar}
                  >
                    Reintentar
                  </button>

                )
              }

            </div>

          )
        }

      </div>

    </div>,

    document.body

  );

}


export default MatchDetailModal;
