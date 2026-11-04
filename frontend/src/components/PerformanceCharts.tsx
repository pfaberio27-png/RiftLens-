import {
  useMemo,
  useState,
} from "react";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type {
  GraficosRendimiento,
  PuntoGraficoRendimiento,
} from "../types/analisis";

import {
  formatearRol,
} from "../utils/formatters";


interface PerformanceChartsProps {
  graficos: GraficosRendimiento;

  rolPrincipal: string;

  // Partidas válidas totales (todas las posiciones), como en la portada
  totalPartidasValidas: number;
}


type TipoGrafico =
  | "kda"
  | "recursos"
  | "daño"
  | "win_rate";


interface TooltipProps {
  active?: boolean;

  payload?: Array<{
    payload: PuntoGraficoRendimiento;
  }>;
}


function PerformanceTooltip({
  active,
  payload,
}: TooltipProps) {

  if (
    !active ||
    !payload ||
    payload.length === 0
  ) {
    return null;
  }


  const partida =
    payload[0].payload;


  return (

    <div className="performance-tooltip">

      <div className="performance-tooltip-head">

        <strong>
          Partida {partida.numero}
        </strong>

        <span
          className={
            partida.victoria
              ? "victoria"
              : "derrota"
          }
        >
          {
            partida.victoria
              ? "VICTORIA"
              : "DERROTA"
          }
        </span>

      </div>


      <span className="performance-tooltip-champion">
        {partida.campeon}
      </span>


      <div className="performance-tooltip-grid">

        <span>
          KDA
          <strong>
            {partida.kda.toFixed(2)}
          </strong>
        </span>


        <span>
          CS / MIN
          <strong>
            {partida.cs_por_minuto.toFixed(2)}
          </strong>
        </span>


        <span>
          ORO / MIN
          <strong>
            {partida.oro_por_minuto.toFixed(2)}
          </strong>
        </span>


        <span>
          DAÑO / MIN
          <strong>
            {partida.daño_por_minuto.toFixed(2)}
          </strong>
        </span>


        <span>
          VISIÓN
          <strong>
            {partida.vision_score.toFixed(2)}
          </strong>
        </span>


        <span>
          WIN RATE
          <strong>
            {partida.win_rate_acumulado.toFixed(2)}%
          </strong>
        </span>

      </div>

    </div>

  );

}


function PerformanceCharts({
  graficos,
  rolPrincipal,
  totalPartidasValidas,
}: PerformanceChartsProps) {

  const [
    graficoActivo,
    setGraficoActivo,
  ] = useState<TipoGrafico>(
    "kda"
  );


  const datos =
    graficos?.partidas ?? [];


  const resumen =
    graficos?.resumen;


  const ultimaPartida =
    datos.length > 0
      ? datos[datos.length - 1]
      : null;


  const tituloGrafico =
    useMemo(
      () => {

        switch (graficoActivo) {

          case "recursos":
            return "Evolución de recursos";

          case "daño":
            return "Daño por minuto";

          case "win_rate":
            return "Win Rate acumulado";

          default:
            return "KDA por partida";

        }

      },
      [graficoActivo]
    );


  if (
    !graficos ||
    !graficos.disponible ||
    datos.length === 0
  ) {

    return (

      <section className="section">

        <div className="section-head">

          <div>

            <span className="section-eyebrow">
              HU13 · EVOLUCIÓN
            </span>

            <h2>
              Evolución del rendimiento
            </h2>

          </div>

          <p>
            No existen datos suficientes
            para generar los gráficos.
          </p>

        </div>

      </section>

    );

  }


  return (

    <section
      className="
        section
        performance-charts-section
      "
    >

      {/* ======================================================
          CABECERA
      ====================================================== */}

      <div className="section-head">

        <div>

          <span className="section-eyebrow">
            EVOLUCIÓN DEL RENDIMIENTO
          </span>

          <h2>
            Métricas a través de las partidas
          </h2>

        </div>


        <p>

          <strong>
            {graficos.cantidad_partidas}
          </strong>

          {/* Si el rol principal no cubre todas las partidas válidas,
              se indica el total para que cuadre con la portada */}
          {
            graficos.cantidad_partidas <
              totalPartidasValidas && (
              <>
                {" "}de{" "}
                <strong>
                  {totalPartidasValidas}
                </strong>
              </>
            )
          }

          {" "}partidas válidas · rol principal:{" "}

          <strong>
            {formatearRol(rolPrincipal)}
          </strong>

        </p>

      </div>


      {/* ======================================================
          SELECTOR
      ====================================================== */}

      <div className="performance-chart-tabs">

        <button
          type="button"
          className={
            graficoActivo === "kda"
              ? "activo"
              : ""
          }
          onClick={
            () =>
              setGraficoActivo(
                "kda"
              )
          }
        >
          KDA
        </button>


        <button
          type="button"
          className={
            graficoActivo === "recursos"
              ? "activo"
              : ""
          }
          onClick={
            () =>
              setGraficoActivo(
                "recursos"
              )
          }
        >
          Recursos
        </button>


        <button
          type="button"
          className={
            graficoActivo === "daño"
              ? "activo"
              : ""
          }
          onClick={
            () =>
              setGraficoActivo(
                "daño"
              )
          }
        >
          Daño
        </button>


        <button
          type="button"
          className={
            graficoActivo === "win_rate"
              ? "activo"
              : ""
          }
          onClick={
            () =>
              setGraficoActivo(
                "win_rate"
              )
          }
        >
          Win Rate
        </button>

      </div>


      {/* ======================================================
          CONTENEDOR
      ====================================================== */}

      <div className="performance-chart-card">

        <div className="performance-chart-title">

          <div>

            <span>
              TENDENCIA
            </span>

            <h3>
              {tituloGrafico}
            </h3>

          </div>


          <div className="performance-chart-direction">

            <span>
              Más antigua
            </span>

            <div />

            <span>
              Más reciente
            </span>

          </div>

        </div>


        {/* ====================================================
            GRÁFICO
        ==================================================== */}

        <div className="performance-chart-container">

          <ResponsiveContainer
            width="100%"
            height="100%"
          >

            <LineChart
              data={datos}
              margin={{
                top: 15,
                right: 25,
                left: 5,
                bottom: 10,
              }}
            >

              <CartesianGrid
                stroke="rgba(200, 170, 110, 0.08)"
                vertical={false}
              />


              <XAxis
                dataKey="numero"
                tick={{
                  fill: "#7f8b99",
                  fontSize: 9,
                }}
                tickLine={false}
                axisLine={{
                  stroke:
                    "rgba(200, 170, 110, 0.15)",
                }}
                minTickGap={25}
              />


              {/* ==============================================
                  KDA
              ============================================== */}

              {
                graficoActivo ===
                  "kda" && (

                  <>

                    <YAxis
                      tick={{
                        fill: "#7f8b99",
                        fontSize: 9,
                      }}
                      tickLine={false}
                      axisLine={false}
                      width={40}
                    />

                    <Tooltip
                      content={
                        <PerformanceTooltip />
                      }
                    />

                    <Line
                      type="monotone"
                      dataKey="kda"
                      stroke="#c8aa6e"
                      strokeWidth={2}
                      dot={false}
                      activeDot={{
                        r: 5,
                      }}
                    />

                  </>

                )
              }


              {/* ==============================================
                  RECURSOS
              ============================================== */}

              {
                graficoActivo ===
                  "recursos" && (

                  <>

                    <YAxis
                      yAxisId="cs"
                      orientation="left"
                      tick={{
                        fill: "#7f8b99",
                        fontSize: 9,
                      }}
                      tickLine={false}
                      axisLine={false}
                      width={40}
                    />


                    <YAxis
                      yAxisId="oro"
                      orientation="right"
                      tick={{
                        fill: "#7f8b99",
                        fontSize: 9,
                      }}
                      tickLine={false}
                      axisLine={false}
                      width={50}
                    />


                    <Tooltip
                      content={
                        <PerformanceTooltip />
                      }
                    />


                    <Line
                      yAxisId="cs"
                      type="monotone"
                      dataKey="cs_por_minuto"
                      stroke="#0ac8b9"
                      strokeWidth={2}
                      dot={false}
                      activeDot={{
                        r: 5,
                      }}
                    />


                    <Line
                      yAxisId="oro"
                      type="monotone"
                      dataKey="oro_por_minuto"
                      stroke="#c8aa6e"
                      strokeWidth={2}
                      dot={false}
                      activeDot={{
                        r: 5,
                      }}
                    />

                  </>

                )
              }


              {/* ==============================================
                  DAÑO
              ============================================== */}

              {
                graficoActivo ===
                  "daño" && (

                  <>

                    <YAxis
                      tick={{
                        fill: "#7f8b99",
                        fontSize: 9,
                      }}
                      tickLine={false}
                      axisLine={false}
                      width={55}
                    />

                    <Tooltip
                      content={
                        <PerformanceTooltip />
                      }
                    />

                    <Line
                      type="monotone"
                      dataKey="daño_por_minuto"
                      stroke="#d36a6a"
                      strokeWidth={2}
                      dot={false}
                      activeDot={{
                        r: 5,
                      }}
                    />

                  </>

                )
              }


              {/* ==============================================
                  WIN RATE
              ============================================== */}

              {
                graficoActivo ===
                  "win_rate" && (

                  <>

                    <YAxis
                      domain={[0, 100]}
                      tick={{
                        fill: "#7f8b99",
                        fontSize: 9,
                      }}
                      tickFormatter={
                        (valor) =>
                          `${valor}%`
                      }
                      tickLine={false}
                      axisLine={false}
                      width={45}
                    />

                    <Tooltip
                      content={
                        <PerformanceTooltip />
                      }
                    />

                    <Line
                      type="monotone"
                      dataKey="win_rate_acumulado"
                      stroke="#52c7a5"
                      strokeWidth={2}
                      dot={false}
                      activeDot={{
                        r: 5,
                      }}
                    />

                  </>

                )
              }

            </LineChart>

          </ResponsiveContainer>

        </div>


        {/* ====================================================
            LEYENDA RECURSOS
        ==================================================== */}

        {
          graficoActivo ===
            "recursos" && (

            <div className="performance-chart-legend">

              <span>
                <i className="cs" />
                CS / min
              </span>

              <span>
                <i className="oro" />
                Oro / min
              </span>

            </div>

          )
        }


        {/* ====================================================
            RESUMEN
        ==================================================== */}

        {
          graficoActivo ===
            "kda" &&
          resumen?.kda && (

            <div className="performance-chart-summary">

              <div>
                <span>PROMEDIO</span>
                <strong>
                  {resumen.kda.promedio.toFixed(2)}
                </strong>
              </div>

              <div>
                <span>MÍNIMO</span>
                <strong>
                  {resumen.kda.minimo.toFixed(2)}
                </strong>
              </div>

              <div>
                <span>MÁXIMO</span>
                <strong>
                  {resumen.kda.maximo.toFixed(2)}
                </strong>
              </div>

            </div>

          )
        }


        {
          graficoActivo ===
            "recursos" && (

            <div className="performance-chart-summary">

              <div>
                <span>CS/MIN PROM.</span>
                <strong>
                  {
                    resumen.cs_por_minuto.promedio.toFixed(
                      2
                    )
                  }
                </strong>
              </div>

              <div>
                <span>ORO/MIN PROM.</span>
                <strong>
                  {
                    resumen.oro_por_minuto.promedio.toFixed(
                      2
                    )
                  }
                </strong>
              </div>

              <div>
                <span>ORO/MIN MÁX.</span>
                <strong>
                  {
                    resumen.oro_por_minuto.maximo.toFixed(
                      2
                    )
                  }
                </strong>
              </div>

            </div>

          )
        }


        {
          graficoActivo ===
            "daño" &&
          resumen?.daño_por_minuto && (

            <div className="performance-chart-summary">

              <div>
                <span>PROMEDIO</span>
                <strong>
                  {
                    resumen.daño_por_minuto.promedio.toFixed(
                      2
                    )
                  }
                </strong>
              </div>

              <div>
                <span>MÍNIMO</span>
                <strong>
                  {
                    resumen.daño_por_minuto.minimo.toFixed(
                      2
                    )
                  }
                </strong>
              </div>

              <div>
                <span>MÁXIMO</span>
                <strong>
                  {
                    resumen.daño_por_minuto.maximo.toFixed(
                      2
                    )
                  }
                </strong>
              </div>

            </div>

          )
        }


        {
          graficoActivo ===
            "win_rate" &&
          ultimaPartida && (

            <div className="performance-chart-summary">

              <div>
                <span>WIN RATE FINAL</span>
                <strong>
                  {
                    ultimaPartida
                      .win_rate_acumulado
                      .toFixed(2)
                  }
                  %
                </strong>
              </div>

              <div>
                <span>PARTIDAS</span>
                <strong>
                  {graficos.cantidad_partidas}
                </strong>
              </div>

              <div>
                <span>ORDEN</span>
                <strong>
                  CRONOLÓGICO
                </strong>
              </div>

            </div>

          )
        }

      </div>

    </section>

  );

}


export default PerformanceCharts;