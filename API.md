# CEDAR API — for the web team

A FastAPI service that exposes CEDAR's **data points** and **deterministic procedures** so the
front-end can be built against a clean contract. It shares one engine with the CLI (`cedar.py`)
via a framework-free service layer (`cedar_service.py`), so the API and CLI can never disagree.

## Run it
```bash
pip install -r requirements.txt
uvicorn api:app --reload --port 8000
# Interactive docs (try every endpoint in the browser):
open http://localhost:8000/docs
```
- Set `CEDAR_OFFLINE=1` to force the bundled cache (no network). Otherwise the API tries the live
  World Bank API and transparently falls back to cache.
- CORS is open (`*`) so a browser app can call it directly during development.

## The mode toggle (deterministic ↔ copilot)
The whole app runs in one of two modes — this is the "initial toggle" the UI should render:

| Mode | What's available |
|---|---|
| `deterministic` (default) | All grounded, **$0, no-LLM** procedures and data endpoints. |
| `copilot` | The above **plus** the LLM endpoints (`/copilot/*`), which need an OpenAI key. |

```bash
curl localhost:8000/mode
# {"mode":"deterministic","capabilities":{"deterministic":true,"llm_copilot":false,...}}

curl -X POST localhost:8000/mode -H "Content-Type: application/json" -d '{"mode":"copilot"}'
```
The front-end should `GET /mode` on load to render the toggle and enable/disable the chat. LLM
endpoints return **403** while in deterministic mode. The OpenAI key is **never stored** by the
server — it is passed per request via the `X-OpenAI-Key` header (or an `OPENAI_API_KEY` env var).

## Endpoints

### Meta
- `GET /` · `GET /health` — service info, current mode, capabilities.

### Mode
- `GET /mode` — current mode + capability flags.
- `POST /mode` `{"mode":"deterministic"|"copilot"}` — flip the toggle.

### Metadata
- `GET /catalog` — themes, indicators (name/unit/lineage/`better`), SDG targets, polycrisis domains, source meta.
- `GET /countries` — `[{iso3, name}]` available in the cache.

### Data points
- `GET /series/{country}/{code}` — one provenance-stamped time series. e.g. `/series/KEN/SH.DYN.MORT`.

### Deterministic procedures ($0, no LLM)
- `GET /brief/{country}?theme=child-survival` — themed evidence brief: per-indicator obs, verification
  (confidence + caveats), and computed **claims** (trend, gap-to-target, **time-to-target projection**), with cost report.
- `GET /drilldown/{country}?dimension=wealth` — within-country equity (stunting by wealth quintile): quintiles, national, ratio, gap.
- `GET /polycrisis/{country}` — cross-SDG composite: per-domain status + stress band.
- `GET /blindspots/{country}?cutoff=2022` — **blind-spot radar**: which key SDG indicators are current / stale / missing.
- `GET /project/{country}/{code}` — **time-to-SDG-target** projection for one indicator (reach year, years late).
- `GET /interventions/{theme}` — curated, cited "effective interventions by evidence strength" (illustrative synthesis).

### LLM copilot (only when mode = copilot)
- `POST /copilot/summary` — guardrailed executive summary of a country/theme brief. The model only
  rewrites the verified claims; any number it invents is **blocked** and reported.
  ```bash
  curl -X POST localhost:8000/copilot/summary \
    -H "Content-Type: application/json" -H "X-OpenAI-Key: sk-..." \
    -d '{"country":"KEN","theme":"child-survival","model":"gpt-4o-mini"}'
  ```

## Examples
```bash
curl localhost:8000/brief/KEN?theme=child-survival
curl localhost:8000/polycrisis/KEN
curl localhost:8000/blindspots/NGA
curl localhost:8000/project/KEN/SH.DYN.MORT      # -> reach_year 2037, years_late 7
curl localhost:8000/interventions/economy-poverty
```

## Response shape notes
- Every data/procedure response carries **provenance** (publisher, upstream source, re-runnable
  `query_url`, retrieval mode) and, where relevant, a `cost` report — so the UI can show grounding and spend.
- `obs` maps year → value (nulls omitted in derived views). `better` tells the UI the good direction.
- Numbers are never model-generated in the deterministic endpoints.
