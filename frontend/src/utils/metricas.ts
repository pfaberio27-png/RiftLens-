// Datos de apoyo para las barras de comparación.

// Con menos partidas que esto se muestra "(pocas partidas)".
export const MINIMO_PARTIDAS_CONFIABLE = 5;


// Explicación corta de cada métrica (tooltip).
export const DESCRIPCIONES_METRICAS: Record<string, string> = {
  win_rate:
    "Porcentaje de partidas ganadas.",
  kda:
    "(Asesinatos + asistencias) ÷ muertes, promedio por partida.",
  cs_por_minuto:
    "Súbditos y monstruos eliminados por minuto.",
  oro_por_minuto:
    "Oro obtenido por minuto de partida.",
  daño_por_minuto:
    "Daño a campeones enemigos por minuto.",
  vision_score:
    "Puntuación de visión promedio por partida: wards colocados, wards eliminados y control de visión.",
  participacion_kills:
    "Porcentaje de los asesinatos de tu equipo en los que participaste con un asesinato o una asistencia.",
  porcentaje_daño_equipo:
    "Qué parte del daño a campeones de tu equipo hiciste tú.",
  muertes_por_10_min:
    "Veces que mueres cada 10 minutos de partida. Menos es mejor.",
  vision_por_minuto:
    "Puntuación de visión dividida entre los minutos de partida.",
  control_wards:
    "Wards de control que compras por partida.",
  cs_10_minutos:
    "Súbditos y monstruos eliminados antes del minuto 10.",
  diferencia_oro_rival:
    "Tu oro al final de la partida menos el de tu rival de la misma línea.",
};
