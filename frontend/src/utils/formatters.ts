import type {
  ComparacionMetrica,
} from "../types/analisis";


export const traducirTier = (
  tier: string | null
) => {

  if (!tier) {
    return "Sin rango";
  }

  const tiers: Record<string, string> = {
    IRON: "Hierro",
    BRONZE: "Bronce",
    SILVER: "Plata",
    GOLD: "Oro",
    PLATINUM: "Platino",
    EMERALD: "Esmeralda",
    DIAMOND: "Diamante",
    MASTER: "Maestro",
    GRANDMASTER: "Gran Maestro",
    CHALLENGER: "Retador",
  };

  return tiers[tier] ?? tier;
};


export const formatearRol = (
  rol: string | null
) => {

  if (!rol) {
    return "Sin rol";
  }

  const roles: Record<string, string> = {
    TOP: "Top",
    JUNGLE: "Jungla",
    MID: "Medio",
    ADC: "ADC",
    SUPPORT: "Soporte",
  };

  return roles[rol] ?? rol;
};


// Diferencia en % con 1 decimal y signo: "+4.2 %".
// null → "—".
export const formatearPorcentajeConSigno = (
  valor: number | null | undefined
) => {

  if (valor === null || valor === undefined) {
    return "—";
  }

  const redondeado =
    Math.round(valor * 10) / 10;

  if (redondeado === 0) {
    return "0.0 %";
  }

  return `${redondeado > 0 ? "+" : ""}${redondeado.toFixed(1)} %`;
};


// Métricas de oro y daño: enteros con separador de miles.
const METRICAS_ENTERAS = [
  "oro_por_minuto",
  "daño_por_minuto",
  "diferencia_oro_rival",
];

// Métricas con signo (pueden ser negativas).
const METRICAS_CON_SIGNO = [
  "diferencia_oro_rival",
];


// Valor de una métrica de comparación con su unidad.
// null → "—".
export const formatearValorMetrica = (
  clave: string,
  valor: number | null | undefined,
  unidad = ""
) => {

  if (valor === null || valor === undefined) {
    return "—";
  }

  const esPorcentaje =
    unidad === "%"
    || clave === "win_rate";

  const decimales =
    METRICAS_ENTERAS.includes(clave)
      ? 0
      : esPorcentaje
        ? 1
        : 2;

  // Se redondea antes para no mostrar "-0".
  const redondeado =
    Number(valor.toFixed(decimales));

  // en-US: separador de miles "," y decimal "." también
  // en números de 4 cifras.
  const texto =
    Math.abs(redondeado).toLocaleString(
      "en-US",
      {
        minimumFractionDigits: decimales,
        maximumFractionDigits: decimales,
      }
    );

  const signo =
    redondeado < 0
      ? "-"
      : METRICAS_CON_SIGNO.includes(clave)
        && redondeado > 0
        ? "+"
        : "";

  return `${signo}${texto}${esPorcentaje ? " %" : ""}`;
};


export const obtenerClaseEstado = (
  estado: ComparacionMetrica["estado"]
) => {

  switch (estado) {

    case "superior":
      return "metrica-superior";

    case "inferior":
      return "metrica-inferior";

    default:
      return "metrica-similar";
  }
};