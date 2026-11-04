import type {
  Dispatch,
  FormEvent,
  SetStateAction,
} from "react";

interface NavbarProps {
  riotId: string;

  setRiotId:
    Dispatch<SetStateAction<string>>;

  region: string;

  setRegion:
    Dispatch<SetStateAction<string>>;

  cargando: boolean;

  onAnalizar:
    (event?: FormEvent) => void;
}

const regiones = [
  { value: "LAS", label: "LAS" },
  { value: "LAN", label: "LAN" },
  { value: "NA", label: "NA" },
  { value: "BR", label: "BR" },

  { value: "EUW", label: "EUW" },
  { value: "EUNE", label: "EUNE" },
  { value: "TR", label: "TR" },
  { value: "RU", label: "RU" },

  { value: "KR", label: "KR" },
  { value: "JP", label: "JP" },

  { value: "OCE", label: "OCE" },
  { value: "PH", label: "PH" },
  { value: "SG", label: "SG" },
  { value: "TH", label: "TH" },
  { value: "TW", label: "TW" },
  { value: "VN", label: "VN" },
];

function Navbar({
  riotId,
  setRiotId,
  region,
  setRegion,
  cargando,
  onAnalizar,
}: NavbarProps) {

  return (

    <header className="header">

      <div className="logo">

        <span className="logo-icon">
          ◆
        </span>

        <div>

          <h1>
            RiftLens
          </h1>

          <p>
            Análisis competitivo
          </p>

        </div>

      </div>


      <form
        className="header-search"
        onSubmit={onAnalizar}
      >

        <input
          type="text"
          placeholder="Nombre#Tag"
          value={riotId}
          onChange={(event) =>
            setRiotId(
              event.target.value
            )
          }
          disabled={cargando}
        />

        <div className="region-select-wrapper">
  <select
    className="region-select"
    value={region}
    onChange={(event) =>
      setRegion(
        event.target.value
      )
    }
    disabled={cargando}
    aria-label="Seleccionar región"
  >
    {
      regiones.map(
        (regionItem) => (
          <option
            key={regionItem.value}
            value={regionItem.value}
          >
            {regionItem.label}
          </option>
        )
      )
    }
  </select>

  <span className="region-select-arrow">
    ▾
  </span>
</div>

        <button
          type="submit"
          disabled={cargando}
        >

          {
            cargando
              ? "Analizando..."
              : "Analizar"
          }

        </button>

      </form>

    </header>

  );
}

export default Navbar;