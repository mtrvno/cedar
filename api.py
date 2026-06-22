"""
CEDAR API — FastAPI service exposing the data points and deterministic procedures
for the web team, plus a mode toggle (deterministic-only vs LLM copilot).

Run:
    pip install -r requirements.txt
    uvicorn api:app --reload --port 8000
Then open http://localhost:8000/docs  (interactive Swagger UI).

MODE TOGGLE
    The whole app runs in one of two modes:
      • "deterministic" (default) — only the grounded, $0, no-LLM procedures are available.
      • "copilot"               — additionally enables the LLM endpoints (caller supplies an
                                  OpenAI key per request via the X-OpenAI-Key header).
    GET  /mode            → current mode + capability flags (frontend reads this to render the toggle)
    POST /mode {"mode": "copilot"}  → flip the toggle
    LLM endpoints (/copilot/*) return 403 unless mode == "copilot".

Set CEDAR_OFFLINE=1 to force the bundled cache (no network); otherwise endpoints try the
live World Bank API and transparently fall back to cache.
"""
import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import cedar_service as svc

app = FastAPI(
    title="CEDAR API",
    version="1.0.0",
    description="Cited Evidence & Data Analytic Reporting — grounded SDG data points and "
                "deterministic analytic procedures, with an optional, gated LLM copilot.",
)
# Open CORS so the teammates' browser app can call this directly.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False,
                   allow_methods=["*"], allow_headers=["*"])

OFFLINE_DEFAULT = os.environ.get("CEDAR_OFFLINE", "0") in ("1", "true", "True", "yes")
STATE = {"mode": os.environ.get("CEDAR_MODE", "deterministic")}
MODES = ("deterministic", "copilot")

def _off(offline: Optional[bool]) -> bool:
    return OFFLINE_DEFAULT if offline is None else offline

def _capabilities():
    return {"deterministic": True, "llm_copilot": STATE["mode"] == "copilot",
            "openai_key_in_env": bool(os.environ.get("OPENAI_API_KEY"))}

# --------------------------------------------------------------------------- meta / health
@app.get("/", tags=["meta"])
def root():
    return {"service": "CEDAR API", "version": "1.0.0", "mode": STATE["mode"],
            "capabilities": _capabilities(), "docs": "/docs",
            "endpoints": ["/mode", "/catalog", "/countries", "/series/{country}/{code}",
                          "/brief/{country}", "/drilldown/{country}", "/polycrisis/{country}",
                          "/blindspots/{country}", "/project/{country}/{code}",
                          "/interventions/{theme}", "/copilot/summary"]}

@app.get("/health", tags=["meta"])
def health():
    return {"ok": True, "mode": STATE["mode"], "offline_default": OFFLINE_DEFAULT}

# --------------------------------------------------------------------------- the mode toggle
class ModeIn(BaseModel):
    mode: str

@app.get("/mode", tags=["mode"])
def get_mode():
    return {"mode": STATE["mode"], "modes": list(MODES), "capabilities": _capabilities(),
            "note": "deterministic = grounded $0 procedures only; copilot = also enables LLM "
                    "endpoints (supply OpenAI key via X-OpenAI-Key header)."}

@app.post("/mode", tags=["mode"])
def set_mode(body: ModeIn):
    if body.mode not in MODES:
        raise HTTPException(400, f"mode must be one of {MODES}")
    STATE["mode"] = body.mode
    return get_mode()

# --------------------------------------------------------------------------- metadata
@app.get("/catalog", tags=["metadata"])
def catalog():
    return svc.catalog()

@app.get("/countries", tags=["metadata"])
def countries():
    return {"countries": svc.countries()}

# --------------------------------------------------------------------------- data points
@app.get("/series/{country}/{code}", tags=["data"])
def series(country: str, code: str, offline: Optional[bool] = Query(None)):
    r = svc.series(country.upper(), code, _off(offline))
    if not r:
        raise HTTPException(404, f"no data for {code} / {country}")
    return r

# --------------------------------------------------------------------------- deterministic procedures
@app.get("/brief/{country}", tags=["procedures"])
def brief(country: str, theme: str = Query("child-survival"), offline: Optional[bool] = Query(None)):
    r = svc.brief(country.upper(), theme, _off(offline))
    if "error" in r:
        raise HTTPException(400, r["error"])
    return r

@app.get("/drilldown/{country}", tags=["procedures"])
def drilldown(country: str, dimension: str = Query("wealth"), offline: Optional[bool] = Query(None)):
    r = svc.drilldown(country.upper(), dimension, _off(offline))
    if "error" in r:
        raise HTTPException(404, r["error"])
    return r

@app.get("/polycrisis/{country}", tags=["procedures"])
def polycrisis(country: str, offline: Optional[bool] = Query(None)):
    return svc.polycrisis(country.upper(), _off(offline))

@app.get("/blindspots/{country}", tags=["procedures"])
def blindspots(country: str, cutoff: int = Query(2022), offline: Optional[bool] = Query(None)):
    return svc.blindspots(country.upper(), _off(offline), cutoff)

@app.get("/project/{country}/{code}", tags=["procedures"])
def project(country: str, code: str, offline: Optional[bool] = Query(None)):
    return svc.project(country.upper(), code, _off(offline))

@app.get("/interventions/{theme}", tags=["procedures"])
def interventions(theme: str):
    r = svc.interventions(theme)
    if "error" in r:
        raise HTTPException(400, r["error"])
    return r

# --------------------------------------------------------------------------- LLM copilot (gated by mode)
class SummaryIn(BaseModel):
    country: str
    theme: str = "child-survival"
    model: str = "gpt-4o-mini"

@app.post("/copilot/summary", tags=["copilot"])
def copilot_summary(body: SummaryIn, x_openai_key: Optional[str] = Header(None, alias="X-OpenAI-Key")):
    if STATE["mode"] != "copilot":
        raise HTTPException(403, "LLM is disabled in deterministic mode. POST /mode {\"mode\":\"copilot\"} to enable.")
    key = x_openai_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise HTTPException(400, "Provide an OpenAI key via the X-OpenAI-Key header (or OPENAI_API_KEY env).")
    b = svc.brief(body.country.upper(), body.theme, _off(None))
    if "error" in b:
        raise HTTPException(400, b["error"])
    claims = "\n".join("- " + c["text"] for ind in b["indicators"] if ind.get("available") for c in ind["claims"])
    if not claims:
        raise HTTPException(404, "no findings to summarise for this country/theme")
    try:
        out = svc.llm_summary(claims, key, body.model)
    except Exception as e:
        raise HTTPException(502, f"LLM call failed: {e.__class__.__name__}: {e}")
    return {"country": body.country.upper(), "theme": body.theme, "grounded_claims": claims, **out}
