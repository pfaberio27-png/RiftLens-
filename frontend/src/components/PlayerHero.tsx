import {
  useState,
} from "react";

import type {
  AnalisisResponse,
} from "../types/analisis";

import {
  formatearRol,
  traducirTier,
} from "../utils/formatters";


type Analisis =
  AnalisisResponse["analisis"];


interface PlayerHeroProps {
  analisis: Analisis;
}


function PlayerHero({
  analisis,
}: PlayerHeroProps) {

  const rango =
    analisis.jugador.rango;

  const insignia =
    analisis.campeon_insignia;

  const etiquetas =
    analisis.etiquetas ?? [];


  // Etiqueta cuyo motivo se muestra al tocarla (celular).
  // En escritorio el motivo también aparece con hover/foco.
  const [
    etiquetaActiva,
    setEtiquetaActiva,
  ] = useState<number | null>(null);


  // ============================================================
  // PARTIDAS PROCESADAS Y WIN RATE GENERAL
  // ============================================================

  // Los remakes vienen marcados en el historial y no cuentan
  // para ningún cálculo.
  const partidasValidas =
    analisis.partidas_recientes.filter(
      (partida) => !partida.remake
    );

  const cantidadRemakes =
    analisis.partidas_recientes.length
    - partidasValidas.length;

  const victoriasValidas =
    partidasValidas.filter(
      (partida) => partida.victoria
    ).length;

  const winRateGeneral =
    partidasValidas.length > 0
      ? Math.round(
        (victoriasValidas / partidasValidas.length)
        * 1000
      ) / 10
      : null;


  return (

    <section className="player-hero">


      <div className="player-hero-left">


        <div className="rank-wrapper">

          <div className="rank-tag">

            <span className="rank-dot" />

            {
              rango?.clasificado
                ? (
                  <>

                    {
                      traducirTier(
                        rango.tier
                      )
                    }

                    {
                      rango.division
                        ? ` ${rango.division}`
                        : ""
                    }

                    {" · "}

                    {rango.cola}

                    {" · Temporada 2026"}

                  </>
                )
                : (
                  <>
                    Sin clasificación · Solo/Duo · Temporada 2026
                  </>
                )
            }

          </div>


          {
            rango?.clasificado && (

              <div className="rank-details">

                <span>
                  {rango.lp} LP
                </span>

                <span>
                  {" · "}
                </span>

                <span className="rank-wins">
                  {rango.victorias} V
                </span>

                <span>
                  {" · "}
                </span>

                <span className="rank-losses">
                  {rango.derrotas} D
                </span>

              </div>

            )
          }

        </div>


        <h2 className="player-title">

          {analisis.jugador.nombre}

          <span>
            #{analisis.jugador.tag}
          </span>

        </h2>


        <p className="player-subtitle">

          {
            analisis.muestra
              .partidas_obtenidas
          }
          {" "}partidas clasificatorias Solo/Dúo procesadas

          {
            cantidadRemakes > 0 && (

              <>
                {" "}(+ {cantidadRemakes}{" "}
                {
                  cantidadRemakes === 1
                    ? "remake no válido"
                    : "remakes no válidos"
                })
              </>

            )
          }

          .

          {" "}

          Rol principal:{" "}

          <strong>
            {
              formatearRol(
                analisis.muestra
                  .rol_principal
              )
            }
          </strong>

          .

        </p>


        {/* =====================================================
            ETIQUETAS DE CUALIDADES
        ===================================================== */}

        {
          (
            etiquetas.length > 0
            || analisis.resumen_jugador
          ) && (

            <div className="hero-etiquetas">

              {
                etiquetas.length > 0 && (

                  <ul className="etiquetas-lista">

                    {
                      etiquetas.map(
                        (
                          etiqueta,
                          index
                        ) => (

                          <li key={etiqueta.texto}>

                            <button
                              type="button"
                              className={
                                `etiqueta-chip ${etiqueta.tipo}`
                                + (
                                  etiquetaActiva === index
                                    ? " activa"
                                    : ""
                                )
                              }
                              aria-describedby={
                                `etiqueta-motivo-${index}`
                              }
                              onClick={() =>
                                setEtiquetaActiva(
                                  etiquetaActiva === index
                                    ? null
                                    : index
                                )
                              }
                              onBlur={() =>
                                setEtiquetaActiva(null)
                              }
                            >

                              {etiqueta.texto}

                              <span
                                id={
                                  `etiqueta-motivo-${index}`
                                }
                                role="tooltip"
                                className="etiqueta-tooltip"
                              >
                                {etiqueta.motivo}
                              </span>

                            </button>

                          </li>

                        )
                      )
                    }

                  </ul>

                )
              }

              {
                analisis.resumen_jugador && (

                  <p className="resumen-jugador">
                    {analisis.resumen_jugador}
                  </p>

                )
              }

            </div>

          )
        }


        <div className="hero-stats">


          <div className="hero-stat">

            <strong className="win">

              {
                winRateGeneral ?? "—"
              }

              {
                winRateGeneral !== null && "%"
              }

            </strong>

            <span>

              Win rate general ·{" "}

              {partidasValidas.length}

              {" PJ"}

            </span>

          </div>


          {
            insignia.nombre && (

              <div className="hero-stat hero-stat-insignia">

                {
                  insignia.imagen_icono && (

                    <img
                      className="insignia-icono"
                      src={insignia.imagen_icono}
                      alt={insignia.nombre}
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

                <div>

                  <strong>
                    {insignia.nombre}
                  </strong>

                  <span>

                    Campeón insignia

                    {
                      insignia.win_rate !== null
                      && insignia.win_rate !== undefined
                      && ` · ${insignia.win_rate}% WR`
                    }

                    {` · ${insignia.partidas} PJ`}

                  </span>

                </div>

              </div>

            )
          }


        </div>


        <div className="form-strip">

          {
            analisis
              .forma_reciente
              .resultados
              .map(
                (
                  resultado,
                  index
                ) => (

                  <div
                    key={index}
                    className={
                      resultado === "V"
                        ? "form-pip win"
                        : "form-pip loss"
                    }
                  >
                    {resultado}
                  </div>

                )
              )
          }

        </div>


      </div>


      <div className="player-hero-right">


        {
          insignia.imagen_splash && (

            <img
              src={insignia.imagen_splash}
              alt={
                insignia.nombre ??
                "Campeón"
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


        <div className="champion-caption">

          <span>
            Campeón insignia
          </span>

          <strong>

            {
              insignia.nombre ??
              "Sin determinar"
            }

          </strong>

        </div>


      </div>


    </section>

  );
}


export default PlayerHero;
