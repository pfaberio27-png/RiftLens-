import {
  useEffect,
} from "react";


export type ToastTipo =
  | "success"
  | "error";


interface ToastProps {
  mensaje: string;
  tipo: ToastTipo;
  onCerrar: () => void;
}


function Toast({
  mensaje,
  tipo,
  onCerrar,
}: ToastProps) {

  useEffect(() => {

    const temporizador =
      window.setTimeout(
        () => {
          onCerrar();
        },
        5000
      );


    return () => {
      window.clearTimeout(
        temporizador
      );
    };

  }, [
    mensaje,
    tipo,
    onCerrar,
  ]);


  return (

    <div
      className={
        `rift-toast ${tipo}`
      }
      role="alert"
      aria-live="assertive"
    >

      <div className="rift-toast-icon">

        {
          tipo === "success"
            ? "✓"
            : "!"
        }

      </div>


      <div className="rift-toast-content">

        <strong>

          {
            tipo === "success"
              ? "Análisis completado"
              : "No se pudo analizar"
          }

        </strong>

        <span>
          {mensaje}
        </span>

      </div>


      <button
        type="button"
        className="rift-toast-close"
        onClick={onCerrar}
        aria-label="Cerrar notificación"
      >
        ×
      </button>


      <div className="rift-toast-progress" />

    </div>

  );

}


export default Toast;