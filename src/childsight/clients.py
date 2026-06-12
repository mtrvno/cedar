"""HTTP clients for verified public APIs (all keyless, all tested live).

Every function returns data WITH provenance: source, retrieved_at, url.
Anti-hallucination is a design principle: tools never invent values —
if an API returns nothing, the tool says so explicitly.
"""

from __future__ import annotations

import asyncio
import csv
import io
from datetime import datetime, timezone
from typing import Any

import requests

GDACS_EVENTS = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/MAP"
EONET_EVENTS = "https://eonet.gsfc.nasa.gov/api/v3/events"
UNICEF_SDMX = "https://sdmx.data.unicef.org/ws/public/sdmxapi/rest"
SDG_API = "https://unstats.un.org/sdgapi/v1/sdg"

HEADERS = {"User-Agent": "childsight-mcp/0.1 (UN Hackathon 2026)"}
TIMEOUT = 30.0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _stamp(source: str, url: str) -> dict[str, str]:
    return {"source": source, "url": url, "retrieved_at": _now()}


def _get_sync(url: str, params: dict | None = None) -> requests.Response:
    resp = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp


async def _get(url: str, params: dict | None = None) -> requests.Response:
    """Async wrapper: run blocking request in a thread (keeps deps to stdlib + requests)."""
    return await asyncio.to_thread(_get_sync, url, params)


# ---------------------------------------------------------------- GDACS

async def gdacs_events(alert_levels: list[str] | None = None, event_types: list[str] | None = None) -> dict[str, Any]:
    """Live disaster events from GDACS (UN/EC joint system).

    alert_levels: subset of ["Green", "Orange", "Red"]
    event_types: subset of ["EQ", "TC", "FL", "VO", "DR", "WF"]
    """
    resp = await _get(GDACS_EVENTS)
    raw = resp.json()
    features = raw.get("features", [])
    events = []
    for f in features:
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


async def sdg_goal_list() -> dict[str, Any]:
    url = f"{SDG_API}/Goal/List?includechildren=false"
    resp = await _get(url)
    return {"goals": resp.json(), "provenance": _stamp("UN DESA Global SDG Indicators Database", url)}
