import {
  useEffect,
  useState,
} from "react";

import {
  leerUltimaVersionConocida,
  obtenerVersionDataDragon,
  versionDataDragonEnMemoria,
  versionDesdeParche,
} from "../services/dataDragon";


/**
 * Versión de Data Dragon para los íconos.
 * - Mientras se consulta devuelve null (los íconos esperan).
 * - Si la consulta falla usa la versión de la partida
 *   (version_parche) o, si no hay, la última conocida.
 */
export function useVersionDataDragon(
  versionParche: string | null | undefined
): string | null {

  const [version, setVersion] =
    useState<string | null>(
      versionDataDragonEnMemoria
    );

  const [fallo, setFallo] =
    useState(false);


  useEffect(() => {

    if (versionDataDragonEnMemoria()) {
      return;
    }

    let activo = true;

    obtenerVersionDataDragon()
      .then((actual) => {

        if (!activo) {
          return;
        }

        if (actual) {
          setVersion(actual);
        } else {
          setFallo(true);
        }

      });

    return () => {
      activo = false;
    };

  }, []);


  if (version) {
    return version;
  }

  if (fallo) {

    return (
      versionDesdeParche(versionParche) ??
      leerUltimaVersionConocida()
    );

  }

  return null;

}
