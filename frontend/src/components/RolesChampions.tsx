import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import type {
  CampeonRendimientoRol,
  PartidaReciente,
  PartidaResumen,
  RendimientoRoles,
  RolJuego,
} from "../types/analisis";

import MatchDetailModal
  from "./MatchDetailModal";

import {
  formatearRol,
  formatearValorMetrica,
} from "../utils/formatters";


interface RolesChampionsProps {
  rendimiento: RendimientoRoles;
  // Para abrir la ventana de detalle buscando por match_id.
  partidasRecientes: PartidaReciente[];
  puuid: string;
  region: string;
}


// ============================================================
// FORMATOS
// ============================================================

// Timestamp de Riot (ms) → "12 oct."
const formatearFecha = (
  fecha: number | null
) => {

  if (!fecha) {
    return "";
  }

  return new Date(fecha).toLocaleDateString(
    "es-PE",
    {
      day: "2-digit",
      month: "short",
    }
  );
};


const claseWinRate = (
  winRate: number
) =>
  winRate >= 50
    ? "rc-wr-alto"
    : "rc-wr-bajo";


const textoPartidas = (
  cantidad: number
) =>
  `${cantidad} ${cantidad === 1 ? "partida" : "partidas"}`;


// ============================================================
// TARJETA DE PARTIDA (abre la ventana de detalle)
// ============================================================

interface TarjetaPartidaProps {
  partida: PartidaResumen;
  titulo?: string;
  campeon: string;
  onAbrir: (matchId: string | null) => void;
  puedeAbrir: boolean;
}


function TarjetaPartida({
  partida,
  titulo,
  campeon,
  onAbrir,
  puedeAbrir,
}: TarjetaPartidaProps) {

  const resultado =
    partida.victoria
      ? "Victoria"
      : "Derrota";

  return (

    <button
      type="button"
      className={
        "rc-partida "
        + (
          partida.victoria
            ? "victoria"
            : "derrota"
        )
      }
      disabled={!puedeAbrir}
      onClick={() =>
        onAbrir(partida.match_id)
      }
      aria-label={
        `${titulo ? `${titulo}: ` : ""}`
        + `${resultado} con ${campeon}, `
        + `${partida.kills}/${partida.muertes}/${partida.asistencias}, `
        + `KDA ${partida.kda.toFixed(2)}. Ver detalle`
      }
    >

      {
        titulo && (
          <span className="rc-partida-titulo">
            {titulo}
          </span>
        )
      }

      <span className="rc-partida-resultado">
        {resultado}
      </span>

      <strong className="rc-partida-kda">
        {partida.kills}
        {" / "}
        <span className="rc-muertes">
          {partida.muertes}
        </span>
        {" / "}
        {partida.asistencias}
      </strong>

      <span className="rc-partida-meta">
        {`KDA ${partida.kda.toFixed(2)}`}
        {
          partida.fecha
            ? ` · ${formatearFecha(partida.fecha)}`
            : ""
        }
      </span>

    </button>

  );
}


// ============================================================
// PANEL DEL CAMPEÓN
// ============================================================

interface PanelCampeonProps {
  campeon: CampeonRendimientoRol;
  id: string;
  onAbrirPartida: (matchId: string | null) => void;
  puedeAbrir: (matchId: string | null) => boolean;
}


function PanelCampeon({
  campeon,
  id,
  onAbrirPartida,
  puedeAbrir,
}: PanelCampeonProps) {

  const nombre =
    campeon.campeon.nombre;

  const participacion =
    campeon.participacion_kills.valor;

  const estadisticas = [
    {
      etiqueta: "Win rate",
      valor: formatearValorMetrica(
        "win_rate",
        campeon.win_rate
      ),
      clase: claseWinRate(campeon.win_rate),
    },
    {
      etiqueta: "KDA",
      valor: formatearValorMetrica(
        "kda",
        campeon.kda
      ),
    },
    {
      etiqueta: "K / M / A promedio",
      valor:
        `${campeon.kills_promedio.toFixed(1)} / `
        + `${campeon.muertes_promedio.toFixed(1)} / `
        + `${campeon.asistencias_promedio.toFixed(1)}`,
    },
    {
      etiqueta: "CS/min",
      valor: formatearValorMetrica(
        "cs_por_minuto",
        campeon.cs_por_minuto
      ),
    },
    {
      etiqueta: "Oro/min",
      valor: formatearValorMetrica(
        "oro_por_minuto",
        campeon.oro_por_minuto
      ),
    },
    {
      etiqueta: "Daño/min",
      valor: formatearValorMetrica(
        "daño_por_minuto",
        campeon.daño_por_minuto
      ),
    },
    {
      etiqueta: "Visión",
      valor: formatearValorMetrica(
        "vision_score",
        campeon.vision_score
      ),
    },
    {
      etiqueta: "Participación en asesinatos",
      valor: formatearValorMetrica(
        "participacion_kills",
        participacion,
        "%"
      ),
      clase:
        participacion === null
          ? "rc-sin-dato"
          : undefined,
    },
  ];

  return (

    <div
      id={id}
      className="rc-panel"
      role="region"
      aria-label={`Rendimiento con ${nombre}`}
    >

      <div className="rc-panel-head">

        {
          campeon.campeon.imagen_icono && (
            <img
              className="rc-panel-icono"
              src={campeon.campeon.imagen_icono}
              alt=""
            />
          )
        }

        <div>

          <h3>{nombre}</h3>

          <p>
            {textoPartidas(campeon.partidas)}
            {" · "}
            <span className="rc-wr-alto">
              {campeon.victorias} V
            </span>
            {" / "}
            <span className="rc-wr-bajo">
              {campeon.derrotas} D
            </span>
          </p>

        </div>

      </div>


      <dl className="rc-panel-stats">

        {
          estadisticas.map(
            (estadistica) => (

              <div key={estadistica.etiqueta}>
                <dt>{estadistica.etiqueta}</dt>
                <dd className={estadistica.clase}>
                  {estadistica.valor}
                </dd>
              </div>

            )
          )
        }

      </dl>


      <h4 className="rc-subtitulo">
        Mejor y peor partida
      </h4>

      <div className="rc-destacadas">

        {
          campeon.peor_partida
            ? (
              <>
                <TarjetaPartida
                  partida={campeon.mejor_partida}
                  titulo="Mejor partida"
                  campeon={nombre}
                  onAbrir={onAbrirPartida}
                  puedeAbrir={
                    puedeAbrir(
                      campeon.mejor_partida.match_id
                    )
                  }
                />

                <TarjetaPartida
                  partida={campeon.peor_partida}
                  titulo="Peor partida"
                  campeon={nombre}
                  onAbrir={onAbrirPartida}
                  puedeAbrir={
                    puedeAbrir(
                      campeon.peor_partida.match_id
                    )
                  }
                />
              </>
            )
            : (
              <TarjetaPartida
                partida={campeon.mejor_partida}
                titulo="Única partida"
                campeon={nombre}
                onAbrir={onAbrirPartida}
                puedeAbrir={
                  puedeAbrir(
                    campeon.mejor_partida.match_id
                  )
                }
              />
            )
        }

      </div>


      <h4 className="rc-subtitulo">
        Últimas partidas
      </h4>

      <div className="rc-ultimas">

        {
          campeon.ultimas_partidas.map(
            (partida, indice) => (

              <TarjetaPartida
                key={partida.match_id ?? indice}
                partida={partida}
                campeon={nombre}
                onAbrir={onAbrirPartida}
                puedeAbrir={
                  puedeAbrir(partida.match_id)
                }
              />

            )
          )
        }

      </div>

    </div>

  );
}


// ============================================================
// SECCIÓN
// ============================================================

function RolesChampions({
  rendimiento,
  partidasRecientes,
  puuid,
  region,
}: RolesChampionsProps) {

  const roles =
    rendimiento.roles;

  // Por defecto el rol principal (o el primero con partidas).
  const rolInicial: RolJuego | null =
    roles.find(
      (rol) => rol.es_principal && rol.disponible
    )?.rol
    ?? roles.find(
      (rol) => rol.disponible
    )?.rol
    ?? null;

  const [
    rolSeleccionado,
    setRolSeleccionado,
  ] = useState<RolJuego | null>(rolInicial);

  const [
    campeonSeleccionado,
    setCampeonSeleccionado,
  ] = useState<string | null>(null);

  const [
    partidaAbierta,
    setPartidaAbierta,
  ] = useState<PartidaReciente | null>(null);

  const panelRef =
    useRef<HTMLDivElement>(null);


  // match_id → partida completa (para la ventana de detalle).
  const partidasPorId = useMemo(
    () => {

      const mapa =
        new Map<string, PartidaReciente>();

      for (const partida of partidasRecientes) {

        if (partida.match_id && !partida.remake) {
          mapa.set(partida.match_id, partida);
        }
      }

      return mapa;
    },
    [partidasRecientes]
  );


  const datosRol =
    roles.find(
      (rol) => rol.rol === rolSeleccionado
    ) ?? null;

  const datosCampeon =
    datosRol?.campeones.find(
      (campeon) =>
        campeon.campeon.nombre === campeonSeleccionado
    ) ?? null;


  // Lleva el panel a la vista al desplegarlo (útil en celular).
  useEffect(() => {

    if (!campeonSeleccionado || !panelRef.current) {
      return;
    }

    const reducirMovimiento =
      window.matchMedia(
        "(prefers-reduced-motion: reduce)"
      ).matches;

    panelRef.current.scrollIntoView({
      behavior:
        reducirMovimiento
          ? "auto"
          : "smooth",
      block: "nearest",
    });

  }, [campeonSeleccionado]);


  const seleccionarRol = (
    rol: RolJuego
  ) => {

    setRolSeleccionado(rol);

    // Al cambiar de rol se cierra el panel del campeón.
    setCampeonSeleccionado(null);
  };


  const alternarCampeon = (
    nombre: string
  ) => {

    setCampeonSeleccionado(
      campeonSeleccionado === nombre
        ? null
        : nombre
    );
  };


  const puedeAbrir = (
    matchId: string | null
  ) =>
    matchId !== null
    && partidasPorId.has(matchId);


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


  return (

    <section className="section rc-section">


      <div className="section-head">

        <div>
          <h2>
            Roles y campeones
          </h2>
        </div>

        <p>
          Elige un rol para ver los campeones que jugaste en él y
          toca un campeón para ver su rendimiento.
        </p>

      </div>


      {/* ================================================
          TARJETAS DE ROL
      ================================================ */}

      <div
        className="rc-roles"
        role="group"
        aria-label="Roles"
      >

        {
          roles.map(
            (rol) => {

              const seleccionado =
                rol.rol === rolSeleccionado;

              return (

                <button
                  key={rol.rol}
                  type="button"
                  className={
                    [
                      "rc-rol",
                      seleccionado
                        ? "seleccionado"
                        : "",
                      rol.disponible
                        ? ""
                        : "sin-partidas",
                    ]
                      .filter(Boolean)
                      .join(" ")
                  }
                  disabled={!rol.disponible}
                  aria-pressed={seleccionado}
                  onClick={() =>
                    seleccionarRol(rol.rol)
                  }
                >

                  <span className="rc-rol-head">

                    <strong>
                      {formatearRol(rol.rol)}
                    </strong>

                    {
                      rol.es_principal && (
                        <em className="rc-etiqueta">
                          Principal
                        </em>
                      )
                    }

                  </span>


                  <span className="rc-rol-uso">

                    <span>
                      {textoPartidas(rol.partidas)}
                    </span>

                    <span>
                      {formatearValorMetrica(
                        "porcentaje_uso",
                        rol.porcentaje_uso,
                        "%"
                      )}
                    </span>

                  </span>

                  <span
                    className="rc-barra"
                    aria-hidden="true"
                  >
                    <span
                      className="rc-barra-relleno"
                      style={{
                        width: `${Math.min(rol.porcentaje_uso, 100)}%`,
                      }}
                    />
                  </span>


                  {
                    rol.disponible
                      ? (
                        <span className="rc-rol-stats">

                          <span>
                            <small>Win rate</small>
                            <b className={claseWinRate(rol.win_rate)}>
                              {formatearValorMetrica(
                                "win_rate",
                                rol.win_rate
                              )}
                            </b>
                          </span>

                          <span>
                            <small>KDA</small>
                            <b>
                              {formatearValorMetrica(
                                "kda",
                                rol.kda
                              )}
                            </b>
                          </span>

                          <span>
                            <small>CS/min</small>
                            <b>
                              {formatearValorMetrica(
                                "cs_por_minuto",
                                rol.cs_por_minuto
                              )}
                            </b>
                          </span>

                          <span>
                            <small>Daño/min</small>
                            <b>
                              {formatearValorMetrica(
                                "daño_por_minuto",
                                rol.daño_por_minuto
                              )}
                            </b>
                          </span>

                          <span>
                            <small>Visión</small>
                            <b>
                              {formatearValorMetrica(
                                "vision_score",
                                rol.vision_score
                              )}
                            </b>
                          </span>

                        </span>
                      )
                      : (
                        <span className="rc-rol-vacio">
                          Sin partidas
                        </span>
                      )
                  }

                </button>

              );
            }
          )
        }

      </div>


      {/* ================================================
          CAMPEONES DEL ROL
      ================================================ */}

      {
        datosRol && datosRol.disponible && (

          <div className="rc-campeones-bloque">

            <h3 className="rc-bloque-titulo">
              {`Campeones en ${formatearRol(datosRol.rol)}`}
            </h3>

            <ul className="rc-campeones">

              {
                datosRol.campeones.map(
                  (campeon) => {

                    const nombre =
                      campeon.campeon.nombre;

                    const abierto =
                      nombre === campeonSeleccionado;

                    return (

                      <li key={nombre}>

                        <button
                          type="button"
                          className={
                            "rc-campeon"
                            + (abierto ? " abierto" : "")
                          }
                          aria-expanded={abierto}
                          aria-controls={
                            abierto
                              ? "rc-panel-campeon"
                              : undefined
                          }
                          onClick={() =>
                            alternarCampeon(nombre)
                          }
                        >

                          {
                            campeon.campeon.imagen_icono
                              ? (
                                <img
                                  className="rc-campeon-icono"
                                  src={campeon.campeon.imagen_icono}
                                  alt=""
                                />
                              )
                              : (
                                <span className="rc-campeon-icono" />
                              )
                          }

                          <span className="rc-campeon-nombre">

                            {nombre}

                            {
                              campeon.es_insignia && (
                                <em className="rc-etiqueta">
                                  Insignia
                                </em>
                              )
                            }

                          </span>

                          <span className="rc-campeon-datos">

                            <span className="rc-campeon-dato">
                              <small>Partidas</small>
                              <b>{campeon.partidas}</b>
                            </span>

                            <span className="rc-campeon-dato">
                              <small>Win rate</small>
                              <b className={claseWinRate(campeon.win_rate)}>
                                {formatearValorMetrica(
                                  "win_rate",
                                  campeon.win_rate
                                )}
                              </b>
                            </span>

                            <span className="rc-campeon-dato">
                              <small>KDA</small>
                              <b>
                                {formatearValorMetrica(
                                  "kda",
                                  campeon.kda
                                )}
                              </b>
                            </span>

                          </span>

                          <span
                            className="rc-campeon-flecha"
                            aria-hidden="true"
                          >
                            ▾
                          </span>

                        </button>

                      </li>

                    );
                  }
                )
              }

            </ul>


            {
              datosCampeon && (

                <div ref={panelRef}>

                  <PanelCampeon
                    key={datosCampeon.campeon.nombre}
                    id="rc-panel-campeon"
                    campeon={datosCampeon}
                    onAbrirPartida={abrirPartida}
                    puedeAbrir={puedeAbrir}
                  />

                </div>

              )
            }

          </div>

        )
      }


      {/* ================================================
          VENTANA DE DETALLE (la que ya existe)
      ================================================ */}

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


export default RolesChampions;
