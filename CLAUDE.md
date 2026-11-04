# RiftLens — instrucciones para Claude Code

## Proyecto
Sistema web de tesis (UPN, Ingeniería de Sistemas Computacionales): analiza el rendimiento
competitivo de jugadores de League of Legends.
Flujo: API de Riot Games → métricas por partida → comparación con la referencia profesional
(Oracle's Elixir 2026, por rol) → K-Means → dashboard web.

- Backend: Python + FastAPI + SQLAlchemy + SQL Server (pyodbc). Carpeta `backend/`.
- Frontend: React + TypeScript + Vite + Recharts. Carpeta `frontend/`. Se despliega en Vercel
  (variable `VITE_API_URL`).
- Base de datos: SQL Server, base `RiftLensDB`. Único script: `database/riftlens_crear_bd.sql`.
- Configuración: `backend/.env` (RIOT_API_KEY, DB_ENABLED, DB_SERVER, DB_NAME, DB_DRIVER,
  TEMPORADA_INICIO, RIOT_LIMITES).

## Cómo ejecutar (Windows)
- Backend, desde la raíz:
  `uv run python -m uvicorn backend.app.main:app --reload --reload-dir backend --port 8000`
  (no uses el ejecutable `uvicorn` directamente: Windows lo bloquea por el Control de aplicaciones).
- Frontend: `cd frontend` y luego `npm run dev` (http://localhost:5173).
- Verificación: `cd frontend && npm run build && npm run lint`.
- El proyecto está dentro de OneDrive: no vigiles `.venv` ni `node_modules` con recarga automática.

## Reglas generales
- Responde y comenta el código en español.
- No modifiques ni muestres el contenido de `backend/.env` (contiene la API key de Riot).
  Si hace falta una variable nueva, agrégala a `backend/.env.example` y dime qué línea añadir.
- No toques `backend/app/data/referencia_profesional.json`.
- Trabaja por etapas: antes de cambiar, muéstrame qué archivos vas a tocar y espera mi aprobación.
- Antes de modificar o eliminar algo, busca en TODO el proyecto (backend y frontend) dónde se usa.
- No cambies nombres ni la forma de los campos de la respuesta de `POST /api/analisis` que el
  frontend ya usa, salvo que la etapa lo pida; en ese caso actualiza también el frontend.
- No hagas commit ni push sin que yo lo pida.
- Al terminar cada etapa: comprueba que el backend arranca, que `GET /` responde, que
  `npm run build` y `npm run lint` pasan sin errores nuevos, y dame un informe con los archivos
  modificados, lo que podría verse afectado y lo que no pudiste probar.
- Si detectas un riesgo de romper algo, detente y pregúntame.

## Reglas de la tesis (no cambiar sin mi permiso)
- Algoritmo K-Means: variables KDA, CS/min, oro/min, daño/min y visión; StandardScaler;
  k de 2 a 6 elegido con el coeficiente de silueta.
- La referencia profesional solo tiene por rol: win_rate, kda, cs_por_minuto, oro_por_minuto,
  daño_por_minuto y vision_score. No inventes valores de referencia para otras métricas.
- Fortalezas/debilidades: umbral de ±5 % frente a la referencia profesional del rol principal.
- Solo se analizan partidas de cola 420 (Ranked Solo/Dúo) de la temporada actual
  (desde TEMPORADA_INICIO), máximo 100.
- Los remakes (menos de 300 s o gameEndedInEarlySurrender) se muestran como
  "Remake / no válida" y se excluyen de todos los cálculos.
- Recomendaciones: sin inteligencia artificial; se eligen del catálogo
  `backend/app/data/recomendaciones.json`.

## Diseño
- Paleta estilo Hextech (azul marino oscuro, dorado y cian) definida como variables CSS en
  `frontend/src/styles/base.css`. No uses colores sueltos en los componentes.
- Las API keys nunca van en el frontend.