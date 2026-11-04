export interface AnalisisRequest {

  riot_id: string;

  region: string;

}


// ============================================================
// DISTRIBUCIÓN DE ROLES
// ============================================================

export interface DistribucionRol {

  partidas: number;

  porcentaje: number;

}


export interface DistribucionRoles {

  TOP: DistribucionRol;

  JUNGLE: DistribucionRol;

  MID: DistribucionRol;

  ADC: DistribucionRol;

  SUPPORT: DistribucionRol;

}


// ============================================================
// RANGO
// ============================================================

export interface RangoJugador {

  clasificado: boolean;

  cola: string;

  tier: string | null;

  division: string | null;

  lp: number;

  victorias: number;

  derrotas: number;

}


// ============================================================
// JUGADOR
// ============================================================

export interface JugadorAnalizado {

  puuid: string;

  nombre: string;

  tag: string;

  riot_id: string | null;

  rango: RangoJugador | null;

}


// ============================================================
// MUESTRA
// ============================================================

export interface MuestraAnalisis {

  partidas_obtenidas: number;

  partidas_analizadas: number;

  rol_principal: string;

  distribucion_roles: DistribucionRoles;

}


// ============================================================
// REFERENCIA PROFESIONAL
// ============================================================

export interface MetricasReferencia {

  win_rate: number;

  kda: number;

  cs_por_minuto: number;

  oro_por_minuto: number;

  daño_por_minuto: number;

  vision_score: number;

}


export interface ReferenciaProfesional {

  fuente: string;

  dataset: string;

  temporada: number;

  tipo_referencia?: string;

  ligas?: string[];

  rol: string;

  partidas_referencia: number;

  metricas: MetricasReferencia;

}


// ============================================================
// ESTADÍSTICAS DEL JUGADOR
// ============================================================

export interface ResultadosJugador {

  victorias: number;

  derrotas: number;

  win_rate: number;

}


export interface CombateJugador {

  kills_promedio: number;

  muertes_promedio: number;

  asistencias_promedio: number;

  kda_promedio: number;

}


export interface FarmeoJugador {

  cs_promedio: number;

  cs_por_minuto_promedio: number;

}


export interface EconomiaJugador {

  oro_promedio: number;

  oro_por_minuto_promedio: number;

}


export interface DanoJugador {

  daño_promedio: number;

  daño_por_minuto_promedio: number;

}


export interface VisionJugador {

  vision_score_promedio: number;

}


export interface EstadisticasJugador {

  partidas_analizadas: number;

  resultados: ResultadosJugador;

  combate: CombateJugador;

  farmeo: FarmeoJugador;

  economia: EconomiaJugador;

  daño: DanoJugador;

  vision: VisionJugador;

}


// ============================================================
// CAMPEÓN INSIGNIA
// ============================================================

export interface CampeonInsignia {

  nombre: string | null;

  partidas: number;

  win_rate: number | null;

  // "mejor_win_rate": mayor win rate con al menos 5 partidas.
  // "mas_jugado": ningún campeón llega a 5 partidas.
  criterio: "mejor_win_rate" | "mas_jugado" | null;

  imagen_icono: string | null;

  imagen_splash: string | null;

  estadisticas: EstadisticasJugador | null;

  // 6 métricas del insignia vs referencia del rol.
  // null si no hay partidas del insignia.
  comparacion_profesional?: Comparacion | null;

  // Métricas sin referencia profesional: insignia vs los
  // promedios generales del jugador.
  comparacion_adicional?: ComparacionAdicional | null;

}


// ============================================================
// FORMA RECIENTE
// ============================================================

export type ResultadoReciente =
  | "V"
  | "D";


export interface FormaReciente {

  resultados: ResultadoReciente[];

  victorias: number;

  derrotas: number;

  cantidad: number;

}


// ============================================================
// CAMPEÓN DE PARTIDA
// ============================================================

export interface CampeonPartida {

  id?: number | null;

  nombre: string;

  nivel: number;

  imagen_icono: string | null;

  imagen_splash: string | null;

}


// ============================================================
// COMBATE DE PARTIDA
// ============================================================

export interface CombatePartida {

  kills: number;

  muertes: number;

  asistencias: number;

  kda: number;

}


// ============================================================
// FARMEO
// ============================================================

export interface FarmeoPartida {

  cs: number;

  cs_por_minuto: number;

}


// ============================================================
// ECONOMÍA
// ============================================================

export interface EconomiaPartida {

  oro: number;

  oro_por_minuto: number;

}


// ============================================================
// DAÑO
// ============================================================

export interface DanoPartida {

  daño_campeones: number;

  daño_por_minuto: number;

}


// ============================================================
// VISIÓN
// ============================================================

export interface VisionPartida {

  vision_score: number;

}


// ============================================================
// RESULTADO DEL RIVAL
// ============================================================

export interface ResultadoRival {

  victoria: boolean;

}


// ============================================================
// RIVAL DEL MISMO ROL
// ============================================================

export interface RivalRol {

  puuid: string | null;

  nombre: string | null;

  tag: string | null;

  team_id: number | null;

  rol: string | null;

  campeon: CampeonPartida;

  combate: CombatePartida;

  resultado: ResultadoRival;

}


// ============================================================
// PARTICIPANTE DEL DETALLE DE PARTIDA
// ============================================================

export interface CampeonParticipante {

  id: number | null;

  nombre: string | null;

  nivel: number | null;

}


export interface CombateParticipante {

  kills: number;

  muertes: number;

  asistencias: number;

  kda: number;

}


export interface RecursosParticipante {

  cs: number;

  oro: number;

}


export interface DanoParticipante {

  campeones: number;

}


export interface VisionParticipante {

  score: number;

  wards: number;

  // null si Riot no envía el dato.
  control_wards: number | null;

}


export interface ParticipantePartida {

  puuid: string | null;

  nombre: string | null;

  tag: string | null;

  team_id: number | null;

  victoria: boolean;

  posicion: string | null;

  campeon: CampeonParticipante;

  combate: CombateParticipante;

  recursos: RecursosParticipante;

  daño: DanoParticipante;

  vision: VisionParticipante;

  objetos: number[];

  es_jugador: boolean;

}


// ============================================================
// EQUIPOS DE UNA PARTIDA
// ============================================================

export interface EquiposPartida {

  aliados: ParticipantePartida[];

  rivales: ParticipantePartida[];

}


// ============================================================
// DETALLE DE PARTIDA (GET /api/partida/{match_id})
// ============================================================

export interface ObjetivosEquipo {

  kills: number;

  torres: number;

  dragones: number;

  barones: number;

  heraldos: number;

  // Solo si Riot envía el objetivo (larvas del Vacío).
  larvas?: number;

  oro: number;

}


export interface DetallePartida {

  match_id: string;

  puuid: string;

  region: string;

  origen: string;

  remake: boolean;

  resultado: {
    victoria: boolean;
  };

  duracion_segundos: number;

  // Timestamp en milisegundos (null si no se conoce).
  game_creation: number | null;

  // Versión del juego de la partida (p. ej. "16.21.712.4153").
  version_parche: string | null;

  equipos: EquiposPartida;

  // null si no se pudieron obtener (por ejemplo, error de Riot).
  objetivos: {
    aliados: ObjetivosEquipo;
    rivales: ObjetivosEquipo;
  } | null;

  resumen: string | null;

}


// ============================================================
// PARTIDAS RECIENTES
// ============================================================

export interface PartidaReciente {

  match_id: string | null;

  modo: string | null;

  queue_id: number | null;

  rol: string | null;

  duracion_segundos: number;

  duracion_minutos: number;

  victoria: boolean;

  campeon: CampeonPartida;

  combate: CombatePartida;

  farmeo: FarmeoPartida;

  economia: EconomiaPartida;

  daño: DanoPartida;

  vision: VisionPartida;

  rival_rol: RivalRol | null;

  // Los 10 participantes ya no vienen aquí: se piden con
  // obtenerDetallePartida() al abrir el detalle.

  // Remake (< 300 s o rendición temprana): excluido de los cálculos.
  remake?: boolean;

}


// ============================================================
// ROLES Y CAMPEONES (rendimiento_roles, sin remakes)
// ============================================================

export type RolJuego =
  | "TOP"
  | "JUNGLE"
  | "MID"
  | "ADC"
  | "SUPPORT";


// Resumen de una partida; el detalle se abre buscando
// match_id en partidas_recientes.
export interface PartidaResumen {

  match_id: string | null;

  victoria: boolean;

  kills: number;

  muertes: number;

  asistencias: number;

  kda: number;

  // Timestamp de Riot en milisegundos.
  fecha: number | null;

  duracion_minutos: number | null;

}


export interface CampeonRendimientoRol {

  campeon: {
    nombre: string;
    imagen_icono: string | null;
  };

  es_insignia: boolean;

  partidas: number;

  victorias: number;

  derrotas: number;

  win_rate: number;

  kda: number;

  kills_promedio: number;

  muertes_promedio: number;

  asistencias_promedio: number;

  cs_por_minuto: number;

  oro_por_minuto: number;

  daño_por_minuto: number;

  vision_score: number;

  participacion_kills: {
    valor: number | null;
    partidas_con_dato: number;
  };

  mejor_partida: PartidaResumen;

  // null si el campeón tiene una sola partida.
  peor_partida: PartidaResumen | null;

  // Hasta 5, la más reciente primero.
  ultimas_partidas: PartidaResumen[];

}


export interface RolRendimiento {

  rol: RolJuego;

  disponible: boolean;

  es_principal: boolean;

  partidas: number;

  // Sobre las partidas con rol (los 5 suman ~100 %).
  porcentaje_uso: number;

  victorias: number;

  derrotas: number;

  win_rate: number;

  kda: number;

  cs_por_minuto: number;

  daño_por_minuto: number;

  vision_score: number;

  // Insignia del rol primero, luego por partidas.
  campeones: CampeonRendimientoRol[];

}


export interface RendimientoRoles {

  rol_principal: string;

  roles: RolRendimiento[];

}


// ============================================================
// COMPARACIÓN PROFESIONAL
// ============================================================

export type EstadoMetrica =
  | "superior"
  | "inferior"
  | "similar";


export interface ComparacionMetrica {

  nombre: string;

  jugador: number;

  referencia: number;

  diferencia: number;

  diferencia_porcentual: number;

  porcentaje_referencia: number;

  estado: EstadoMetrica;

}


export interface Comparacion {

  win_rate: ComparacionMetrica;

  kda: ComparacionMetrica;

  cs_por_minuto: ComparacionMetrica;

  oro_por_minuto: ComparacionMetrica;

  daño_por_minuto: ComparacionMetrica;

  vision_score: ComparacionMetrica;

}


// ============================================================
// MÉTRICAS ADICIONALES (SIN REFERENCIA PROFESIONAL)
// ============================================================

// Promedio general del jugador en todas sus partidas válidas.
// valor = null si ninguna partida trae el dato.
export interface MetricaAdicional {

  nombre: string;

  valor: number | null;

  // "%" o "" (sin unidad)
  unidad: string;

  menor_es_mejor: boolean;

  partidas_con_dato: number;

}


export interface MetricasAdicionales {

  participacion_kills: MetricaAdicional;

  porcentaje_daño_equipo: MetricaAdicional;

  muertes_por_10_min: MetricaAdicional;

  vision_por_minuto: MetricaAdicional;

  control_wards: MetricaAdicional;

  cs_10_minutos: MetricaAdicional;

  diferencia_oro_rival: MetricaAdicional;

}


// estado ya considera menor_es_mejor: "superior" = mejor.
// diferencia, diferencia_porcentual y estado son null si falta
// alguno de los dos valores.
export interface ComparacionAdicionalMetrica {

  nombre: string;

  jugador: number | null;

  referencia: number | null;

  diferencia: number | null;

  diferencia_porcentual: number | null;

  estado: EstadoMetrica | null;

  unidad: string;

  menor_es_mejor: boolean;

  partidas_con_dato: number;

  partidas_con_dato_referencia: number;

}


export type ComparacionAdicional = Record<
  keyof MetricasAdicionales,
  ComparacionAdicionalMetrica
>;


// ============================================================
// SCORE
// ============================================================

export interface Score {

  valor: number;

  maximo: number;

  clasificacion: string;

}


// ============================================================
// FORTALEZAS / DEBILIDADES
// ============================================================

export interface EvaluacionMetrica {

  metrica: string;

  nombre: string;

  jugador: number;

  referencia: number;

  diferencia_porcentual: number;

}


// ============================================================
// RECOMENDACIONES
// ============================================================

export interface Recomendacion {

  // Identificador del catálogo (p. ej. "VIS-02").
  id?: string;

  // Métrica débil o "general" cuando no hay debilidades.
  metrica: string;

  nombre: string;

  // null en las recomendaciones generales.
  diferencia_porcentual: number | null;

  titulo?: string;

  recomendacion: string;

  prioridad?: PrioridadRecomendacion;

}

export type PrioridadRecomendacion =
  | "alta"
  | "media"
  | "baja";

// ============================================================
// ANÁLISIS POR CAMPEÓN
// ============================================================

export interface CampeonAnalisis {

  nombre: string;

  imagen_icono: string | null;

  imagen_splash: string | null;

}


export interface AnalisisCampeon {

  campeon: CampeonAnalisis;

  partidas: number;

  porcentaje_uso: number;

  victorias: number;

  derrotas: number;

  win_rate: number;

  kda: number;

  kills_promedio: number;

  muertes_promedio: number;

  asistencias_promedio: number;

  cs_por_minuto: number;

  oro_por_minuto: number;

  daño_por_minuto: number;

  vision_score: number;

}

// ============================================================
// ANÁLISIS POR POSICIÓN
// ============================================================

export interface AnalisisPosicion {

  rol: string;

  disponible: boolean;

  partidas: number;

  porcentaje: number;

  victorias: number;

  derrotas: number;

  win_rate: number;

  kda: number;

  kills_promedio: number;

  muertes_promedio: number;

  asistencias_promedio: number;

  cs_por_minuto: number;

  oro_por_minuto: number;

  daño_por_minuto: number;

  vision_score: number;

}


export interface AnalisisPosiciones {

  TOP: AnalisisPosicion;

  JUNGLE: AnalisisPosicion;

  MID: AnalisisPosicion;

  ADC: AnalisisPosicion;

  SUPPORT: AnalisisPosicion;

}

// ============================================================
// HU13 - GRÁFICOS DE RENDIMIENTO
// ============================================================

export interface PuntoGraficoRendimiento {
  numero: number;

  match_id: string | null;

  campeon: string;

  victoria: boolean;

  kda: number;

  cs_por_minuto: number;

  oro_por_minuto: number;

  daño_por_minuto: number;

  vision_score: number;

  win_rate_acumulado: number;
}


export interface ResumenMetricaGrafico {
  promedio: number;

  minimo: number;

  maximo: number;
}


export interface ResumenGraficosRendimiento {
  kda: ResumenMetricaGrafico;

  cs_por_minuto: ResumenMetricaGrafico;

  oro_por_minuto: ResumenMetricaGrafico;

  daño_por_minuto: ResumenMetricaGrafico;

  vision_score: ResumenMetricaGrafico;
}


export interface GraficosRendimiento {
  disponible: boolean;

  cantidad_partidas: number;

  orden?: string;

  partidas: PuntoGraficoRendimiento[];

  resumen: ResumenGraficosRendimiento;
}

// ============================================================
// ANÁLISIS COMPLETO
// ============================================================

export interface AnalisisCompleto {

  jugador: JugadorAnalizado;

  campeon_insignia: CampeonInsignia;

  muestra: MuestraAnalisis;

  forma_reciente: FormaReciente;

  partidas_recientes: PartidaReciente[];

  referencia_profesional: ReferenciaProfesional;

  estadisticas_jugador: EstadisticasJugador;

  analisis_posiciones: AnalisisPosiciones;

  // Sección "Roles y campeones".
  rendimiento_roles?: RendimientoRoles;

  analisis_campeones: AnalisisCampeon[];
  
  graficos_rendimiento: GraficosRendimiento;

  mineria_datos: MineriaDatosKMeans;

  comparacion: Comparacion;

  // Promedios generales de las métricas sin referencia pro.
  metricas_adicionales?: MetricasAdicionales;

  score: Score;

  fortalezas: EvaluacionMetrica[];

  debilidades: EvaluacionMetrica[];

  metricas_similares: EvaluacionMetrica[];

  recomendaciones: Recomendacion[];

  etiquetas: EtiquetaJugador[];

  resumen_jugador: string;

}

// ============================================================
// ETIQUETAS DE CUALIDADES
// ============================================================

export interface EtiquetaJugador {

  texto: string;

  tipo: "positiva" | "negativa";

  motivo: string;

}

// ============================================================
// MINERÍA DE DATOS - K-MEANS
// ============================================================

export interface MetricasClusterKMeans {

  kda: number;

  cs_por_minuto: number;

  oro_por_minuto: number;

  daño_por_minuto: number;

  vision_score: number;

}


export interface EvaluacionClusterKMeans {

  k: number;

  silhouette_score: number;

  inercia: number;

}


export interface ClusterKMeans {

  cluster: number;

  cantidad_partidas: number;

  porcentaje: number;

  metricas_promedio: MetricasClusterKMeans;

  // Interpretación (se calcula después del agrupamiento)
  nombre: string;

  descripcion: string;

  win_rate: number;

  campeones_top: CampeonGrupoKMeans[];

  es_mejor_estilo: boolean;

  // Se muestra como "Estilo con menos victorias"
  es_estilo_a_evitar: boolean;

}


export interface CampeonGrupoKMeans {

  nombre: string;

  cantidad: number;

}


// PCA a 2 componentes: solo para dibujar, no agrupa.
export interface PuntoPcaKMeans {

  x: number;

  y: number;

  cluster: number;

  victoria: boolean;

  campeon: string | null;

  match_id: string | null;

}


export interface PcaKMeans {

  varianza_explicada: number[];

  puntos: PuntoPcaKMeans[];

}


export interface AsignacionKMeans {

  indice_partida: number;

  match_id: string | null;

  campeon: string | null;

  cluster: number;

}


export interface MineriaDatosKMeans {

  disponible: boolean;

  motivo?: string;

  algoritmo: string;

  normalizacion?: string;

  criterio_seleccion_k?: string;

  partidas_utilizadas: number;

  variables: string[];

  numero_clusters: number;

  silhouette_score?: number | null;

  evaluacion_clusters: EvaluacionClusterKMeans[];

  clusters: ClusterKMeans[];

  asignaciones?: AsignacionKMeans[];

  // Mensaje amigable cuando disponible es false
  mensaje?: string;

  mejor_estilo?: number | null;

  estilo_a_evitar?: number | null;

  conclusion?: string | null;

  pca?: PcaKMeans;

}

// ============================================================
// RESPUESTA API
// ============================================================

export interface AnalisisResponse {

  mensaje: string;

  riot_id: string;

  region: string;

  analisis: AnalisisCompleto;

}