"""ChildSight MCP — from live crisis signals to child-centered, SDG-linked evidence.

Tools are designed around DECISION QUESTIONS, not raw data access:
  1. get_active_crises        — what is happening right now? (GDACS + EONET)
  2. get_child_risk_profile   — how vulnerable are children where it's happening? (UNICEF CCRI)
  3. get_sdg_baseline         — what does the official evidence say? (DESA SDG API)
  4. assess_crisis_impact     — THE FUSION: event × child vulnerability × SDG baseline
  5. compare_active_crises    — which crisis should we prioritize? (ranked severity)
  6. generate_situation_brief — decision-ready, fully-sourced brief (USG-policy style)

Every response carries provenance (source, url, retrieved_at). No invented values.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from . import clients
from .clients import EVENT_TO_SDG, GDACS_TO_CCRI

mcp = FastMCP(
    "childsight",
    instructions=(
        "ChildSight fuses live disaster data (GDACS, NASA EONET) with UNICEF child "
        "vulnerability indices (CCRI) and official UN SDG indicators (DESA) to produce "
        "decision-ready evidence. Always cite the provenance blocks returned by tools. "
        "Never state a number that did not come from a tool response."
    ),
)


def _j(obj: Any) -> str:
    return json.dumps(obj, indent=2, default=str)


def _aslist(value: Any) -> list[str] | None:
    """Some MCP clients send list params as JSON strings ('[\"Green\"]'). Coerce."""
    if value is None or isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except ValueError:
            pass
        return [v.strip() for v in value.split(",") if v.strip()]
    return [str(value)]


# ------------------------------------------------------------------ 1. events

@mcp.tool()
async def get_active_crises(
    alert_levels: list[str] | None = None,
    event_types: list[str] | None = None,
    include_eonet: bool = False,
) -> str:
    """List active disasters worldwide, right now.

    Args:
        alert_levels: Filter GDACS alerts, e.g. ["Orange", "Red"]. Default: all.
        event_types: Filter by type: EQ, TC (cyclone), FL (flood), VO, DR (drought), WF (wildfire).
        include_eonet: Also include NASA EONET satellite-observed events (wildfires, storms, volcanoes).
    """
    gdacs = await clients.gdacs_events(_aslist(alert_levels), _aslist(event_types))
    result: dict[str, Any] = {"gdacs": gdacs}
    if include_eonet:
        try:
            result["eonet"] = await clients.eonet_events(limit=30)
        except Exception as e:  # EONET occasionally slow; degrade gracefully
            result["eonet"] = {"error": f"EONET unavailable: {e}"}
    return _j(result)


# ------------------------------------------------- 2. child vulnerability

@mcp.tool()
async def get_child_risk_profile(iso3: str) -> str:
    """UNICEF Children's Climate Risk Index profile for a country: per-hazard
    exposure scores (floods, cyclones, heatwaves, water scarcity, disease) and
    child vulnerability pillars (health, nutrition, WASH, education, poverty),
    each 0-10 with named data sources.

    Args:
        iso3: ISO3 country code, e.g. "KEN", "PHL", "BGD".
    """
    return _j(await clients.unicef_ccri(iso3))


@mcp.tool()
async def get_child_population(iso3: str) -> str:
    """Under-18 population for a country (UNICEF demography data).

    Args:
        iso3: ISO3 country code.
    """
    return _j(await clients.unicef_child_population(iso3))


# ------------------------------------------------------ 3. SDG baseline

@mcp.tool()
async def get_sdg_baseline(series_code: str, area_code: str) -> str:
    """Official SDG indicator values from the UN DESA Global SDG Database,
    with nature codes (Country-reported/Estimated/Modeled), official source,
    and footnotes.

    Args:
        series_code: DESA series code, e.g. "SI_POV_DAY1" (extreme poverty),
            "SH_DYN_MORT" (under-5 mortality), "SN_ITK_DEFC" (undernourishment).
        area_code: UN M49 numeric area code, e.g. "404" for Kenya, "608" Philippines.
    """
    return _j(await clients.sdg_series_data(series_code, area_code))


# ------------------------------------------------------------ 4. THE FUSION

async def _impact_for_event(event: dict[str, Any]) -> dict[str, Any]:
    iso3 = (event.get("iso3") or "").strip()
    etype = event.get("type", "")
    assessment: dict[str, Any] = {"event": event}

    if not iso3 or len(iso3) != 3:
        assessment["note"] = "No ISO3 country code on event; cannot join vulnerability data."
        return assessment

    ccri_task = clients.unicef_ccri(iso3)
    pop_task = clients.unicef_child_population(iso3)
    ccri, pop = await asyncio.gather(ccri_task, pop_task, return_exceptions=True)

    if isinstance(ccri, Exception):
        assessment["child_risk"] = {"error": str(ccri)}
    else:
        relevant_codes = set(GDACS_TO_CCRI.get(etype, []))
        relevant_codes |= {"CCRI_CHLD_VULNERABILITY", "CCRI_CHLD_CLIMATE_ENV_RISK_INDEX"}
        assessment["child_risk"] = {
            "country": ccri.get("country"),
            "hazard_specific": [i for i in ccri.get("indicators", []) if i["code"] in relevant_codes],
            "provenance": ccri.get("provenance"),
        }

    if isinstance(pop, Exception):
        assessment["child_population"] = {"error": str(pop)}
    else:
        assessment["child_population"] = pop

    assessment["threatened_sdg_indicators"] = [
        {"indicator": code, "name": name} for code, name in EVENT_TO_SDG.get(etype, [])
    ]
    return assessment


@mcp.tool()
async def assess_crisis_impact(gdacs_event_id: str) -> str:
    """Fuse a live GDACS event with UNICEF child vulnerability data and the SDG
    framework: which children are exposed, how vulnerable they are to THIS hazard
    type, and which SDG indicators are threatened. Every value is sourced.

    Args:
        gdacs_event_id: GDACS event id from get_active_crises.
    """
    gdacs = await clients.gdacs_events()
    match = next((e for e in gdacs["events"] if str(e.get("event_id")) == str(gdacs_event_id)), None)
    if not match:
        return _j({"error": f"Event {gdacs_event_id} not found in current GDACS list",
                   "hint": "Call get_active_crises first and use a current event_id."})
    return _j(await _impact_for_event(match))


# ------------------------------------------------------------ 5. compare

@mcp.tool()
async def compare_active_crises(alert_levels: list[str] | None = None, top_n: int = 5) -> str:
    """Rank current crises by child-centered severity: GDACS alert score ×
    country child vulnerability (CCRI). Answers: 'where should we look first?'

    Args:
        alert_levels: e.g. ["Orange", "Red"]. Default: ["Orange", "Red"].
        top_n: How many top-ranked crises to assess in detail.
    """
    levels = _aslist(alert_levels) or ["Orange", "Red"]
    gdacs = await clients.gdacs_events(alert_levels=levels)
    events = [e for e in gdacs["events"] if e.get("iso3") and len(e["iso3"].strip()) == 3]

    # Fetch CCRI composite per candidate country: deduped, concurrency-capped
    # (UNICEF SDMX throttles bursts), capped at 15 countries per call so the
    # tool always returns within the MCP client's timeout.
    MAX_COUNTRIES = 15
    iso3s = sorted({e["iso3"].strip() for e in events})
    skipped_countries = iso3s[MAX_COUNTRIES:]
    iso3s = iso3s[:MAX_COUNTRIES]
    profiles = await clients.gather_limited(
        (clients.unicef_ccri(i) for i in iso3s), limit=4, per_task_timeout=15.0)
    composite: dict[str, float | None] = {}
    unresolved: list[str] = []
    for iso3, prof in zip(iso3s, profiles):
        if isinstance(prof, BaseException):
            composite[iso3] = None
            unresolved.append(iso3)
            continue
        score = next((i.get("score") for i in prof.get("indicators", [])
                      if i["code"] == "CCRI_CHLD_CLIMATE_ENV_RISK_INDEX"), None)
        composite[iso3] = score

    alert_weight = {"Green": 1.0, "Orange": 2.0, "Red": 3.0}
    ranked = []
    for e in events:
        ccri = composite.get(e["iso3"].strip())
        priority = round(alert_weight.get(e["alert_level"], 1.0) * (ccri if ccri is not None else 5.0), 2)
        ranked.append({**e, "ccri_composite": ccri, "child_priority_score": priority,
                       "scoring": "GDACS alert weight (1-3) x CCRI composite (0-10); CCRI missing -> neutral 5.0"})
    ranked.sort(key=lambda x: x["child_priority_score"], reverse=True)

    result: dict[str, Any] = {
        "ranked_crises": ranked[:top_n],
        "total_considered": len(ranked),
        "method": "Transparent heuristic, not an official severity metric. All inputs sourced.",
        "provenance": [gdacs["provenance"], {"source": "UNICEF CCRI", "note": "composite per country"}],
    }
    if unresolved:
        result["ccri_unresolved"] = {
            "countries": unresolved,
            "note": "CCRI lookup failed/timed out for these; their events were ranked with a neutral 5.0. Retry, or call get_child_risk_profile individually.",
        }
    if skipped_countries:
        result["countries_not_assessed"] = {
            "countries": skipped_countries,
            "note": f"More than {MAX_COUNTRIES} countries in scope; these were skipped to stay within time budget. Narrow with alert_levels or event filters.",
        }
    return _j(result)


# ------------------------------------------------------------ 6. brief

@mcp.tool()
async def generate_situation_brief(gdacs_event_id: str) -> str:
    """Produce the structured evidence pack for a decision-ready situation brief
    (USG-policy style): event facts, exposed children, hazard-specific child
    vulnerability, threatened SDG indicators with official baselines, and a
    complete source list. The calling LLM should format this as a brief and
    MUST only use values present in this response.

    Args:
        gdacs_event_id: GDACS event id from get_active_crises.
    """
    gdacs = await clients.gdacs_events()
    match = next((e for e in gdacs["events"] if str(e.get("event_id")) == str(gdacs_event_id)), None)
    if not match:
        return _j({"error": f"Event {gdacs_event_id} not found in current GDACS list"})

    impact = await _impact_for_event(match)

    # Pull official SDG baselines for the top threatened indicators (best effort)
    baselines = []
    series_map = {"1.5.1": "VC_DSR_MTMP", "3.2.1": "SH_DYN_MORT", "2.2.1": "SH_STA_STNT",
                  "6.1.1": "SP_ACS_BSRVH2O", "2.1.2": "AG_PRD_FIESMS"}
    area = clients.ISO3_TO_M49.get((match.get("iso3") or "").strip().upper())
    if area:
        for t in impact.get("threatened_sdg_indicators", [])[:3]:
            series = series_map.get(t["indicator"])
            if not series:
                continue
            try:
                baselines.append(await clients.sdg_series_data(series, area, page_size=1))
            except Exception as e:
                baselines.append({"series": series, "error": str(e)})

    sources = [impact.get("child_risk", {}).get("provenance"),
               impact.get("child_population", {}).get("provenance"),
               gdacs["provenance"],
               *[b.get("provenance") for b in baselines if isinstance(b, dict)]]

    return _j({
        "brief_structure": [
            "1. SITUATION — event facts", "2. CHILDREN EXPOSED — population + vulnerability",
            "3. SDG IMPACT — threatened indicators vs official baselines",
            "4. EVIDENCE GAPS — what we do not know", "5. SOURCES",
        ],
        "situation": match,
        "impact_assessment": impact,
        "sdg_baselines": baselines,
        "evidence_gaps": [
            "Subnational exposure not computed (country-level join only)",
            "CCRI reference year 2020-2021; conditions may have changed",
            "Real-time displacement figures not included",
        ],
        "sources": [s for s in sources if s],
    })


# ------------------------------------------------------------ 7. SDG context

@mcp.tool()
async def get_sdg_context(iso3: str) -> str:
    """Macro SDG country context: latest official value for 17 key indicators
    across 8 SDG goals (poverty, hunger, health, education, gender, water,
    cities, climate). Data from UN DESA Global SDG Indicators Database.
    Use alongside get_child_risk_profile and get_active_crises to understand
    the baseline conditions a crisis hits.

    Args:
        iso3: ISO3 country code, e.g. "KEN", "HTI", "PHL".
    """
    return _j(await clients.sdg_country_context(iso3))


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
