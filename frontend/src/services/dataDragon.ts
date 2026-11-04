// ============================================================
// DATA DRAGON (íconos de campeones e ítems)
// ============================================================
//
// La versión actual se consulta una sola vez en
// versions.json y se guarda en memoria. Si la consulta falla,
// se usa la versión de la partida o la última conocida.

const URL_DATA_DRAGON =
  "https://ddragon.leagueoflegends.com";

const URL_VERSIONES =
  `${URL_DATA_DRAGON}/api/versions.json`;

// Última versión obtenida con éxito (respaldo entre visitas)
const CLAVE_ULTIMA_VERSION =
  "riftlens.ddragon.version";


let versionEnMemoria: string | null = null;

let peticionVersion: Promise<string | null> | null = null;


export function versionDataDragonEnMemoria(): string | null {
  return versionEnMemoria;
}


export function leerUltimaVersionConocida(): string | null {

  try {
    return localStorage.getItem(
      CLAVE_ULTIMA_VERSION
    );
  } catch {
    return null;
  }

}


/**
 * "16.21.712.4153" (gameVersion de Riot) → "16.21.1"
 * (formato de Data Dragon). Devuelve null si no es válida.
 */
export function versionDesdeParche(
  parche: string | null | undefined
): string | null {

  const coincidencia =
    parche?.match(/^(\d+)\.(\d+)/);

  return coincidencia
    ? `${coincidencia[1]}.${coincidencia[2]}.1`
    : null;

}


/**
 * Devuelve la versión actual de Data Dragon (una sola
 * petición por sesión) o null si no se pudo obtener.
 */
export function obtenerVersionDataDragon(): Promise<string | null> {

  if (versionEnMemoria) {
    return Promise.resolve(versionEnMemoria);
  }

  if (!peticionVersion) {

    peticionVersion = fetch(URL_VERSIONES)
      .then((response) => {

        if (!response.ok) {
          throw new Error("versions.json no disponible");
        }

        return response.json() as Promise<unknown>;

      })
      .then((versiones) => {

        if (
          !Array.isArray(versiones) ||
          typeof versiones[0] !== "string"
        ) {
          throw new Error("versions.json no válido");
        }

        versionEnMemoria = versiones[0];

        try {
          localStorage.setItem(
            CLAVE_ULTIMA_VERSION,
            versiones[0]
          );
        } catch {
          // Sin almacenamiento local: solo queda en memoria.
        }

        return versiones[0];

      })
      .catch(() => {

        // Se permite reintentar en la próxima apertura.
        peticionVersion = null;

        return null;

      });

  }

  return peticionVersion;

}


/**
 * Riot envía championName ("MonkeyKing", "FiddleSticks")
 * y Data Dragon usa su id de campeón.
 */
function idCampeonDataDragon(
  nombre: string
): string {

  const limpio =
    nombre.replace(
      /[^a-zA-Z0-9]/g,
      ""
    );

  return limpio === "FiddleSticks"
    ? "Fiddlesticks"
    : limpio;

}


export function urlIconoCampeon(
  version: string | null,
  nombre: string | null
): string | null {

  if (!version || !nombre) {
    return null;
  }

  return (
    `${URL_DATA_DRAGON}/cdn/${version}/img/champion/` +
    `${idCampeonDataDragon(nombre)}.png`
  );

}


export function urlIconoObjeto(
  version: string | null,
  itemId: number
): string | null {

  if (!version || !itemId) {
    return null;
  }

  return (
    `${URL_DATA_DRAGON}/cdn/${version}/img/item/${itemId}.png`
  );

}
