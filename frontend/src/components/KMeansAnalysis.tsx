import {
  type CSSProperties,
  useMemo,
  useState,
} from "react";

import {
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";

import type {
  ClusterKMeans,
  MineriaDatosKMeans,
  PartidaReciente,
  PuntoPcaKMeans,
} from "../types/analisis";

import MatchDetailModal
  from "./MatchDetailModal";


interface KMeansAnalysisProps {
  mineria: MineriaDatosKMeans;
  // Para los íconos de campeón y la ventana de detalle.
  partidasRecientes: PartidaReciente[];
  puuid: string;
  region: string;
}


// ============================================================
// FORMATOS
// ============================================================

// Color de cada grupo (variables --grupo-N de base.css)
const colorGrupo = (
  cluster: number
) =>
  `var(--grupo-${(cluster % 6) + 1})`;


const porcentaje = (
  valor: number
) =>
  `${Math.round(valor)} %`;


const textoPartidas = (
  cantidad: number
) =>
  `${cantidad} ${cantidad === 1 ? "partida" : "partidas"}`;


const NOMBRES_VARIABLES: Record<string, string> = {
  kda: "KDA",
  cs_por_minuto: "CS por minuto",
  oro_por_minuto: "Oro por minuto",
  daño_por_minuto: "Daño por minuto",
  vision_score: "Puntuación de visión",
};


// ============================================================
// PASOS ILUSTRADOS
// ============================================================

const PASOS = [
  {
    titulo: "Medimos 5 datos de cada partida",
    texto: "KDA, farmeo, oro, daño y visión.",
    icono: (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M4 20V10M10 20V4M16 20v-7M22 20H2" />
      </svg>
    ),
  },
  {
    titulo: "Agrupamos las partidas parecidas",
    texto: "Sin saber si ganaste o perdiste.",
    icono: (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="7" cy="8" r="2.5" />
        <circle cx="5" cy="15" r="2.5" />
        <circle cx="17" cy="7" r="2.5" />
        <circle cx="19" cy="14" r="2.5" />
        <circle cx="14" cy="18" r="2.5" />
      </svg>
    ),
  },
  {
    titulo: "Vemos con qué estilo ganas más",
    texto: "Calculamos tus victorias en cada grupo.",
    icono: (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M7 4h10v5a5 5 0 0 1-10 0V4ZM7 6H4a3 3 0 0 0 3 4M17 6h3a3 3 0 0 1-3 4M12 14v4M8 20h8" />
      </svg>
    ),
  },
];


// ============================================================
// GRÁFICO: PUNTO Y TOOLTIP
// ============================================================

interface PuntoProps {
  cx?: number;
  cy?: number;
  payload?: PuntoPcaKMeans;
}


interface TooltipEstiloProps {
  active?: boolean;
  payload?: Array<{
    payload: PuntoPcaKMeans;
  }>;
  nombres: Map<number, string>;
}


function TooltipEstilo({
  active,
  payload,
  nombres,
}: TooltipEstiloProps) {

  if (!active || !payload || payload.length === 0) {
    return null;
  }

  const punto =
    payload[0].payload;

  return (

    <div className="estilos-tooltip">

      <strong>
        {punto.campeon ?? "Campeón desconocido"}
      </strong>

      <span
        className={
          punto.victoria
            ? "victoria"
            : "derrota"
        }
      >
        {punto.victoria ? "Victoria" : "Derrota"}
      </span>

      <span className="estilos-tooltip-grupo">
        <i
          style={{
            background: colorGrupo(punto.cluster),
          }}
        />
        {nombres.get(punto.cluster)}
      </span>

    </div>

  );
}


// ============================================================
// TARJETA DE ESTILO
// ============================================================

interface TarjetaEstiloProps {
  cluster: ClusterKMeans;
  resaltado: boolean;
  atenuado: boolean;
  iconos: Map<string, string | null>;
  onAlternar: () => void;
}


function TarjetaEstilo({
  cluster,
  resaltado,
  atenuado,
  iconos,
  onAlternar,
}: TarjetaEstiloProps) {

  const estilo = {
    "--color-grupo": colorGrupo(cluster.cluster),
  } as CSSProperties;

  return (

    <button
      type="button"
      className={
        [
          "kmeans-cluster-card",
          "estilo-card",
          resaltado ? "resaltado" : "",
          atenuado ? "atenuado" : "",
        ]
          .filter(Boolean)
          .join(" ")
      }
      style={estilo}
      aria-pressed={resaltado}
      onClick={onAlternar}
    >

      <span className="estilo-card-head">

        <i
          className="estilo-color"
          aria-hidden="true"
        />

        {
          cluster.es_mejor_estilo && (
            <em className="estilo-etiqueta mejor">
              Tu mejor estilo
            </em>
          )
        }

        {
          cluster.es_estilo_a_evitar && (
            <em className="estilo-etiqueta menos">
              Estilo con menos victorias
            </em>
          )
        }

      </span>


      <strong className="estilo-nombre">
        {cluster.nombre}
      </strong>

      <span className="estilo-descripcion">
        {cluster.descripcion}
      </span>


      <span className="estilo-datos">

        <span>
          <small>Victorias</small>
          <b
            className={
              cluster.win_rate >= 50
                ? "alto"
                : "bajo"
            }
          >
            {porcentaje(cluster.win_rate)}
          </b>
        </span>

        <span>
          <small>Partidas</small>
          <b>{cluster.cantidad_partidas}</b>
        </span>

        <span>
          <small>Del total</small>
          <b>{porcentaje(cluster.porcentaje)}</b>
        </span>

      </span>


      <span className="estilo-campeones">

        {
          cluster.campeones_top.map(
            (campeon) => {

              const icono =
                iconos.get(campeon.nombre);

              const titulo =
                `${campeon.nombre}: ${textoPartidas(campeon.cantidad)}`;

              return (

                <span
                  key={campeon.nombre}
                  className="estilo-campeon"
                  title={titulo}
                >

                  {
                    icono
                      ? (
                        <img
                          src={icono}
                          alt={campeon.nombre}
                        />
                      )
                      : (
                        <span
                          className="estilo-campeon-sin-icono"
                          aria-label={campeon.nombre}
                        >
                          {campeon.nombre.slice(0, 2)}
                        </span>
                      )
                  }

                  <small>×{campeon.cantidad}</small>

                </span>

              );
            }
          )
        }

      </span>


      <span className="estilo-accion">
        {
          resaltado
            ? "Quitar resaltado"
            : "Ver en el gráfico"
        }
      </span>

    </button>

  );
}


// ============================================================
// SECCIÓN
// ============================================================

function KMeansAnalysis({
  mineria,
  partidasRecientes,
  puuid,
  region,
}: KMeansAnalysisProps) {

  const [
    grupoResaltado,
    setGrupoResaltado,
  ] = useState<number | null>(null);

  const [
    partidaAbierta,
    setPartidaAbierta,
  ] = useState<PartidaReciente | null>(null);


  // match_id → partida completa (ventana de detalle) y
  // nombre de campeón → ícono.
  const {
    partidasPorId,
    iconos,
  } = useMemo(
    () => {

      const mapaPartidas =
        new Map<string, PartidaReciente>();

      const mapaIconos =
        new Map<string, string | null>();

      for (const partida of partidasRecientes) {

        if (partida.match_id && !partida.remake) {
          mapaPartidas.set(partida.match_id, partida);
        }

        if (
          partida.campeon.imagen_icono
          && !mapaIconos.get(partida.campeon.nombre)
        ) {
          mapaIconos.set(
            partida.campeon.nombre,
            partida.campeon.imagen_icono
          );
        }
      }

      return {
        partidasPorId: mapaPartidas,
        iconos: mapaIconos,
      };
    },
    [partidasRecientes]
  );


  const nombresGrupo = useMemo(
    () =>
      new Map(
        mineria.clusters.map(
          (cluster) => [cluster.cluster, cluster.nombre]
        )
      ),
    [mineria.clusters]
  );


  // El grupo resaltado se dibuja al final (encima del resto).
  const puntos = useMemo(
    () => {

      const lista =
        mineria.pca?.puntos ?? [];

      if (grupoResaltado === null) {
        return lista;
      }

      return [
        ...lista.filter(
          (punto) => punto.cluster !== grupoResaltado
        ),
        ...lista.filter(
          (punto) => punto.cluster === grupoResaltado
        ),
      ];
    },
    [mineria.pca, grupoResaltado]
  );


  const alternarGrupo = (
    cluster: number
  ) => {

    setGrupoResaltado(
      grupoResaltado === cluster
        ? null
        : cluster
    );
  };


  const abrirPartida = (
    matchId: string | null
  ) => {

    if (!matchId) {
      return;
    }

    const partida =
      partidasPorId.get(matchId);

    if (partida) {
      setPartidaAbierta(partida);
    }
  };


  // Victoria = punto relleno; derrota = punto vacío.
  const renderizarPunto = (
    props: PuntoProps
  ) => {

    const {
      cx,
      cy,
      payload,
    } = props;

    if (
      cx === undefined
      || cy === undefined
      || !payload
    ) {
      return <g />;
    }

    const color =
      colorGrupo(payload.cluster);

    const atenuado =
      grupoResaltado !== null
      && payload.cluster !== grupoResaltado;

    const clicable =
      payload.match_id !== null
      && partidasPorId.has(payload.match_id);

    return (

      <circle
        cx={cx}
        cy={cy}
        r={grupoResaltado === payload.cluster ? 6.5 : 5.5}
        className={
          clicable
            ? "estilos-punto clicable"
            : "estilos-punto"
        }
        style={{
          fill: payload.victoria ? color : "var(--void)",
          stroke: color,
          strokeWidth: 2,
          opacity: atenuado ? 0.15 : 0.95,
        }}
        onClick={() =>
          abrirPartida(payload.match_id)
        }
      />

    );
  };


  // ============================================================
  // SIN DATOS
  // ============================================================

  const cabecera = (

    <div className="section-head">

      <div>

        <span className="section-eyebrow">
          ESTILOS DE JUEGO
        </span>

        <h2>
          Tus estilos de juego
        </h2>

      </div>

      <p>
        Detectados automáticamente comparando tus
        partidas entre sí.
      </p>

    </div>

  );


  if (!mineria.disponible) {

    return (

      <section className="section kmeans-section">

        {cabecera}

        <div className="kmeans-empty">

          <strong>
            Aún no podemos detectar tus estilos
          </strong>

          <p>
            {
              mineria.mensaje
              ?? mineria.motivo
              ?? "No hay suficientes partidas para detectar tus estilos de juego."
            }
          </p>

        </div>

      </section>

    );

  }


  const varianza =
    mineria.pca?.varianza_explicada ?? [];


  // ============================================================
  // RENDER
  // ============================================================

  return (

    <section className="section kmeans-section">

      {cabecera}


      {/* ========================================================
          CÓMO FUNCIONA (3 PASOS)
      ======================================================== */}

      <ol className="estilos-pasos">

        {
          PASOS.map(
            (paso, indice) => (

              <li key={paso.titulo}>

                <span className="estilos-paso-icono">
                  {paso.icono}
                </span>

                <span className="estilos-paso-numero">
                  {indice + 1}
                </span>

                <div>
                  <strong>{paso.titulo}</strong>
                  <p>{paso.texto}</p>
                </div>

              </li>

            )
          )
        }

      </ol>


      {/* ========================================================
          CONCLUSIÓN
      ======================================================== */}

      {
        mineria.conclusion && (

          <p className="estilos-conclusion">
            {mineria.conclusion}
          </p>

        )
      }


      {/* ========================================================
          TARJETAS DE ESTILO
      ======================================================== */}

      <div className="kmeans-clusters">

        {
          mineria.clusters.map(
            (cluster) => (

              <TarjetaEstilo
                key={cluster.cluster}
                cluster={cluster}
                resaltado={grupoResaltado === cluster.cluster}
                atenuado={
                  grupoResaltado !== null
                  && grupoResaltado !== cluster.cluster
                }
                iconos={iconos}
                onAlternar={() =>
                  alternarGrupo(cluster.cluster)
                }
              />

            )
          )
        }

      </div>


      {/* ========================================================
          GRÁFICO DE PUNTOS
      ======================================================== */}

      {
        puntos.length > 0 && (

          <div className="estilos-grafico">

            <div className="estilos-grafico-head">

              <div>
                <h3>Mapa de tus partidas</h3>
                <p>
                  Cada punto es una partida; las que están cerca
                  se parecen entre sí. Toca un punto para ver
                  su detalle.
                </p>
              </div>

              <div
                className="estilos-leyenda"
                aria-label="Leyenda"
              >
                <span>
                  <i className="relleno" />
                  Victoria
                </span>
                <span>
                  <i className="vacio" />
                  Derrota
                </span>
              </div>

            </div>


            <div className="estilos-grafico-contenedor">

              <ResponsiveContainer
                width="100%"
                height="100%"
              >

                <ScatterChart
                  margin={{
                    top: 12,
                    right: 12,
                    bottom: 12,
                    left: 12,
                  }}
                >

                  {/* Ejes ocultos: las coordenadas no tienen
                      un significado directo para el jugador */}
                  <XAxis
                    type="number"
                    dataKey="x"
                    hide
                    domain={["dataMin - 0.5", "dataMax + 0.5"]}
                  />

                  <YAxis
                    type="number"
                    dataKey="y"
                    hide
                    domain={["dataMin - 0.5", "dataMax + 0.5"]}
                  />

                  <ZAxis range={[60, 60]} />

                  <Tooltip
                    cursor={false}
                    content={
                      <TooltipEstilo
                        nombres={nombresGrupo}
                      />
                    }
                  />

                  <Scatter
                    data={puntos}
                    shape={renderizarPunto}
                    isAnimationActive={false}
                  />

                </ScatterChart>

              </ResponsiveContainer>

            </div>


            <div className="estilos-leyenda-grupos">

              {
                mineria.clusters.map(
                  (cluster) => (

                    <span key={cluster.cluster}>
                      <i
                        style={{
                          background: colorGrupo(cluster.cluster),
                        }}
                      />
                      {cluster.nombre}
                    </span>

                  )
                )
              }

            </div>

          </div>

        )
      }


      {/* ========================================================
          DETALLE TÉCNICO (cerrado por defecto)
      ======================================================== */}

      <details className="estilos-tecnico">

        <summary>
          Detalle técnico
        </summary>

        <div className="estilos-tecnico-cuerpo">

          <p>
            Los grupos se obtienen con el algoritmo{" "}
            <strong>{mineria.algoritmo}</strong> sobre{" "}
            {textoPartidas(mineria.partidas_utilizadas)} del rol
            principal. Las variables se normalizan con{" "}
            <strong>{mineria.normalizacion ?? "StandardScaler"}</strong>{" "}
            y el número de grupos (k, de 2 a 6) se elige con el{" "}
            <strong>coeficiente de silueta</strong>. El resultado de
            la partida no interviene en el agrupamiento.
          </p>

          <dl className="estilos-tecnico-datos">

            <div>
              <dt>Variables</dt>
              <dd>
                {
                  mineria.variables
                    .map(
                      (variable) =>
                        NOMBRES_VARIABLES[variable] ?? variable
                    )
                    .join(", ")
                }
              </dd>
            </div>

            <div>
              <dt>k elegido</dt>
              <dd>{mineria.numero_clusters}</dd>
            </div>

            <div>
              <dt>Coeficiente de silueta</dt>
              <dd>
                {
                  mineria.silhouette_score !== undefined
                  && mineria.silhouette_score !== null
                    ? mineria.silhouette_score.toFixed(4)
                    : "—"
                }
              </dd>
            </div>

            {
              varianza.length === 2 && (
                <div>
                  <dt>Varianza explicada (PCA)</dt>
                  <dd>
                    {`Eje 1: ${(varianza[0] * 100).toFixed(1)} % · `}
                    {`Eje 2: ${(varianza[1] * 100).toFixed(1)} %`}
                  </dd>
                </div>
              )
            }

          </dl>


          {
            mineria.evaluacion_clusters.length > 0 && (

              <div className="estilos-tabla-envoltura">

                <table className="estilos-tabla">

                  <caption>
                    Evaluación de cada k
                  </caption>

                  <thead>
                    <tr>
                      <th scope="col">k</th>
                      <th scope="col">Silueta</th>
                      <th scope="col">Inercia</th>
                    </tr>
                  </thead>

                  <tbody>
                    {
                      mineria.evaluacion_clusters.map(
                        (evaluacion) => (

                          <tr
                            key={evaluacion.k}
                            className={
                              evaluacion.k === mineria.numero_clusters
                                ? "seleccionado"
                                : undefined
                            }
                          >
                            <td>{evaluacion.k}</td>
                            <td>{evaluacion.silhouette_score.toFixed(4)}</td>
                            <td>{evaluacion.inercia.toFixed(2)}</td>
                          </tr>

                        )
                      )
                    }
                  </tbody>

                </table>

              </div>

            )
          }

          <p className="estilos-tecnico-nota">
            El mapa de puntos usa PCA (2 componentes) sobre los
            mismos datos normalizados, solo para dibujar; no
            interviene en la formación de los grupos.
          </p>

        </div>

      </details>


      {/* ========================================================
          VENTANA DE DETALLE (la que ya existe)
      ======================================================== */}

      {
        partidaAbierta && (

          <MatchDetailModal
            partida={partidaAbierta}
            puuid={puuid}
            region={region}
            onCerrar={() =>
              setPartidaAbierta(null)
            }
          />

        )
      }

    </section>

  );

}


export default KMeansAnalysis;
