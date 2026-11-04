import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";


// Duración de la animación de salida (debe coincidir con los CSS de los modales)
const DURACION_CIERRE_MS = 180;


/**
 * Retrasa el cierre de un modal para que se vea la animación de salida.
 * Devuelve si el modal se está cerrando y la función que lo cierra.
 */
export function useCierreAnimado(
  onCerrar: () => void
): [boolean, () => void] {

  const [cerrando, setCerrando] =
    useState(false);

  const temporizador =
    useRef<number | null>(null);


  useEffect(() => {

    return () => {

      if (temporizador.current !== null) {
        window.clearTimeout(
          temporizador.current
        );
      }

    };

  }, []);


  const cerrar = useCallback(() => {

    // Sin animación si el usuario prefiere movimiento reducido
    const movimientoReducido =
      window.matchMedia(
        "(prefers-reduced-motion: reduce)"
      ).matches;

    if (movimientoReducido) {
      onCerrar();
      return;
    }

    if (temporizador.current !== null) {
      return;
    }

    setCerrando(true);

    temporizador.current =
      window.setTimeout(() => {

        temporizador.current = null;

        setCerrando(false);

        onCerrar();

      }, DURACION_CIERRE_MS);

  }, [onCerrar]);


  return [cerrando, cerrar];

}
