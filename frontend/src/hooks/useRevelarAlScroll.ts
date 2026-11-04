import {
  type RefObject,
  useEffect,
} from "react";


/**
 * Hace aparecer los hijos directos del contenedor cuando entran en pantalla.
 * Solo agrega clases CSS (.revelar / .revelado); no cambia el DOM ni los datos.
 */
export function useRevelarAlScroll(
  contenedor: RefObject<HTMLElement | null>,
  dependencia: unknown
) {

  useEffect(() => {

    const elemento =
      contenedor.current;

    if (
      !elemento ||
      !("IntersectionObserver" in window)
    ) {
      return;
    }


    const secciones =
      Array.from(
        elemento.children
      ) as HTMLElement[];


    const observador =
      new IntersectionObserver(
        (entradas) => {

          entradas.forEach((entrada) => {

            if (entrada.isIntersecting) {

              entrada.target.classList.add(
                "revelado"
              );

              observador.unobserve(
                entrada.target
              );

            }

          });

        },
        {
          threshold: 0.08,
          rootMargin: "0px 0px -40px 0px",
        }
      );


    secciones.forEach((seccion) => {

      seccion.classList.add("revelar");

      observador.observe(seccion);

    });


    return () => {

      observador.disconnect();

    };

  }, [contenedor, dependencia]);

}
