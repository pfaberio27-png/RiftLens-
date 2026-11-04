import {
  useEffect,
  useState,
} from "react";

import type {
  KeyboardEvent,
} from "react";

import type {
  AnalisisResponse,
  PartidaReciente,
} from "../types/analisis";

import MatchDetailModal
  from "./MatchDetailModal";

import {
  formatearRol,
} from "../utils/formatters";


type PartidasRecientes =
  AnalisisResponse["analisis"]["partidas_recientes"];


interface RecentMatchesProps {
  partidas: PartidasRecientes;
  // Necesarios para pedir el detalle de cada partida.
  puuid: string;
  region: string;
}


function RecentMatches({
  partidas,
  puuid,
  region,
}: RecentMatchesProps) {

  const PARTIDAS_POR_PAGINA = 10;

  const [
    paginaActual,
    setPaginaActual,
  ] = useState(0);


  useEffect(() => {

    setPaginaActual(0);

  }, [partidas]);


  const totalPartidas =
    partidas.length;


  const totalPaginas =
    Math.ceil(
      totalPartidas /
      PARTIDAS_POR_PAGINA
    );


  const inicio =
    paginaActual *
    PARTIDAS_POR_PAGINA;


  const fin =
    Math.min(
      inicio +
        PARTIDAS_POR_PAGINA,
      totalPartidas
    );


  const partidasVisibles =
    partidas.slice(
      inicio,
      fin
    );


  // Partida abierta en el modal de detalle
  const [
    partidaSeleccionada,
    setPartidaSeleccionada,
  ] = useState<PartidaReciente | null>(null);


  // Los remakes no se pueden abrir.
  const abrirPartida = (
    partida: PartidaReciente
  ) => {

    if (
      partida.remake ||
      !partida.match_id
    ) {
      return;
    }

    setPartidaSeleccionada(
      partida
    );

  };


  const irAnterior = () => {

    setPaginaActual(
      (pagina) =>
        Math.max(
          pagina - 1,
          0
        )
    );

  };


  const irSiguiente = () => {

    setPaginaActual(
      (pagina) =>
        Math.min(
          pagina + 1,
          totalPaginas - 1
        )
    );

  };


  return (

    <section className="recent-section">


      <div className="section-head">

        <div>

          <h2>
            Actividad reciente en la Grieta
          </h2>

        </div>

      </div>


      <div className="match-strip">

        {
          partidasVisibles.map(
            (
              partida,
              index
            ) => {

              const esRemake =
                Boolean(
                  partida.remake
                );

              const sePuedeAbrir =
                !esRemake &&
                Boolean(
                  partida.match_id
                );

              const claseResultado =
                esRemake
                  ? "remake"
                  : partida.victoria
                    ? "win"
                    : "loss";

              return (

              <article
                key={
                  partida.match_id ??
                  `${paginaActual}-${index}`
                }
                className={
                  `match-card ${claseResultado}` +
                  (
                    sePuedeAbrir
                      ? " clickable"
                      : ""
                  )
                }
                {
                  ...(
                    sePuedeAbrir
                      ? {
                          role: "button",
                          tabIndex: 0,
                          "aria-label":
                            `Ver detalle de la partida con ${partida.campeon.nombre}`,
                          onClick: () =>
                            abrirPartida(
                              partida
                            ),
                          onKeyDown: (
                            event: KeyboardEvent<HTMLElement>
                          ) => {

                            if (
                              event.key === "Enter" ||
                              event.key === " "
                            ) {

                              event.preventDefault();

                              abrirPartida(
                                partida
                              );

                            }

                          },
                        }
                      : {
                          "aria-disabled": esRemake
                            ? true
                            : undefined,
                        }
                  )
                }
              >

                {
                  partida
                    .campeon
                    .imagen_icono && (

                    <img
                      className="champ-icon"
                      src={
                        partida
                          .campeon
                          .imagen_icono
                      }
                      alt={
                        partida
                          .campeon
                          .nombre
                      }
                      onError={(event) => {

                        event
                          .currentTarget
                          .style
                          .display =
                          "none";

                      }}
                    />

                  )
                }


                <div className="match-kda">

                  {
                    partida
                      .combate
                      .kills
                  }

                  /

                  {
                    partida
                      .combate
                      .muertes
                  }

                  /

                  {
                    partida
                      .combate
                      .asistencias
                  }

                </div>


                <div className="match-meta">

                  {
                    partida
                      .campeon
                      .nombre
                  }

                  {" · "}

                  {
                    formatearRol(
                      partida.rol
                    )
                  }

                  {" · "}

                  {
                    Math.round(
                      partida
                        .duracion_minutos
                    )
                  }

                  {" min"}

                </div>


                <div className="match-result">

                  {
                    esRemake
                      ? "Remake / no válida"
                      : partida.victoria
                        ? "Victoria"
                        : "Derrota"
                  }

                </div>

              </article>

              );

            }
          )
        }

      </div>


      {
        totalPartidas > 0 && (

          <div className="matches-pagination">

            {
              totalPaginas > 1 && (

                <div className="matches-pagination-buttons">

                  <button
                    type="button"
                    className="pagination-button"
                    onClick={
                      irAnterior
                    }
                    disabled={
                      paginaActual === 0
                    }
                  >
                    ← Anterior
                  </button>


                  <span className="pagination-page">

                    Página{" "}

                    <strong>
                      {paginaActual + 1}
                    </strong>

                    {" de "}

                    <strong>
                      {totalPaginas}
                    </strong>

                  </span>


                  <button
                    type="button"
                    className="pagination-button"
                    onClick={
                      irSiguiente
                    }
                    disabled={
                      paginaActual >=
                      totalPaginas - 1
                    }
                  >
                    Siguiente →
                  </button>

                </div>

              )
            }

          </div>

        )
      }


      {/* ========================================================
          MODAL DE DETALLE DE PARTIDA
      ======================================================== */}

      {
        partidaSeleccionada && (

          <MatchDetailModal
            partida={
              partidaSeleccionada
            }
            puuid={puuid}
            region={region}
            onCerrar={() => {

              setPartidaSeleccionada(
                null
              );

            }}
          />

        )
      }


    </section>

  );
}


export default RecentMatches;