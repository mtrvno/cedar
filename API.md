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

## Endpoints at a glance

| Method | Path | Auth/mode | Purpose |
|---|---|---|---|
| GET | `/` , `/health` | — | service info, mode, capabilities |
| GET | `/mode` | — | current mode + capabilities |
| POST | `/mode` | — | flip deterministic ↔ copilot |
| GET | `/catalog` | — | themes, indicators, SDG targets, polycrisis domains |
| GET | `/countries` | — | available countries |
| GET | `/series/{country}/{code}` | — | one provenance-stamped time series |
| GET | `/brief/{country}` | — | themed evidence brief |
| GET | `/drilldown/{country}` | — | within-country equity (wealth quintiles) |
| GET | `/polycrisis/{country}` | — | cross-SDG composite risk read |
| GET | `/blindspots/{country}` | — | blind-spot radar (missing/stale data) |
| GET | `/project/{country}/{code}` | — | time-to-SDG-target projection |
| GET | `/interventions` | — | interventions by evidence strength, **all themes** |
| GET | `/interventions/{theme}` | — | interventions by evidence strength for one theme |
| GET | `/evidence-chain` | — | the 7-step pipeline definition (static) |
| GET | `/evidence-chain/{country}` | — | the chain with live per-step status for a run |
| GET | `/ccri` | — | UNICEF Children's Climate Risk Index (full table or one ISO3) |
| GET | `/gdacs` | — | current GDACS disaster alerts, each enriched with CCRI |
| GET | `/climate-risk` | — | GDACS×CCRI: underestimated alerts + where-to-focus |
| POST | `/copilot/summary` | copilot + key | guardrailed executive summary |
| POST | `/copilot/chat` | copilot + key | agentic, tool-grounded chat |

**Conventions.** Path params: `{country}` = ISO3 (case-insensitive, e.g. `KEN`); `{code}` = World Bank
indicator code (e.g. `SH.DYN.MORT`); `{theme}` ∈ `child-survival, economy-poverty, education, health-system, wash, energy-climate`.
Common query param `offline` (bool) forces the bundled cache. LLM endpoints require header `X-OpenAI-Key`
(or `OPENAI_API_KEY` env) **and** `mode=copilot`. All responses are JSON. Error shape: `{"detail": "..."}`
with status 400 (bad input), 403 (LLM disabled), 404 (no data for `/series` and `/drilldown`), 502 (LLM upstream error).
Note: `/brief`, `/polycrisis`, `/blindspots`, `/project` never 500 on missing data — they return **200** and flag the
gap (`available:false`, `status:"missing"`, or `projectable:false`). Treating absent data as a result, not an error, is intentional.

---

## Endpoint reference — inputs & outputs

### GET `/mode`  ·  POST `/mode`
**Input (POST):** JSON body `{ "mode": "deterministic" | "copilot" }`. (GET takes nothing.)
**Output:**
```json
{ "mode": "deterministic",
  "modes": ["deterministic","copilot"],
  "capabilities": { "deterministic": true, "llm_copilot": false, "openai_key_in_env": false },
  "note": "deterministic = grounded $0 procedures only; copilot = also enables LLM endpoints …" }
```

### GET `/catalog`
**Input:** none.
**Output:** `themes` (key → `{label, indicators[], headline, comparator|null}`), `indicators` (code → `{name, unit, better:"lower"|"higher", lineage}`), `sdg_targets` (code → `{target, label, direction:"below"|"above"}`), `polycrisis_domains` (`[{domain, indicator}]`), `source` (cache `_meta`).
```json
{ "themes": { "child-survival": { "label": "Child survival (SDG 2.2, 3.2)",
      "indicators": ["SH.DYN.MORT","SP.DYN.IMRT.IN","SH.IMM.IDPT","SH.STA.STNT.ZS"],
      "headline": "SH.DYN.MORT", "comparator": "SSF" } },
  "indicators": { "SH.DYN.MORT": { "name":"Under-5 mortality rate","unit":"per 1,000 live births","better":"lower","lineage":"UN IGME (UNICEF-led) -> World Bank WDI" } },
  "sdg_targets": { "SH.DYN.MORT": { "target":25, "label":"SDG 3.2.1…", "direction":"below" } },
  "polycrisis_domains": [ { "domain":"Child survival", "indicator":"SH.DYN.MORT" } ],
  "source": { "source_name":"World Bank World Development Indicators (WDI)", "source_last_updated":"2026-04-08" } }
```

### GET `/countries`
**Input:** none. **Output:**
```json
{ "countries": [ { "iso3": "AFG", "name": "Afghanistan" }, { "iso3": "AGO", "name": "Angola" } ] }
```

### GET `/series/{country}/{code}`
**Input:** path `country`, `code`; query `offline?`. **Output** (404 if no data):
```json
{ "country": "KEN", "indicator_code": "SH.DYN.MORT", "indicator_name": "Under-5 mortality rate",
  "unit": "per 1,000 live births", "ref_area_name": "Kenya",
  "obs": { "2010": 53.1, "2023": 39.6 },
  "provenance": { "publisher":"World Bank World Development Indicators (WDI)",
    "upstream_source":"UN IGME (UNICEF-led) -> WDI",
    "query_url":"https://api.worldbank.org/v2/country/KEN/indicator/SH.DYN.MORT?format=json&date=2010:2023",
    "source_last_updated":"2026-04-08", "retrieved_at":"2026-06-22T03:31:08Z", "retrieval_mode":"bundled-cache" } }
```

### GET `/brief/{country}`
**Input:** path `country`; query `theme` (default `child-survival`), `offline?`. **Output:**
```json
{ "country":"KEN", "theme":"child-survival", "label":"Child survival (SDG 2.2, 3.2)",
  "generated_at":"2026-06-22T03:31:08Z",
  "indicators": [
    { "code":"SH.DYN.MORT", "name":"Under-5 mortality rate", "unit":"per 1,000 live births",
      "available": true, "obs": { "2010":53.1, "2023":39.6 },
      "verification": { "n_values":14, "span_years":14, "coverage":1.0, "latest_year":2023,
                        "confidence_tier":"High", "caveats":[], "value_hash":"5b55d4762606" },
      "claims": [
        { "id":"SH.DYN.MORT.trend", "text":"Under-5 mortality rate fell from 53.1 to 39.6 …", "verdict":"improving",
          "datapoints":["SH.DYN.MORT@2010","SH.DYN.MORT@2023"] },
        { "id":"SH.DYN.MORT.target", "text":"As of 2023, the value of 39.6 does not yet meet the benchmark of 25 …",
          "verdict":"off-track", "datapoints":["SH.DYN.MORT@2023"], "benchmark":25 },
        { "id":"SH.DYN.MORT.project", "text":"At the 2010-2023 pace, the benchmark (25) is reached around 2037 - 7 year(s) late.",
          "verdict":"off-track", "datapoints":["SH.DYN.MORT@2010","SH.DYN.MORT@2023"] }
      ],
      "provenance": { "...": "as in /series" } }
  ],
  "cost": { "wall_clock_seconds":0.002, "authoritative_api_calls":0, "cache_hits":5,
            "llm_calls":0, "cedar_llm_cost_usd":0.0, "naive_single_big_model_cost_usd":0.097,
            "cost_reduction_vs_naive":"100%", "runs_with_zero_llm":true } }
```
**Data availability.** Any indicator that is missing **or returns an all-null series** (e.g. Afghanistan
has no recent poverty data in WDI) is reported as `{ "code":…, "name":…, "available": false }` — with no
`obs`/`verification`/`claims`. The endpoint still returns **200**; the front-end should branch on
`available` and render "no data" for those. If *every* indicator in a theme is unavailable you simply get
an `indicators` array where all entries are `available:false` (still 200). Example — `GET /brief/AFG?theme=economy-poverty`:
```json
{ "country":"AFG", "theme":"economy-poverty", "label":"Economy & poverty (SDG 1, 8)",
  "generated_at":"…",
  "indicators":[ { "code":"SI.POV.DDAY", "name":"Poverty rate ($3.00/day, 2021 PPP)", "available":false },
                 { "code":"NY.GDP.PCAP.CD", "name":"GDP per capita", "available":false },
                 { "code":"SL.UEM.TOTL.ZS", "name":"Unemployment rate", "available":false } ],
  "cost": { "...": "cost report" } }
```

### GET `/drilldown/{country}`
**Input:** path `country`; query `dimension` (default `wealth`), `offline?`. 404 if the country has no wealth-disaggregated data. **Output:**
```json
{ "country":"NGA", "dimension":"wealth_quintile", "indicator":"SH.STA.STNT.ZS", "year":2018, "national":36.8,
  "quintiles": [ { "code":"SH.STA.STNT.Q1.ZS", "quintile":"poorest (Q1)", "value":55.4,
                   "query_url":"https://api.worldbank.org/v2/country/NGA/indicator/SH.STA.STNT.Q1.ZS?format=json" },
                 { "code":"SH.STA.STNT.Q5.ZS", "quintile":"richest (Q5)", "value":16.8, "query_url":"…" } ],
  "ratio_poorest_to_richest":3.3, "gap_points":38.6, "cost": { "...": "cost report" } }
```

### GET `/polycrisis/{country}`
**Input:** path `country`; query `offline?`. **Output:**
```json
{ "country":"KEN", "stressed":5, "scored":7, "band":"high",
  "domains": [
    { "domain":"Child survival", "indicator":"SH.DYN.MORT", "name":"Under-5 mortality rate",
      "unit":"per 1,000 live births", "available":true, "value":39.6, "year":2023, "benchmark":25,
      "status":"off-track", "stressed":true, "confidence":"High", "query_url":"…" },
    { "domain":"Nutrition", "indicator":"SH.STA.STNT.ZS", "value":17.6, "year":2022, "benchmark":null,
      "status":"improving", "stressed":false, "confidence":"Low", "available":true, "query_url":"…" }
  ],
  "cost": { "...": "cost report" } }
```
`band` ∈ `high` (≥4 stressed) / `elevated` (≥2) / `lower`. Unavailable domains: `{domain, indicator, available:false}`.

### GET `/blindspots/{country}`
**Input:** path `country`; query `cutoff` (int, default `2022`), `offline?`. **Output:**
```json
{ "country":"KEN", "cutoff":2022, "total":15, "missing":0, "stale":2, "recent":13, "gaps":2,
  "indicators": [ { "indicator":"EG.ELC.ACCS.ZS", "name":"Access to electricity", "status":"recent", "latest":2023 },
                  { "indicator":"EG.FEC.RNEW.ZS", "name":"Renewable energy share", "status":"stale", "latest":2021 } ],
  "cost": { "...": "cost report" } }
```
`status` ∈ `recent` (latest ≥ cutoff) / `stale` (older) / `missing` (`latest:null`).

### GET `/project/{country}/{code}`
**Input:** path `country`, `code`; query `offline?`. **Output** (when the indicator has an SDG target):
```json
{ "country":"KEN", "indicator":"SH.DYN.MORT", "latest":39.6, "latest_year":2023, "target":25,
  "direction":"below", "met":false, "projectable":true, "reach_year":2037, "years_late":7,
  "diverging":false, "on_time":false, "note":"reaches target ~2037" }
```
If the indicator has no target or no data: `{ "projectable": false, "reason": "no target" | "no data" }`. If the trend moves away from the target: `{ "diverging": true, "reach_year": null, "years_late": null }`. If already met: `{ "met": true, "reach_year": <latest_year>, "years_late": 0 }`.

### GET `/interventions/{theme}`
**Input:** path `theme` (one of the six theme keys — **required**; call `/interventions` for all themes at once). **Output:**
```json
{ "theme":"economy-poverty", "counts": { "High":1, "Moderate":4, "Limited":1 },
  "interventions": [ { "name":"Cash transfers & social protection", "evidence_strength":"High",
      "rationale":"Robust evidence for reducing poverty and vulnerability.",
      "source":"World Bank", "source_url":"https://www.worldbank.org" } ],
  "note":"Illustrative evidence synthesis from published reviews …; distinct from the live indicator data." }
```
`evidence_strength` ∈ `High` | `Moderate` | `Limited`. Returns 400 with `{themes:[…]}` for an unknown theme.

### GET `/interventions`
**Input:** none. **Output:** every theme's interventions in one payload (same per-theme shape as above):
```json
{ "themes": {
    "child-survival":  { "theme":"child-survival",  "counts":{…}, "interventions":[…], "note":"…" },
    "economy-poverty": { "theme":"economy-poverty", "counts":{…}, "interventions":[…], "note":"…" }
} }
```

### GET `/evidence-chain`
**Input:** none. **Output:** the static 7-step pipeline definition (for rendering the chain UI):
```json
{ "steps": [
    { "id":"discover", "step":"Discover", "agent":"Agent 1", "description":"Resolve indicator & country codes and metadata for the question." },
    { "id":"retrieve", "step":"Retrieve", "agent":"Agent 1", "description":"Fetch authoritative series; stamp provenance on every datapoint." },
    { "id":"verify",   "step":"Verify",   "agent":"Agent 2", "description":"Check coverage, recency & data gaps; assign confidence; raise caveats." },
    { "id":"analyse",  "step":"Analyse",  "agent":"Agent 3", "description":"Compute trend, gap-to-target and projection deterministically (no LLM)." },
    { "id":"narrate",  "step":"Narrate",  "agent":"Agent 4", "description":"Render the verified claims to prose; every figure carries a citation." },
    { "id":"review",   "step":"Review",   "agent":"Agent 5", "description":"Refuse to ship any number that lacks a supporting datapoint." },
    { "id":"output",   "step":"Output",   "agent":"—",       "description":"Emit the brief + evidence ledger + provenance graph + cost report." }
  ],
  "note":"Every CEDAR output moves through these steps; nothing downstream uses a value an earlier step did not verify." }
```

### GET `/evidence-chain/{country}`
**Input:** path `country`; query `theme` (default `child-survival`), `offline?`. **Output:** the same 7 steps,
each annotated with a live `status` and a `detail` derived from an actual brief run — ideal for animating the stepper:
```json
{ "country":"KEN", "theme":"child-survival", "review_passed": true,
  "steps": [
    { "id":"discover", "step":"Discover", "agent":"Agent 1", "description":"…", "status":"done", "detail":"4 indicators" },
    { "id":"retrieve", "step":"Retrieve", "agent":"Agent 1", "description":"…", "status":"done", "detail":"36 datapoints" },
    { "id":"verify",   "step":"Verify",   "agent":"Agent 2", "description":"…", "status":"done", "detail":"1 caveat(s)" },
    { "id":"analyse",  "step":"Analyse",  "agent":"Agent 3", "description":"…", "status":"done", "detail":"10 claims" },
    { "id":"narrate",  "step":"Narrate",  "agent":"Agent 4", "description":"…", "status":"done", "detail":"10 cited" },
    { "id":"review",   "step":"Review",   "agent":"Agent 5", "description":"…", "status":"done", "detail":"passed" },
    { "id":"output",   "step":"Output",   "agent":"—",       "description":"…", "status":"done", "detail":"ready" }
  ],
  "cost": { "...": "cost report" } }
```

### GET `/ccri`
UNICEF **Children's Climate & Environment Risk Index** (CCRI, 2021) — a grounded static dataset of 163 scored
countries, 0 (lowest risk) → 10 (highest). **Input:** optional query `country` (ISO3). With no `country`, returns the
full table + metadata; with one, returns that country's record.
```json
// GET /ccri?country=CAF
{ "iso3":"CAF", "name":"Central African Republic", "ccri":8.7, "exposure":6.7, "vulnerability":9.8, "tier":"Extremely High" }
```
```json
// GET /ccri  (abridged)
{ "indicator":"Children's Climate and Environment Risk Index (CCRI)", "scale":"0 (lowest risk) to 10 (highest risk)",
  "extremely_high_threshold":7.0, "n_scored":163, "n_extremely_high":33,
  "pillars":{ "exposure":"Pillar 1 - …hazards, shocks, stresses", "vulnerability":"Pillar 2 - child vulnerability…" },
  "source":{ "name":"UNICEF CCRI, 2021", "report":"https://www.unicef.org/reports/climate-crisis-child-rights-crisis", "data":"…/FeatureServer/1" },
  "countries":{ "CAF":{ "name":"Central African Republic", "ccri":8.7, "exposure":6.7, "vulnerability":9.8, "tier":"Extremely High" }, "…":{} } }
```
- `exposure` = Pillar 1 (climate/environmental hazards); `vulnerability` = Pillar 2 (child health, nutrition, education, WASH, poverty, social protection). `tier` ∈ `Extremely High (>7) · High · Medium · Low · Very Low`.

### GET `/gdacs`
Current **GDACS** disaster alerts (Global Disaster Alert and Coordination System, UN OCHA / European Commission),
each enriched with the affected country's CCRI. **Input:** query `offline?`. Live by default (server fetches GDACS via
HTTPS); falls back to a bundled snapshot if the network is unavailable — see `provenance.mode`.
```json
{ "generated_at":"2026-06-20T…Z",
  "provenance":{ "mode":"live", "source":"https://www.gdacs.org/gdacsapi/api/events/geteventlist/EVENTS4APP", "retrieved":"…", "count":42 },
  "n_events":42,
  "events":[
    { "id":1545522, "type":"EQ", "type_name":"Earthquake", "alertlevel":"Green", "alertscore":1,
      "country":"Philippines", "iso3":"PHL", "severity":4.9, "severity_text":"Magnitude 4.9M…",
      "from":"2026-06-11T00:00:43", "to":"2026-06-11T00:00:43", "coordinates":[125.6,7.1],
      "url":"https://www.gdacs.org/report.aspx?eventtype=EQ&eventid=1545522",
      "ccri":{ "iso3":"PHL", "name":"Philippines", "ccri":7.1, "exposure":8.9, "vulnerability":4.0, "tier":"Extremely High" } }
  ],
  "ccri_source":{ "name":"UNICEF CCRI, 2021", "…":"…" } }
```
- `ccri` is `null` for events GDACS leaves un-coded (open-ocean / some multi-country events) or for unscored small states.

### GET `/climate-risk`
The headline analytic: **join GDACS × CCRI to surface "underestimated" alerts** — hazards GDACS graded low/medium
priority (Green/Orange) that strike *extremely high* child-risk countries (CCRI > 7), where a hazard-only triage may
under-serve children. **Input:** query `levels` (comma-separated GDACS levels to flag, default `Green,Orange`), `offline?`.
```json
{ "generated_at":"2026-06-20T…Z",
  "provenance":{ "mode":"live", "source":"…/EVENTS4APP", "retrieved":"…", "count":42 },
  "method":{ "definition":"underestimated = GDACS alertlevel in ['Green','Orange'] AND country CCRI > 7.0",
             "rationale":"GDACS alert colour reflects hazard magnitude, exposed population and a generic vulnerability proxy - not child-specific vulnerability…",
             "ccri_threshold":7.0, "limitations":"alerts without an ISO3 code can't be joined; CCRI is a 2021 static index of 163 countries" },
  "global_scope":{ "total_alerts":42, "by_alert_level":{ "Green":38, "Orange":3, "Red":1 },
                   "by_hazard_type":{ "Earthquake":21, "Tropical cyclone":6, "Flood":9, "Drought":6 },
                   "alerts_with_ccri":30, "flagged_alerts":7, "focus_countries":5 },
  "headline":"42 active GDACS alerts worldwide; 7 are Green/Orange alerts striking 'extremely high' child-risk countries (CCRI > 7) across 5 countries…",
  "underestimated_alerts":[
    { "id":1545522, "type_name":"Earthquake", "alertlevel":"Green", "country":"Philippines", "iso3":"PHL",
      "severity":4.9, "from":"…", "url":"…", "ccri":7.1, "exposure":8.9, "vulnerability":4.0, "tier":"Extremely High",
      "why":"GDACS graded this Green (low/medium priority), but Philippines is an 'extremely high' child-risk country (CCRI 7.1/10; child-vulnerability 4.0/10) - children's exposure is likely underestimated…" }
  ],
  "where_to_focus":[
    { "iso3":"PHL", "country":"Philippines", "ccri":7.1, "exposure":8.9, "vulnerability":4.0, "tier":"Extremely High",
      "n_alerts":2, "alert_levels":["Green"], "hazards":["Earthquake"], "max_severity":5.1, "alert_ids":[1545522,1545514] }
  ],
  "sources":[ { "name":"UNICEF CCRI, 2021", "…":"…" }, { "name":"GDACS (UN OCHA / European Commission)", "site":"https://www.gdacs.org" } ],
  "disclaimer":"Not an official United Nations product." }
```
- `where_to_focus` is ranked by child-risk (CCRI) first, then number of flagged alerts, then any Orange ahead of Green — a direct "which countries to prioritise" list.
- Use `levels=Green` for the strictest "lowest-priority hazards only" read, or add `Red` to widen the lens.

### POST `/copilot/summary`  *(mode = copilot)*
**Input:** header `X-OpenAI-Key`; JSON body `{ "country": "KEN", "theme": "child-survival", "model": "gpt-4o-mini" }` (`theme`,`model` optional).
```bash
curl -X POST localhost:8000/copilot/summary -H "Content-Type: application/json" \
  -H "X-OpenAI-Key: sk-..." -d '{"country":"KEN","theme":"child-survival"}'
```
**Output:**
```json
{ "country":"KEN", "theme":"child-survival",
  "grounded_claims":"- Under-5 mortality rate fell from 53.1 to 39.6 …\n- As of 2023 …",
  "summary":"Kenya has cut under-5 mortality to 39.6 per 1,000 (2023) but remains above the SDG target of 25 …",
  "blocked":false, "invented_numbers":[], "model":"gpt-4o-mini", "tokens": { "in":420, "out":96 } }
```
If the model emits a figure not in the claims, it is withheld: `{ "summary": null, "blocked": true, "invented_numbers": ["3.1"] }`. Returns 403 if not in copilot mode, 400 if no key.

### POST `/copilot/chat`  *(mode = copilot)*
**Input:** header `X-OpenAI-Key`; JSON body:
```json
{ "country":"KEN",
  "messages":[ { "role":"user", "content":"Is Kenya on track for child survival, and what works?" } ],
  "model":"gpt-4o-mini" }
```
`messages` is the conversation so far (`role` ∈ `user`|`assistant`, plus any prior turns). **Output** — note the
**per-prompt `evidence_chain`** and the raw `tool_calls`, both reflecting what *this* answer actually did:
```json
{ "answer":"Kenya's under-5 mortality is 39.6 per 1,000 (2023), down from 53.1 (2010) but above the SDG target of 25 …",
  "grounded":true, "unverified_numbers":[],
  "sources":[ { "country":"Kenya", "iso":"KEN", "code":"SH.DYN.MORT", "name":"Under-5 mortality rate",
                "latest":{ "year":2023, "value":39.6 },
                "query_url":"https://api.worldbank.org/v2/country/KEN/indicator/SH.DYN.MORT?format=json" } ],
  "tool_calls":[ { "name":"get_indicator", "args":{ "iso":"KEN","code":"SH.DYN.MORT" }, "detail":"14 values · 2023: 39.6" } ],
  "charts":[
    { "type":"line", "title":"Under-5 mortality", "unit":"per 1,000 live births",
      "x":[2010, "…", 2023],
      "series":[ { "label":"Kenya", "data":[53.1, "…", 39.6] } ],
      "sources":[ { "label":"Kenya · Under-5 mortality rate",
                    "query_url":"https://api.worldbank.org/v2/country/KEN/indicator/SH.DYN.MORT?format=json" } ] }
  ],
  "evidence_chain":[
    { "id":"discover", "step":"Discover", "agent":"Agent 1", "status":"done", "detail":"1 tool call(s) · 1 indicator(s), 1 country(ies)", "description":"…" },
    { "id":"retrieve", "step":"Retrieve", "agent":"Agent 1", "status":"done", "detail":"1 series · 14 datapoints", "description":"…" },
    { "id":"verify",   "step":"Verify",   "agent":"Agent 2", "status":"done", "detail":"1 grounded source(s)", "description":"…" },
    { "id":"analyse",  "step":"Analyse",  "agent":"Agent 3", "status":"done", "detail":"computed from retrieved data", "description":"…" },
    { "id":"narrate",  "step":"Narrate",  "agent":"Agent 4", "status":"done", "detail":"22 words", "description":"…" },
    { "id":"review",   "step":"Review",   "agent":"Agent 5", "status":"done", "detail":"passed — all figures grounded", "description":"…" },
    { "id":"output",   "step":"Output",   "agent":"—",       "status":"done", "detail":"1 source(s) cited", "description":"…" }
  ],
  "tokens":{ "in":1320, "out":180 }, "model":"gpt-4o-mini" }
```
- `evidence_chain` is computed **per prompt** from the agent's actual run (tool calls, datapoints fetched, grounding result), so the UI can render a chain specific to each answer (not the generic `/evidence-chain` definition).
- `charts` is a (possibly empty) list of **render-ready chart specs** the agent chose to build to complement the prose; numbers come only from retrieved data (the guardrail also checks figures plotted here). Render directly with any chart library:
  - `type:"line"` → `x` (array of years) + `series:[{label, data}]` where each `data` aligns to `x` (`null` = gap).
  - `type:"bar"` → `categories` (array of labels) + `series:[{label:"latest", data}]` plus `years` (array aligned to `categories` — the year each latest value is from).
  - Every spec carries `title`, `unit`, and `sources:[{label, query_url}]` so the chart stays cited and re-runnable.
- When the answer contains a figure not found in the retrieved data, `grounded` is `false`, `unverified_numbers` lists them, and the `review` step has `status:"warn"` with a `detail` naming the flagged figures.
- Returns 403 if not in copilot mode, 400 if no key/empty messages.

**Agent tools** the model may call while answering (all grounded; the caller never invokes these directly):

| Tool | Purpose |
|------|---------|
| `get_indicator` | one indicator time series for one country (World Bank) |
| `compare_indicator` | latest value of one indicator across several countries |
| `list_indicators` | the indicator codes CEDAR knows by name |
| `get_interventions` | effective interventions for a theme, graded by evidence strength, with sources |
| `build_chart` | builds a chart spec (returned in `charts`) to attach a graph to the answer |

## Typed clients for the front-end (TypeScript)
FastAPI publishes a full OpenAPI schema at **`/openapi.json`**, so the web team gets typed clients for free:

```bash
# 1) start the API:  uvicorn api:app --port 8000
# 2) generate types (pick one):
npx openapi-typescript http://localhost:8000/openapi.json -o web/src/cedar-api.d.ts          # types only
npx openapi-typescript-codegen --input http://localhost:8000/openapi.json --output web/src/cedar  # types + fetch client
```
Then in the app:
```ts
import type { paths } from "./cedar-api";
type Brief = paths["/brief/{country}"]["get"]["responses"]["200"]["content"]["application/json"];
```
The interactive Swagger UI at **`/docs`** (and ReDoc at `/redoc`) also lets the team explore and try every endpoint.

## Examples
```bash
curl localhost:8000/brief/KEN?theme=child-survival
curl localhost:8000/polycrisis/KEN
curl localhost:8000/blindspots/NGA
curl localhost:8000/project/KEN/SH.DYN.MORT      # -> reach_year 2037, years_late 7
curl localhost:8000/interventions                # all themes
curl localhost:8000/interventions/economy-poverty
curl localhost:8000/evidence-chain               # static 7-step definition
curl localhost:8000/evidence-chain/KEN?theme=child-survival   # steps with live status
```

## Response shape notes
- Every data/procedure response carries **provenance** (publisher, upstream source, re-runnable
  `query_url`, retrieval mode) and, where relevant, a `cost` report — so the UI can show grounding and spend.
- `obs` maps year → value (nulls omitted in derived views). `better` tells the UI the good direction.
- Numbers are never model-generated in the deterministic endpoints.
