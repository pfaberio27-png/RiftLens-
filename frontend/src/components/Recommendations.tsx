import type {
  AnalisisResponse,
  Recomendacion,
} from "../types/analisis";


type Recomendaciones =
  AnalisisResponse["analisis"]["recomendaciones"];


interface RecommendationsProps {
  recomendaciones: Recomendaciones;
}


// Nombre corto de cada métrica para la etiqueta.
const ETIQUETAS_METRICAS: Record<string, string> = {
  win_rate: "Win rate",
  kda: "KDA",
  cs_por_minuto: "CS/min",
  oro_por_minuto: "Oro/min",
  daño_por_minuto: "Daño/min",
  vision_score: "Visión",
  general: "General",
};


// Texto de la etiqueta: "Visión −66 %" o "General".
function textoEtiqueta(
  recomendacion: Recomendacion
) {

  const nombre =
    ETIQUETAS_METRICAS[recomendacion.metrica]
    ?? recomendacion.nombre;

  const diferencia =
    recomendacion.diferencia_porcentual;

  if (
    recomendacion.metrica === "general"
    || diferencia === null
    || diferencia === undefined
  ) {
    return nombre;
  }

  const brecha = Math.round(
    Math.abs(diferencia)
  );

  return `${nombre} −${brecha} %`;
}


function Recommendations({
  recomendaciones,
}: RecommendationsProps) {

  return (

    <section className="section">


      <div className="section-head">

        <div>

          <h2>
            Recomendaciones
          </h2>

        </div>

        <p>
          Sugerencias elegidas según las métricas
          que se encuentran debajo de la referencia
          profesional 2026 de tu rol.
        </p>

      </div>


      {
        recomendaciones.length > 0
          ? (

            <>

              <p className="recomendaciones-leyenda">

                Prioridad:{" "}

                <span className="prioridad-alta">
                  alta
                </span>

                {" · "}

                <span className="prioridad-media">
                  media
                </span>

                {" · "}

                <span className="prioridad-baja">
                  baja
                </span>

              </p>


              <div className="recomendaciones-list">

                {
                  recomendaciones.map(
                    (
                      recomendacion,
                      index
                    ) => (

                      <article
                        className={
                          "recomendacion-card prioridad-"
                          + (
                            recomendacion.prioridad
                            ?? "baja"
                          )
                        }
                        key={
                          recomendacion.id
                            ?? index
                        }
                      >

                        <div className="recomendacion-numero">

                          {index + 1}

                        </div>


                        <div className="recomendacion-contenido">

                          <div className="recomendacion-encabezado">

                            <h4>

                              {
                                recomendacion.titulo
                                  ?? recomendacion.nombre
                              }

                            </h4>

                            <span className="recomendacion-etiqueta">

                              {
                                textoEtiqueta(
                                  recomendacion
                                )
                              }

                            </span>

                          </div>

                          <p>

                            {
                              recomendacion
                                .recomendacion
                            }

                          </p>

                        </div>


                      </article>

                    )
                  )
                }

              </div>

            </>

          )
          : (

            <p className="empty-text">

              No existen recomendaciones
              prioritarias.

            </p>

          )
      }


    </section>

  );
}


export default Recommendations;
