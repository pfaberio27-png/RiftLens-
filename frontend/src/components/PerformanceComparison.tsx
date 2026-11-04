import {
  useState,
} from "react";

import type {
  AnalisisResponse,
  Comparacion,
} from "../types/analisis";

import ComparisonBar, {
  AyudaMetrica,
} from "./ComparisonBar";

import {
  formatearRol,
  formatearValorMetrica,
} from "../utils/formatters";

import {
  MINIMO_PARTIDAS_CONFIABLE,
} from "../utils/metricas";


type Analisis =
  AnalisisResponse["analisis"];


type PestanaInsignia =
  | "pro"
  | "promedio";


interface PerformanceComparisonProps {
  analisis: Analisis;
}


// ============================================================
// BARRAS VS NIVEL PRO (6 métricas con referencia)
// ============================================================

function BarrasNivelPro({
  comparacion,
  partidas,
}: {
  comparacion: Comparacion;
  partidas: number;
}) {

  return (

    <div className="comparacion-barras">

      {
        Object.entries(
          comparacion
        ).map(
          ([
            clave,
            datos,
          ]) => (

            <ComparisonBar
              key={clave}
              clave={clave}
              nombre={datos.nombre}
              jugador={datos.jugador}
              referencia={datos.referencia}
              diferenciaPorcentual={
                datos.diferencia_porcentual
              }
              estado={datos.estado}
              etiquetaReferencia="Nivel pro"
              partidasConDato={partidas}
            />

          )
        )
      }

    </div>

  );
}


function PerformanceComparison({
  analisis,
}: PerformanceComparisonProps) {

  const [
    pestana,
    setPestana,
  ] = useState<PestanaInsignia>("pro");

  const insignia =
    analisis.campeon_insignia;

  const estadisticasInsignia =
    insignia.estadisticas;

  const comparacionProInsignia =
    insignia.comparacion_profesional ?? null;

  const comparacionAdicionalInsignia =
    insignia.comparacion_adicional ?? null;

  const metricasAdicionales =
    analisis.metricas_adicionales ?? null;


  return (

    <section className="section comparison-section">


      <div className="section-head">

        <div>

          <h2>
            ¿Qué tan cerca estás del nivel pro?
          </h2>

        </div>

      </div>


      {/* ================================================
          VS NIVEL PRO (rol principal)
      ================================================ */}

      <div className="comparacion-bloque">

        <h3 className="comparacion-bloque-titulo">

          Vs nivel pro

          <span>
            {" · "}
            {
              formatearRol(
                analisis.muestra.rol_principal
              )
            }
          </span>

        </h3>

        <BarrasNivelPro
          comparacion={analisis.comparacion}
          partidas={
            analisis.muestra.partidas_analizadas
          }
        />

      </div>


      {/* ================================================
          PERFIL DEL CAMPEÓN INSIGNIA
      ================================================ */}

      <div className="compare-wrap comparacion-bloque">


        <div className="compare-champ">


          <div className="compare-champ-image">

            {
              insignia.imagen_splash && (

                <img
                  src={insignia.imagen_splash}
                  alt={
                    insignia.nombre ??
                    "Campeón"
                  }
                />

              )
            }

          </div>


          <div className="compare-champ-body">

            <span className="compare-role">

              {"Campeón insignia · "}

              {
                formatearRol(
                  analisis.muestra.rol_principal
                )
              }

            </span>


            <h3 className="compare-champ-nombre">

              {
                insignia.imagen_icono && (
                  <img
                    className="compare-champ-icono"
                    src={insignia.imagen_icono}
                    alt=""
                  />
                )
              }

              {
                insignia.nombre ??
                "Sin determinar"
              }

            </h3>


            <p>

              {insignia.partidas}

              {" partidas jugadas"}

              {
                insignia.partidas > 0
                && insignia.partidas
                  < MINIMO_PARTIDAS_CONFIABLE && (
                  <span className="comparacion-pocas">
                    {" (pocas partidas)"}
                  </span>
                )
              }

            </p>


            <dl className="compare-champ-stats">

              <div>
                <dt>Win rate</dt>
                <dd>
                  {
                    formatearValorMetrica(
                      "win_rate",
                      estadisticasInsignia
                        ?.resultados
                        .win_rate
                    )
                  }
                </dd>
              </div>

              <div>
                <dt>KDA</dt>
                <dd>
                  {
                    formatearValorMetrica(
                      "kda",
                      estadisticasInsignia
                        ?.combate
                        .kda_promedio
                    )
                  }
                </dd>
              </div>

              <div>
                <dt>Oro/min</dt>
                <dd>
                  {
                    formatearValorMetrica(
                      "oro_por_minuto",
                      estadisticasInsignia
                        ?.economia
                        .oro_por_minuto_promedio
                    )
                  }
                </dd>
              </div>

            </dl>

          </div>


        </div>


        <div className="comparacion-insignia">

          <div
            className="comparacion-tabs"
            role="tablist"
            aria-label="Comparaciones del campeón insignia"
          >

            <button
              type="button"
              role="tab"
              id="tab-insignia-pro"
              aria-controls="panel-insignia"
              aria-selected={pestana === "pro"}
              className={
                pestana === "pro"
                  ? "activo"
                  : ""
              }
              onClick={() =>
                setPestana("pro")
              }
            >
              Vs nivel pro
            </button>

            <button
              type="button"
              role="tab"
              id="tab-insignia-promedio"
              aria-controls="panel-insignia"
              aria-selected={pestana === "promedio"}
              className={
                pestana === "promedio"
                  ? "activo"
                  : ""
              }
              onClick={() =>
                setPestana("promedio")
              }
            >
              Vs tu promedio
            </button>

          </div>


          <div
            id="panel-insignia"
            role="tabpanel"
            aria-labelledby={
              pestana === "pro"
                ? "tab-insignia-pro"
                : "tab-insignia-promedio"
            }
          >

            {
              pestana === "pro" && (

                comparacionProInsignia
                  ? (
                    <BarrasNivelPro
                      comparacion={
                        comparacionProInsignia
                      }
                      partidas={insignia.partidas}
                    />
                  )
                  : (
                    <p className="empty-text">
                      Sin datos del campeón insignia.
                    </p>
                  )

              )
            }


            {
              pestana === "promedio" && (

                comparacionAdicionalInsignia
                  ? (
                    <>

                      <div className="comparacion-barras">

                        {
                          Object.entries(
                            comparacionAdicionalInsignia
                          ).map(
                            ([
                              clave,
                              datos,
                            ]) => (

                              <ComparisonBar
                                key={clave}
                                clave={clave}
                                nombre={datos.nombre}
                                jugador={datos.jugador}
                                referencia={datos.referencia}
                                diferenciaPorcentual={
                                  datos.diferencia_porcentual
                                }
                                estado={datos.estado}
                                etiquetaReferencia="Tu promedio"
                                unidad={datos.unidad}
                                menorEsMejor={
                                  datos.menor_es_mejor
                                }
                                partidasConDato={
                                  datos.partidas_con_dato
                                }
                              />

                            )
                          )
                        }

                      </div>

                      <p className="comparacion-nota">
                        Comparado con tu promedio en todas tus partidas
                      </p>

                    </>
                  )
                  : (
                    <p className="empty-text">
                      Sin datos del campeón insignia.
                    </p>
                  )

              )
            }

          </div>

        </div>


      </div>


      {/* ================================================
          TUS PROMEDIOS GENERALES
      ================================================ */}

      {
        metricasAdicionales && (

          <div className="comparacion-bloque">

            <h3 className="comparacion-bloque-titulo">
              Tus promedios generales
            </h3>

            <div className="promedios-grid">

              {
                Object.entries(
                  metricasAdicionales
                ).map(
                  ([
                    clave,
                    datos,
                  ]) => (

                    <article
                      key={clave}
                      className="promedio-card"
                    >

                      <div className="comparacion-barra-head">

                        <span className="comparacion-barra-nombre">
                          {datos.nombre}
                        </span>

                        <AyudaMetrica
                          clave={clave}
                          nombre={datos.nombre}
                        />

                      </div>

                      <strong
                        className={
                          datos.valor === null
                            ? "promedio-valor sin-dato"
                            : "promedio-valor"
                        }
                      >
                        {
                          formatearValorMetrica(
                            clave,
                            datos.valor,
                            datos.unidad
                          )
                        }
                      </strong>

                      {
                        datos.partidas_con_dato > 0
                        && datos.partidas_con_dato
                          < MINIMO_PARTIDAS_CONFIABLE && (
                          <span className="comparacion-pocas">
                            (pocas partidas)
                          </span>
                        )
                      }

                    </article>

                  )
                )
              }

            </div>

          </div>

        )
      }


    </section>

  );
}


export default PerformanceComparison;
