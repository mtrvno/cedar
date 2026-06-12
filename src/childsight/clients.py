"""HTTP clients for verified public APIs (all keyless, all tested live).

Every function returns data WITH provenance: source, retrieved_at, url.
Anti-hallucination is a design principle: tools never invent values —
if an API returns nothing, the tool says so explicitly.
"""

from __future__ import annotations

import asyncio
import contextvars
import csv
import hashlib
import io
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

GDACS_EVENTS = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/MAP"
EONET_EVENTS = "https://eonet.gsfc.nasa.gov/api/v3/events"
UNICEF_SDMX = "https://sdmx.data.unicef.org/ws/public/sdmxapi/rest"
SDG_API = "https://unstats.un.org/sdgapi/v1/sdg"

HEADERS = {"User-Agent": "childsight-mcp/0.1 (UN Hackathon 2026)"}
# Fail fast: a slow upstream must not blow past the MCP client's tool timeout.
TIMEOUT = float(os.environ.get("CHILDSIGHT_HTTP_TIMEOUT", "10"))

# Reuse connections (kinder to upstream APIs, faster for bursts of queries)
_session = requests.Session()
_session.headers.update(HEADERS)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# Tracks how the most recent response in this async task was served
# ("live" or "snapshot (<timestamp>)") so provenance never lies.
_served: contextvars.ContextVar[str] = contextvars.ContextVar("served", default="live")


def _stamp(source: str, url: str) -> dict[str, str]:
    return {"source": source, "url": url, "retrieved_at": _now(), "served": _served.get()}


# ---- demo-day resilience: in-memory TTL cache + on-disk snapshot fallback ----
CACHE_TTL_SECONDS = int(os.environ.get("CHILDSIGHT_CACHE_TTL", "600"))
SNAPSHOT_DIR = Path(os.environ.get("CHILDSIGHT_SNAPSHOT_DIR", Path(__file__).parent / "snapshots"))
CAPTURE = os.environ.get("CHILDSIGHT_CAPTURE") == "1"

_mem_cache: dict[str, tuple[float, "_Resp"]] = {}


class _Resp:
    """Minimal response object (text/json), used for cached and snapshot data."""

    def __init__(self, text: str):
        self.text = text

    def json(self) -> Any:
        return json.loads(self.text)


def _cache_key(url: str, params: dict | None) -> str:
    raw = url + "|" + json.dumps(params or {}, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def _snapshot_path(key: str) -> Path:
    return SNAPSHOT_DIR / f"{key}.json"


def _get_sync(url: str, params: dict | None = None) -> _Resp:
    key = _cache_key(url, params)

    cached = _mem_cache.get(key)
    if cached and time.time() - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    last_err: Exception | None = None
    for attempt in range(2):  # one retry
        try:
            r = _session.get(url, params=params, timeout=TIMEOUT)
            r.raise_for_status()
            resp = _Resp(r.text)
            _mem_cache[key] = (time.time(), resp)
            _served.set("live")
            if CAPTURE:
                SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
                _snapshot_path(key).write_text(json.dumps(
                    {"url": url, "params": params, "captured_at": _now(), "text": r.text}))
            return resp
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(0.5 * (attempt + 1))

    snap = _snapshot_path(key)
    if snap.exists():
        data = json.loads(snap.read_text())
        _served.set(f"snapshot (captured {data.get('captured_at', 'unknown')}) — live API unreachable")
        return _Resp(data["text"])

    raise last_err  # type: ignore[misc]


async def _get(url: str, params: dict | None = None) -> _Resp:
    """Async wrapper: run blocking request in a thread (keeps deps to stdlib + requests)."""
    return await asyncio.to_thread(_get_sync, url, params)


async def gather_limited(coros, limit: int = 4, per_task_timeout: float = 18.0) -> list:
    """Run coroutines with bounded concurrency and a per-task timeout.

    Prevents bursts of parallel queries from overwhelming upstream APIs
    (UNICEF SDMX throttles aggressively). Failures and timeouts come back
    as exceptions, never raised — callers degrade gracefully.
    """
    sem = asyncio.Semaphore(limit)

    async def run(c):
        async with sem:
            return await asyncio.wait_for(c, timeout=per_task_timeout)

    return await asyncio.gather(*(run(c) for c in coros), return_exceptions=True)


# ---------------------------------------------------------------- GDACS

async def gdacs_events(alert_levels: list[str] | None = None, event_types: list[str] | None = None) -> dict[str, Any]:
    """Live disaster events from GDACS (UN/EC joint system).

    alert_levels: subset of ["Green", "Orange", "Red"]
    event_types: subset of ["EQ", "TC", "FL", "VO", "DR", "WF"]
    """
    resp = await _get(GDACS_EVENTS)
    raw = resp.json()
    features = raw.get("features", [])
    # GDACS returns one feature per EPISODE; dedup to one per event (keep latest todate)
    by_event: dict[Any, dict] = {}
    for f in features:
        p = f.get("properties", {})
        eid = p.get("eventid")
        prev = by_event.get(eid)
        if prev is None or (p.get("todate") or "") > (prev.get("properties", {}).get("todate") or ""):
            by_event[eid] = f
    events = []
    for f in by_event.values():
        p = f.get("properties", {})
        level = p.get("alertlevel", "")
        etype = p.get("eventtype", "")
        if alert_levels and level not in alert_levels:
            continue
        if event_types and etype not in event_types:
            continue
        events.append({
            "event_id": p.get("eventid"),
            "type": etype,
            "type_name": _GDACS_TYPES.get(etype, etype),
            "name": p.get("eventname") or p.get("name"),
            "alert_level": level,
            "alert_score": p.get("alertscore"),
            "country": p.get("country"),
            "iso3": p.get("iso3"),
            "from_date": p.get("fromdate"),
            "to_date": p.get("todate"),
            "severity": (p.get("severitydata") or {}).get("severitytext") or p.get("severitytext"),
            "coordinates": (f.get("geometry") or {}).get("coordinates"),
            "report_url": (p.get("url") or {}).get("report") if isinstance(p.get("url"), dict) else None,
        })
    return {"events": events, "count": len(events), "provenance": _stamp("GDACS (UN OCHA / European Commission JRC)", GDACS_EVENTS)}


_GDACS_TYPES = {
    "EQ": "Earthquake", "TC": "Tropical Cyclone", "FL": "Flood",
    "VO": "Volcano", "DR": "Drought", "WF": "Wildfire",
}

# Map GDACS event types to CCRI hazard indicator codes (verified in CCRI dataflow)
GDACS_TO_CCRI = {
    "FL": ["CCRI_FLOODS_RIVERINE", "CCRI_FLOODS_COASTAL"],
    "TC": ["CCRI_TROPICAL_CYCLONES"],
    "DR": ["CCRI_WATER_SCARCITY"],
    "WF": ["CCRI_HEATWAVES"],
    "EQ": [],  # no CCRI hazard pillar for seismic; vulnerability pillar still applies
    "VO": [],
}

# Map GDACS event types to threatened SDG indicators (DESA official codes)
EVENT_TO_SDG = {
    "FL": [("1.5.1", "Deaths/affected by disasters"), ("6.1.1", "Safe drinking water"), ("3.2.1", "Under-5 mortality"), ("4.1.1", "School completion")],
    "TC": [("1.5.1", "Deaths/affected by disasters"), ("11.5.1", "Disaster impact in cities"), ("4.1.1", "School completion")],
    "DR": [("2.1.2", "Food insecurity"), ("2.2.1", "Child stunting"), ("6.4.2", "Water stress")],
    "WF": [("3.9.1", "Air pollution mortality"), ("15.1.1", "Forest area")],
    "EQ": [("1.5.1", "Deaths/affected by disasters"), ("11.5.1", "Disaster impact in cities"), ("3.2.1", "Under-5 mortality")],
    "VO": [("1.5.1", "Deaths/affected by disasters"), ("3.9.1", "Air pollution mortality")],
}


# ---------------------------------------------------------------- EONET

async def eonet_events(category: str | None = None, status: str = "open", limit: int = 50) -> dict[str, Any]:
    """Natural events from NASA EONET (satellite-observed)."""
    params: dict[str, Any] = {"status": status, "limit": limit}
    if category:
        params["category"] = category
    resp = await _get(EONET_EVENTS, params)
    raw = resp.json()
    events = [
        {
            "id": e.get("id"),
            "title": e.get("title"),
            "categories": [c.get("title") for c in e.get("categories", [])],
            "last_geometry": (e.get("geometry") or [{}])[-1],
            "sources": [s.get("url") for s in e.get("sources", [])],
        }
        for e in raw.get("events", [])
    ]
    return {"events": events, "count": len(events), "provenance": _stamp("NASA EONET", EONET_EVENTS)}


# ---------------------------------------------------------------- UNICEF SDMX

async def unicef_ccri(iso3: str) -> dict[str, Any]:
    """Children's Climate Risk Index for a country — per-hazard scores + sources.

    Verified live: returns ~27 indicators (hazard exposure + child vulnerability pillars).
    """
    url = f"{UNICEF_SDMX}/data/UNICEF,CCRI,1.0/{iso3.upper()}.?format=csv&lastNObservations=1"
    resp = await _get(url)
    rows = list(csv.DictReader(io.StringIO(resp.text)))
    if not rows:
        return {"iso3": iso3, "indicators": [], "note": "No CCRI data for this country", "provenance": _stamp("UNICEF CCRI", url)}
    indicators = [
        {
            "code": r["INDICATOR"],
            "name": r["Indicator"],
            "category": r["OBS_VALUE"],            # e.g. "Extremely High"
            "score": _ccri_score(r.get("OBS_FOOTNOTE", "")),  # numeric 0-10 from footnote
            "year": r["TIME_PERIOD"],
            "data_source": r.get("DATA_SOURCE") or None,
        }
        for r in rows
    ]
    return {"iso3": iso3.upper(), "country": rows[0]["Geographic area"], "indicators": indicators,
            "provenance": _stamp("UNICEF Children's Climate and Environment Risk Index (CCRI)", url)}


def _ccri_score(footnote: str) -> float | None:
    if footnote.startswith("Value:"):
        try:
            return float(footnote.split("Value:")[1].strip())
        except ValueError:
            return None
    return None


async def unicef_indicator(dataflow: str, iso3: str, indicator: str = "", last_n: int = 1) -> dict[str, Any]:
    """Generic UNICEF SDMX query. Verified dataflows include:
    DM (demography), NUTRITION, PT_CONFLICT, CHLD_PVTY, WASH_HOUSEHOLDS,
    CME (child mortality), EDUCATION, CHILD_RELATED_SDG, SDG_PROG_ASSESSMENT.
    """
    key = f"{iso3.upper()}.{indicator}" if indicator else f"{iso3.upper()}."
    url = f"{UNICEF_SDMX}/data/UNICEF,{dataflow},1.0/{key}?format=csv&lastNObservations={last_n}"
    resp = await _get(url)
    rows = list(csv.DictReader(io.StringIO(resp.text)))
    out = [
        {k: v for k, v in r.items() if v and k in (
            "REF_AREA", "Geographic area", "INDICATOR", "Indicator", "SEX", "AGE",
            "TIME_PERIOD", "OBS_VALUE", "UNIT_MEASURE", "DATA_SOURCE", "OBS_FOOTNOTE")}
        for r in rows
    ]
    return {"dataflow": dataflow, "rows": out, "count": len(out),
            "provenance": _stamp(f"UNICEF Data Warehouse ({dataflow})", url)}


async def unicef_child_population(iso3: str) -> dict[str, Any]:
    """Under-18 population from UNICEF demography dataflow (DM)."""
    return await unicef_indicator("DM", iso3, "DM_POP_U18", last_n=1)


# ---------------------------------------------------------------- DESA SDG API

async def sdg_series_data(series_code: str, area_code: str, page_size: int = 5) -> dict[str, Any]:
    """Official SDG indicator values from DESA Global SDG Database.

    Returns values WITH nature codes (Country/Estimated/Modeled), bounds,
    source, and footnotes — official provenance built in.
    """
    url = f"{SDG_API}/Series/Data"
    resp = await _get(url, {"seriesCode": series_code, "areaCode": area_code, "pageSize": page_size})
    raw = resp.json()
    data = [
        {
            "indicator": ".".join(d.get("indicator", [])),
            "series": d.get("series"),
            "description": d.get("seriesDescription"),
            "area": d.get("geoAreaName"),
            "year": d.get("timePeriodStart"),
            "value": d.get("value"),
            "nature": (d.get("attributes") or {}).get("Nature"),
            "units": (d.get("attributes") or {}).get("Units"),
            "official_source": d.get("source"),
            "footnotes": d.get("footnotes"),
        }
        for d in raw.get("data", [])
    ]
    return {"series": series_code, "total_available": raw.get("totalElements"), "data": data,
            "provenance": _stamp("UN DESA Global SDG Indicators Database", url)}


# ISO3 -> UN M49 numeric area codes (M49 equals ISO 3166-1 numeric for countries).
# Used to join GDACS (ISO3) with the DESA SDG API (M49). Missing codes degrade
# gracefully: SDG baselines are skipped, the rest of the brief still works.
ISO3_TO_M49: dict[str, str] = {
    "AFG": "004", "ALB": "008", "DZA": "012", "AND": "020", "AGO": "024", "ATG": "028",
    "AZE": "031", "ARG": "032", "AUS": "036", "AUT": "040", "BHS": "044", "BHR": "048",
    "BGD": "050", "ARM": "051", "BRB": "052", "BEL": "056", "BTN": "064", "BOL": "068",
    "BIH": "070", "BWA": "072", "BRA": "076", "BLZ": "084", "SLB": "090", "BRN": "096",
    "BGR": "100", "MMR": "104", "BDI": "108", "BLR": "112", "KHM": "116", "CMR": "120",
    "CAN": "124", "CPV": "132", "CAF": "140", "LKA": "144", "TCD": "148", "CHL": "152",
    "CHN": "156", "COL": "170", "COM": "174", "COG": "178", "COD": "180", "CRI": "188",
    "HRV": "191", "CUB": "192", "CYP": "196", "CZE": "203", "BEN": "204", "DNK": "208",
    "DMA": "212", "DOM": "214", "ECU": "218", "SLV": "222", "GNQ": "226", "ETH": "231",
    "ERI": "232", "EST": "233", "FJI": "242", "FIN": "246", "FRA": "250", "DJI": "262",
    "GAB": "266", "GEO": "268", "GMB": "270", "PSE": "275", "DEU": "276", "GHA": "288",
    "GRC": "300", "GRD": "308", "GTM": "320", "GIN": "324", "GUY": "328", "HTI": "332",
    "HND": "340", "HUN": "348", "ISL": "352", "IND": "356", "IDN": "360", "IRN": "364",
    "IRQ": "368", "IRL": "372", "ISR": "376", "ITA": "380", "CIV": "384", "JAM": "388",
    "JPN": "392", "KAZ": "398", "JOR": "400", "KEN": "404", "PRK": "408", "KOR": "410",
    "KWT": "414", "KGZ": "417", "LAO": "418", "LBN": "422", "LSO": "426", "LVA": "428",
    "LBR": "430", "LBY": "434", "LTU": "440", "LUX": "442", "MDG": "450", "MWI": "454",
    "MYS": "458", "MDV": "462", "MLI": "466", "MLT": "470", "MRT": "478", "MUS": "480",
    "MEX": "484", "MNG": "496", "MDA": "498", "MNE": "499", "MAR": "504", "MOZ": "508",
    "OMN": "512", "NAM": "516", "NRU": "520", "NPL": "524", "NLD": "528", "VUT": "548",
    "NZL": "554", "NIC": "558", "NER": "562", "NGA": "566", "NOR": "578", "FSM": "583",
    "MHL": "584", "PLW": "585", "PAK": "586", "PAN": "591", "PNG": "598", "PRY": "600",
    "PER": "604", "PHL": "608", "POL": "616", "PRT": "620", "GNB": "624", "TLS": "626",
    "QAT": "634", "ROU": "642", "RUS": "643", "RWA": "646", "KNA": "659", "LCA": "662",
    "VCT": "670", "SMR": "674", "STP": "678", "SAU": "682", "SEN": "686", "SRB": "688",
    "SYC": "690", "SLE": "694", "SGP": "702", "SVK": "703", "VNM": "704", "SVN": "705",
    "SOM": "706", "ZAF": "710", "ZWE": "716", "ESP": "724", "SSD": "728", "SDN": "729",
    "SUR": "740", "SWZ": "748", "SWE": "752", "CHE": "756", "SYR": "760", "TJK": "762",
    "THA": "764", "TGO": "768", "TON": "776", "TTO": "780", "ARE": "784", "TUN": "788",
    "TUR": "792", "TKM": "795", "TUV": "798", "UGA": "800", "UKR": "804", "MKD": "807",
    "EGY": "818", "GBR": "826", "TZA": "834", "USA": "840", "BFA": "854", "URY": "858",
    "UZB": "860", "VEN": "862", "WSM": "882", "YEM": "887", "ZMB": "894", "KIR": "296",
    "MCO": "492", "LIE": "438",
}


async def sdg_goal_list() -> dict[str, Any]:
    url = f"{SDG_API}/Goal/List?includechildren=false"
    resp = await _get(url)
    return {"goals": resp.json(), "provenance": _stamp("UN DESA Global SDG Indicators Database", url)}
