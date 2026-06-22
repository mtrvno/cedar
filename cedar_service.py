"""
CEDAR service layer — pure, framework-free functions that return JSON-ready dicts.
Reuses the deterministic engine in cedar.py (Retriever / Verifier / Analyst), so the
API and the CLI share one source of truth. No FastAPI here, so this module is unit-testable.
"""
import json
import os
import urllib.request
from collections import Counter
import cedar

CACHE = json.load(open(cedar.CACHE_PATH))
CCRI = json.load(open(os.path.join(cedar.HERE, "data", "ccri.json"), encoding="utf-8"))
_GDACS_SNAPSHOT_PATH = os.path.join(cedar.HERE, "data", "gdacs_snapshot.json")

# ----------------------------------------------------------------------------- helpers
def _engine(offline):
    meter = cedar.CostMeter()
    return cedar.Retriever(meter, offline=offline), cedar.Verifier(), cedar.Analyst(CACHE), meter

def _latest(obs):
    pts = {int(y): v for y, v in obs.items() if v is not None}
    if not pts:
        return None, None
    ly = max(pts); return ly, pts[ly]

# ----------------------------------------------------------------------------- metadata
def catalog():
    return {
        "themes": {k: {"label": v["label"], "indicators": v["indicators"],
                       "headline": v["headline"], "comparator": v.get("comparator")}
                   for k, v in cedar.THEMES.items()},
        "indicators": {c: {"name": m["name"], "unit": m["unit"], "better": m["better"], "lineage": m["lineage"]}
                       for c, m in cedar.CATALOG.items()},
        "sdg_targets": CACHE.get("sdg_targets", {}),
        "polycrisis_domains": [{"domain": d, "indicator": c} for d, c in cedar.POLYCRISIS_DOMAINS],
        "source": CACHE.get("_meta", {}),
    }

def countries():
    seen = {}
    for s in CACHE["series"]:
        seen.setdefault(s["ref_area"], s["ref_area_name"])
    return [{"iso3": k, "name": v} for k, v in sorted(seen.items(), key=lambda kv: kv[1])]

# ----------------------------------------------------------------------------- data
def series(country, code, offline=False):
    retr, *_ = _engine(offline)
    s = retr.fetch(code, country)
    if not s:
        return None
    return {"country": country, "indicator_code": code, "indicator_name": s["indicator_name"],
            "unit": s["unit"], "ref_area_name": s["ref_area_name"], "obs": s["obs"],
            "provenance": s["provenance"]}

# ----------------------------------------------------------------------------- live disaster x child-risk (GDACS x CCRI)
# GDACS = Global Disaster Alert and Coordination System (UN/EC). Its alert COLOR (Green/Orange/Red)
# reflects hazard magnitude, exposed population, and a GENERIC vulnerability proxy (INFORM/HDI) -
# it is NOT weighted for child-specific vulnerability. UNICEF's CCRI is. So a Green/Orange alert
# (graded low/medium priority) that lands on an "extremely high" CCRI country (score > 7) is an
# "underestimated" signal: children are highly exposed/vulnerable even though the hazard triage is low.
GDACS_URL = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/EVENTS4APP"
EVENT_TYPES = {"EQ": "Earthquake", "TC": "Tropical cyclone", "FL": "Flood", "DR": "Drought",
               "VO": "Volcano", "WF": "Wildfire", "VW": "Severe weather"}
HIGH_CCRI = CCRI.get("extremely_high_threshold", 7.0)
# name -> ISO3 fallback for events GDACS leaves un-coded but names a single country
_NAME2ISO = {v["name"].lower(): k for k, v in CCRI["countries"].items()}
_NAME2ISO.update({"democratic republic of the congo": "COD", "dr congo": "COD", "tanzania": "TZA",
                  "republic of korea": "KOR", "south korea": "KOR", "north korea": "PRK",
                  "iran": "IRN", "syria": "SYR", "bolivia": "BOL", "venezuela": "VEN",
                  "laos": "LAO", "moldova": "MDA", "russia": "RUS", "vietnam": "VNM"})

def ccri_country(iso3):
    """CCRI record for one ISO3 (or None)."""
    c = CCRI["countries"].get((iso3 or "").upper())
    return ({"iso3": iso3.upper(), **c} if c else None)

def ccri_all():
    """The full grounded CCRI table + metadata (deterministic, $0)."""
    return CCRI

def _gdacs_severity(p):
    sd = p.get("severitydata")
    if isinstance(sd, dict):
        return sd.get("severity"), sd.get("severitytext")
    return p.get("severity"), p.get("severitytext")

def _normalize_gdacs(features):
    out = []
    for f in features:
        p = f.get("properties", {}) or {}
        g = f.get("geometry") or {}
        iso = (p.get("iso3") or "").strip().upper()
        if not iso:  # try a single-country name match
            nm = (p.get("country") or "").strip().lower()
            if "," not in nm:
                iso = _NAME2ISO.get(nm, "")
        sev, sevtext = _gdacs_severity(p)
        url = p.get("url")
        if isinstance(url, dict):
            url = url.get("report") or url.get("details")
        out.append({
            "id": p.get("eventid"), "episode": p.get("episodeid"),
            "type": p.get("eventtype"), "type_name": EVENT_TYPES.get(p.get("eventtype"), p.get("eventtype")),
            "alertlevel": p.get("alertlevel"), "alertscore": p.get("alertscore"),
            "country": p.get("country"), "iso3": iso, "name": p.get("name"),
            "severity": sev, "severity_text": sevtext,
            "from": p.get("fromdate"), "to": p.get("todate"),
            "coordinates": (g.get("coordinates") if g else None), "url": url,
        })
    return out

def _fetch_gdacs(offline):
    """Returns (events, provenance). Live via urllib; bundled snapshot on offline/failure."""
    if not offline:
        try:
            req = urllib.request.Request(GDACS_URL, headers={"User-Agent": "CEDAR/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.loads(r.read().decode("utf-8"))
            feats = data.get("features", []) or []
            return _normalize_gdacs(feats), {
                "mode": "live", "source": GDACS_URL, "retrieved": cedar.now_iso(), "count": len(feats)}
        except Exception as e:  # network blocked / GDACS down -> fall back
            snap = json.load(open(_GDACS_SNAPSHOT_PATH, encoding="utf-8"))
            return snap["events"], {"mode": "offline-snapshot", "source": snap.get("source"),
                                    "retrieved": snap.get("retrieved"), "count": len(snap["events"]),
                                    "note": "live GDACS fetch failed (%s); using bundled snapshot" % e.__class__.__name__}
    snap = json.load(open(_GDACS_SNAPSHOT_PATH, encoding="utf-8"))
    return snap["events"], {"mode": "offline-snapshot", "source": snap.get("source"),
                            "retrieved": snap.get("retrieved"), "count": len(snap["events"]),
                            "note": "offline mode; using bundled snapshot"}

def gdacs(offline=False):
    """All current GDACS alerts, each enriched with the affected country's CCRI (deterministic, $0)."""
    events, prov = _fetch_gdacs(offline)
    for e in events:
        e["ccri"] = ccri_country(e.get("iso3"))
    return {"generated_at": cedar.now_iso(), "provenance": prov, "n_events": len(events),
            "events": events, "ccri_source": CCRI["source"]}

def climate_risk(offline=False, levels=("Green", "Orange")):
    """Join live GDACS alerts to UNICEF CCRI and surface 'underestimated' alerts: low/medium-priority
    (Green/Orange) hazards striking 'extremely high' child-risk countries (CCRI > 7). Returns a global
    scope, the flagged alerts, and a ranked 'where to focus' country list. Deterministic, cited, $0."""
    g = gdacs(offline)
    events = g["events"]
    levels = tuple(levels)

    by_level = Counter(e.get("alertlevel") for e in events if e.get("alertlevel"))
    by_type = Counter(e.get("type_name") for e in events if e.get("type_name"))
    coded = [e for e in events if e.get("ccri")]

    flagged, focus = [], {}
    for e in events:
        cc = e.get("ccri")
        if not cc or e.get("alertlevel") not in levels or cc["ccri"] <= HIGH_CCRI:
            continue
        item = {"id": e["id"], "type_name": e["type_name"], "alertlevel": e["alertlevel"],
                "country": e["country"], "iso3": e["iso3"], "severity": e.get("severity"),
                "severity_text": e.get("severity_text"), "from": e.get("from"), "url": e.get("url"),
                "ccri": cc["ccri"], "exposure": cc["exposure"], "vulnerability": cc["vulnerability"],
                "tier": cc["tier"],
                "why": ("GDACS graded this %s (low/medium priority), but %s is an 'extremely high' child-risk "
                        "country (CCRI %.1f/10; child-vulnerability %.1f/10) - children's exposure is likely "
                        "underestimated by the hazard-only alert."
                        % (e["alertlevel"], cc["name"], cc["ccri"], cc["vulnerability"]))}
        flagged.append(item)
        f = focus.setdefault(e["iso3"], {
            "iso3": e["iso3"], "country": cc["name"], "ccri": cc["ccri"], "exposure": cc["exposure"],
            "vulnerability": cc["vulnerability"], "tier": cc["tier"], "n_alerts": 0,
            "alert_levels": set(), "hazards": set(), "max_severity": None, "alert_ids": []})
        f["n_alerts"] += 1
        f["alert_levels"].add(e["alertlevel"])
        f["hazards"].add(e["type_name"])
        f["alert_ids"].append(e["id"])
        if e.get("severity") is not None:
            f["max_severity"] = e["severity"] if f["max_severity"] is None else max(f["max_severity"], e["severity"])

    focus_list = []
    for f in focus.values():
        f["alert_levels"] = sorted(f["alert_levels"])
        f["hazards"] = sorted(f["hazards"])
        focus_list.append(f)
    # rank: highest child-risk first, then most flagged alerts, then any Orange ahead of Green
    focus_list.sort(key=lambda x: (x["ccri"], x["n_alerts"], "Orange" in x["alert_levels"]), reverse=True)

    n_flag = len(flagged)
    headline = ("%d active GDACS alerts worldwide; %d are %s alerts striking 'extremely high' child-risk "
                "countries (CCRI > %g) across %d countries - low-priority hazards where children may be "
                "disproportionately affected." % (len(events), n_flag, "/".join(levels), HIGH_CCRI, len(focus_list)))
    if not n_flag:
        headline = ("%d active GDACS alerts worldwide; none are %s alerts in 'extremely high' child-risk "
                    "countries right now." % (len(events), "/".join(levels)))

    return {
        "generated_at": cedar.now_iso(),
        "provenance": g["provenance"],
        "method": {
            "definition": "underestimated = GDACS alertlevel in %s AND country CCRI > %g" % (list(levels), HIGH_CCRI),
            "rationale": ("GDACS alert colour reflects hazard magnitude, exposed population and a generic "
                          "vulnerability proxy - not child-specific vulnerability. UNICEF's CCRI captures "
                          "children's exposure and vulnerability. Their intersection flags places where a "
                          "hazard-only triage may under-serve children."),
            "ccri_threshold": HIGH_CCRI,
            "limitations": ("Alerts without an ISO3 country code (e.g. open-ocean or some multi-country events) "
                            "cannot be joined to CCRI and are excluded from the flagged set. CCRI is a 2021 "
                            "static index covering 163 countries; some small states are unscored."),
        },
        "global_scope": {
            "total_alerts": len(events),
            "by_alert_level": dict(by_level),
            "by_hazard_type": dict(by_type),
            "alerts_with_ccri": len(coded),
            "flagged_alerts": n_flag,
            "focus_countries": len(focus_list),
        },
        "headline": headline,
        "underestimated_alerts": flagged,
        "where_to_focus": focus_list,
        "sources": [CCRI["source"],
                    {"name": "GDACS - Global Disaster Alert and Coordination System (UN OCHA / European Commission)",
                     "data": GDACS_URL, "site": "https://www.gdacs.org"}],
        "disclaimer": "Not an official United Nations product.",
    }

# ----------------------------------------------------------------------------- procedures (deterministic, $0)
def brief(country, theme, offline=False):
    if theme not in cedar.THEMES:
        return {"error": f"unknown theme '{theme}'", "themes": list(cedar.THEMES)}
    retr, ver, an, meter = _engine(offline)
    spec = cedar.THEMES[theme]
    comparator = retr.fetch(spec["headline"], spec["comparator"]) if spec.get("comparator") else None
    inds = []
    for code in spec["indicators"]:
        s = retr.fetch(code, country)
        if not s or not any(v is not None for v in s["obs"].values()):
            inds.append({"code": code, "name": cedar.CATALOG[code]["name"], "available": False}); continue
        v = ver.assess(s)
        claims = an.analyse(s, comparator=(comparator if code == spec["headline"] else None))
        inds.append({"code": code, "name": cedar.CATALOG[code]["name"], "unit": cedar.CATALOG[code]["unit"],
                     "available": True, "obs": s["obs"], "verification": v, "claims": claims,
                     "provenance": s["provenance"]})
    return {"country": country, "theme": theme, "label": spec["label"],
            "generated_at": cedar.now_iso(), "indicators": inds, "cost": meter.report()}

def drilldown(country, dimension="wealth", offline=False):
    if dimension != "wealth":
        return {"error": f"dimension '{dimension}' not available", "available": ["wealth"]}
    retr, ver, an, meter = _engine(offline)
    avail = CACHE.get("equity", {}).get("available", {})
    if country not in avail:
        return {"error": f"no wealth-disaggregated data for {country}", "available_countries": list(avail)}
    yr = avail[country]; vals = []
    for code, lab in zip(cedar.QUINTILE_CODES, cedar.QUINTILE_LABELS):
        s = retr.fetch(code, country)
        v = None
        if s:
            nn = [x for x in s["obs"].values() if x is not None]
            v = nn[-1] if nn else None
        vals.append({"code": code, "quintile": lab, "value": v,
                     "query_url": s["provenance"]["query_url"] if s else None})
    nat_s = retr.fetch("SH.STA.STNT.ZS", country)
    nat = nat_s["obs"].get(yr, nat_s["obs"].get(str(yr))) if nat_s else None
    q1, q5 = vals[0]["value"], vals[-1]["value"]
    ratio = round(q1 / q5, 2) if (q1 and q5) else None
    gap = round(q1 - q5, 1) if (q1 is not None and q5 is not None) else None
    return {"country": country, "dimension": "wealth_quintile", "indicator": "SH.STA.STNT.ZS",
            "year": yr, "national": nat, "quintiles": vals,
            "ratio_poorest_to_richest": ratio, "gap_points": gap, "cost": meter.report()}

def polycrisis(country, offline=False):
    retr, ver, an, meter = _engine(offline)
    targets = CACHE.get("sdg_targets", {})
    rows = []
    for domain, code in cedar.POLYCRISIS_DOMAINS:
        s = retr.fetch(code, code if False else country)
        if not s:
            rows.append({"domain": domain, "indicator": code, "available": False}); continue
        obs = {int(y): v for y, v in s["obs"].items() if v is not None}
        if not obs:
            rows.append({"domain": domain, "indicator": code, "available": False}); continue
        ys = sorted(obs); first, last = obs[ys[0]], obs[ys[-1]]
        tgt = targets.get(code, {}); better = cedar.CATALOG[code]["better"]
        if tgt.get("target") is not None:
            t, dirn = tgt["target"], tgt["direction"]
            met = (last <= t) if dirn == "below" else (last >= t)
            status = "on-track" if met else "off-track"; bench = t
        else:
            improving = (last < first and better == "lower") or (last > first and better == "higher")
            status = "improving" if improving else "worsening"; bench = None
        v = ver.assess(s)
        rows.append({"domain": domain, "indicator": code, "name": cedar.CATALOG[code]["name"],
                     "unit": cedar.CATALOG[code]["unit"], "available": True, "value": last,
                     "year": ys[-1], "benchmark": bench, "status": status,
                     "stressed": status in ("off-track", "worsening"),
                     "confidence": v["confidence_tier"], "query_url": s["provenance"]["query_url"]})
    scored = [r for r in rows if r.get("available")]
    sN = sum(r["stressed"] for r in scored); n = len(scored)
    band = "high" if sN >= 4 else ("elevated" if sN >= 2 else "lower")
    return {"country": country, "domains": rows, "stressed": sN, "scored": n,
            "band": band, "cost": meter.report()}

def blindspots(country, offline=False, cutoff=2022):
    retr, *_rest, meter = _engine(offline)
    core = sorted({c for sp in cedar.THEMES.values() for c in sp["indicators"]})
    rows = []
    for code in core:
        s = retr.fetch(code, country)
        ly, _ = _latest(s["obs"]) if s else (None, None)
        status = "missing" if ly is None else ("recent" if ly >= cutoff else "stale")
        rows.append({"indicator": code, "name": cedar.CATALOG[code]["name"], "status": status, "latest": ly})
    miss = sum(r["status"] == "missing" for r in rows); stale = sum(r["status"] == "stale" for r in rows)
    rec = sum(r["status"] == "recent" for r in rows)
    return {"country": country, "cutoff": cutoff, "total": len(rows),
            "missing": miss, "stale": stale, "recent": rec, "gaps": miss + stale,
            "indicators": rows, "cost": meter.report()}

def project(country, code, offline=False):
    """Time-to-SDG-target projection for one indicator."""
    retr, *_ = _engine(offline)
    s = retr.fetch(code, country)
    if not s:
        return {"error": "no data", "country": country, "indicator": code}
    obs = {int(y): v for y, v in s["obs"].items() if v is not None}
    tgt = CACHE.get("sdg_targets", {}).get(code, {})
    if not obs or tgt.get("target") is None:
        return {"country": country, "indicator": code, "projectable": False,
                "reason": "no target" if tgt.get("target") is None else "no data"}
    ys = sorted(obs); f0, l0 = ys[0], ys[-1]; v0, v1 = obs[f0], obs[l0]
    t, dirn = tgt["target"], tgt["direction"]
    met = (v1 <= t) if dirn == "below" else (v1 >= t)
    out = {"country": country, "indicator": code, "latest": v1, "latest_year": l0,
           "target": t, "direction": dirn, "met": met, "projectable": True}
    if met:
        out.update(reach_year=l0, years_late=0, note="target already met"); return out
    slope = (v1 - v0) / (l0 - f0) if l0 > f0 else 0.0
    toward = (slope < 0 and dirn == "below") or (slope > 0 and dirn == "above")
    if not toward or abs(slope) < 1e-9:
        out.update(reach_year=None, years_late=None, diverging=True,
                   note="not moving toward target at current pace")
    else:
        reach = round(l0 + (t - v1) / slope)
        out.update(reach_year=reach, years_late=max(0, reach - 2030), diverging=False,
                   on_time=reach <= 2030, note=f"reaches target ~{reach}")
    return out

# ----------------------------------------------------------------------------- interventions (curated, cited synthesis)
EVID_SRC = {"WHO": "https://www.who.int", "Cochrane": "https://www.cochrane.org",
            "J-PAL": "https://www.povertyactionlab.org", "World Bank": "https://www.worldbank.org",
            "ILO": "https://www.ilo.org", "UNICEF": "https://data.unicef.org",
            "UNESCO GEM": "https://www.unesco.org/gem-report", "IEA": "https://www.iea.org",
            "WFP": "https://www.wfp.org", "3ie": "https://www.3ieimpact.org"}
INTERVENTIONS = {
 "child-survival": [
  ("Childhood immunisation programmes", "High", "Among the most cost-effective ways to prevent child deaths.", "WHO"),
  ("Skilled birth attendance & antenatal care", "High", "Reduces neonatal and maternal mortality.", "WHO"),
  ("Insecticide-treated nets & malaria control", "High", "Large reductions in child mortality in endemic settings.", "Cochrane"),
  ("Oral rehydration & zinc for diarrhoea", "High", "Cheap, proven reduction in diarrhoeal deaths.", "UNICEF"),
  ("Exclusive breastfeeding promotion", "Moderate", "Improves infant survival; effect varies by setting.", "WHO"),
  ("Conditional cash transfers", "Moderate", "Improve care-seeking & nutrition; context-dependent.", "J-PAL")],
 "economy-poverty": [
  ("Cash transfers & social protection", "High", "Robust evidence for reducing poverty and vulnerability.", "World Bank"),
  ("Skills training + apprenticeships", "Moderate", "Best when demand-led and employer-linked (youth).", "ILO"),
  ("Active labour-market programmes", "Moderate", "Job-search & matching help; effects modest on average.", "J-PAL"),
  ("Wage / hiring subsidies", "Moderate", "Can boost youth hiring; risk of displacement.", "ILO"),
  ("Entrepreneurship grants", "Moderate", "Help microenterprises; mixed on sustained jobs.", "J-PAL"),
  ("Digital inclusion / connectivity", "Limited", "Promising but thin causal evidence for jobs so far.", "World Bank")],
 "education": [
  ("Structured pedagogy & teacher coaching", "High", "Consistent gains in learning outcomes.", "UNESCO GEM"),
  ("Teaching at the right level", "High", "Strong, replicated learning gains.", "J-PAL"),
  ("School feeding", "Moderate", "Improves attendance & nutrition; learning effects vary.", "WFP"),
  ("Cash transfers for enrolment", "Moderate", "Raise enrolment & attendance.", "World Bank"),
  ("Reducing class size", "Limited", "Costly; inconsistent effects on learning.", "3ie")],
 "health-system": [
  ("Emergency obstetric care", "High", "Core to cutting maternal deaths.", "WHO"),
  ("Skilled birth attendance", "High", "Reduces maternal & neonatal mortality.", "WHO"),
  ("Community health workers", "Moderate", "Extend coverage; quality & support are key.", "WHO"),
  ("Health-financing / UHC reforms", "Moderate", "Improve access; design-dependent.", "World Bank")],
 "wash": [
  ("Improved water supply", "High", "Reduces diarrhoeal disease.", "Cochrane"),
  ("Handwashing / hygiene promotion", "High", "Effective at cutting diarrhoea.", "Cochrane"),
  ("Sanitation (community-led total sanitation)", "Moderate", "Reduces open defecation; effects vary.", "3ie"),
  ("Household water treatment", "Moderate", "Works with sustained use.", "Cochrane")],
 "energy-climate": [
  ("Grid extension / electrification", "High", "Direct gains in access where affordable.", "World Bank"),
  ("Off-grid solar & mini-grids", "Moderate", "Reach remote areas; financing is the constraint.", "IEA"),
  ("Clean cooking programmes", "Moderate", "Health & climate gains; adoption is the challenge.", "WHO"),
  ("Energy-efficiency standards", "Moderate", "Cost-effective emissions cuts.", "IEA")],
}
def interventions(theme):
    if theme not in INTERVENTIONS:
        return {"error": f"unknown theme '{theme}'", "themes": list(INTERVENTIONS)}
    items = [{"name": n, "evidence_strength": s, "rationale": w, "source": src, "source_url": EVID_SRC.get(src, "")}
             for n, s, w, src in INTERVENTIONS[theme]]
    counts = {"High": 0, "Moderate": 0, "Limited": 0}
    for i in items:
        counts[i["evidence_strength"]] += 1
    return {"theme": theme, "counts": counts, "interventions": items,
            "note": "Illustrative evidence synthesis from published reviews by the cited bodies; "
                    "distinct from the live indicator data and not a statistical estimate."}

def interventions_all():
    return {"themes": {t: interventions(t) for t in INTERVENTIONS}}

# ----------------------------------------------------------------------------- evidence chain
EVIDENCE_CHAIN = [
    {"id": "discover", "step": "Discover", "agent": "Agent 1",
     "description": "Resolve indicator & country codes and metadata for the question."},
    {"id": "retrieve", "step": "Retrieve", "agent": "Agent 1",
     "description": "Fetch authoritative series; stamp provenance on every datapoint."},
    {"id": "verify", "step": "Verify", "agent": "Agent 2",
     "description": "Check coverage, recency & data gaps; assign confidence; raise caveats."},
    {"id": "analyse", "step": "Analyse", "agent": "Agent 3",
     "description": "Compute trend, gap-to-target and projection deterministically (no LLM)."},
    {"id": "narrate", "step": "Narrate", "agent": "Agent 4",
     "description": "Render the verified claims to prose; every figure carries a citation."},
    {"id": "review", "step": "Review", "agent": "Agent 5",
     "description": "Refuse to ship any number that lacks a supporting datapoint."},
    {"id": "output", "step": "Output", "agent": "—",
     "description": "Emit the brief + evidence ledger + provenance graph + cost report."},
]

def evidence_chain():
    """The canonical 7-step pipeline definition (static)."""
    return {"steps": EVIDENCE_CHAIN,
            "note": "Every CEDAR output moves through these steps; nothing downstream uses a value an earlier step did not verify."}

def evidence_chain_run(country, theme="child-survival", offline=False):
    """The chain with live per-step status computed from an actual brief run (for the UI stepper)."""
    b = brief(country, theme, offline)
    if "error" in b:
        return b
    avail = [i for i in b["indicators"] if i.get("available")]
    datapoints = sum(len([v for v in i["obs"].values() if v is not None]) for i in avail)
    caveats = sum(len(i["verification"]["caveats"]) for i in avail)
    claims = sum(len(i["claims"]) for i in avail)
    review_ok = all(c.get("datapoints") for i in avail for c in i["claims"])
    detail = {"discover": f"{len(b['indicators'])} indicators",
              "retrieve": f"{datapoints} datapoints",
              "verify": (f"{caveats} caveat(s)" if caveats else "clean"),
              "analyse": f"{claims} claims",
              "narrate": f"{claims} cited",
              "review": "passed" if review_ok else "blocked",
              "output": "ready"}
    steps = [{**s, "status": "done", "detail": detail[s["id"]]} for s in EVIDENCE_CHAIN]
    return {"country": country, "theme": theme, "steps": steps,
            "review_passed": review_ok, "cost": b["cost"]}

# ----------------------------------------------------------------------------- optional LLM (gated by mode in api.py)
CHAT_TOOLS = [
 {"type": "function", "function": {"name": "get_indicator",
   "description": "Authoritative time series for one indicator in one country (World Bank). Returns yearly values, latest, source, query URL.",
   "parameters": {"type": "object", "properties": {
       "iso": {"type": "string", "description": "ISO3 country code, e.g. KEN"},
       "code": {"type": "string", "description": "World Bank indicator code, e.g. SH.DYN.MORT"}}, "required": ["iso", "code"]}}},
 {"type": "function", "function": {"name": "compare_indicator",
   "description": "Compare the latest value of one indicator across several countries.",
   "parameters": {"type": "object", "properties": {
       "isos": {"type": "array", "items": {"type": "string"}}, "code": {"type": "string"}}, "required": ["isos", "code"]}}},
 {"type": "function", "function": {"name": "list_indicators",
   "description": "List the indicator codes CEDAR knows by name.",
   "parameters": {"type": "object", "properties": {}, "required": []}}},
 {"type": "function", "function": {"name": "get_interventions",
   "description": "Effective interventions for a theme, graded by strength of published evidence (High/Moderate/Limited), with sources. Use to answer 'what works'.",
   "parameters": {"type": "object", "properties": {
       "theme": {"type": "string", "enum": list(INTERVENTIONS)}}, "required": ["theme"]}}},
 {"type": "function", "function": {"name": "build_chart",
   "description": "Build a chart spec (render-ready data) to complement the answer with a graph. Provide the indicator/country items to plot. Use a 'line' chart for trends over time and a 'bar' chart for comparing the latest value across countries/indicators.",
   "parameters": {"type": "object", "properties": {
       "kind": {"type": "string", "enum": ["line", "bar"], "description": "line = time series; bar = latest-value comparison"},
       "title": {"type": "string"},
       "items": {"type": "array", "description": "series to plot",
                 "items": {"type": "object", "properties": {"iso": {"type": "string"}, "code": {"type": "string"}},
                           "required": ["iso", "code"]}}},
     "required": ["items"]}}},
]

def _build_chart(args, offline):
    kind = args.get("kind", "line"); title = args.get("title") or ""
    fetched = []
    for it in (args.get("items") or []):
        iso = str(it.get("iso", "")).upper(); code = it.get("code", "")
        s = series(iso, code, offline)
        obs = {int(y): v for y, v in s["obs"].items() if v is not None} if s else {}
        if obs:
            fetched.append({"iso": iso, "code": code, "name": s["indicator_name"], "unit": s["unit"],
                            "country": s["ref_area_name"], "obs": obs, "query_url": s["provenance"]["query_url"]})
    if not fetched:
        return {"error": "no data for requested chart items"}
    same_code = len({f["code"] for f in fetched}) == 1
    label = lambda f: (f["country"] if same_code else f"{f['country']} · {f['name']}")
    spec = {"type": kind, "title": title or fetched[0]["name"], "unit": fetched[0]["unit"],
            "sources": [{"label": f"{f['country']} · {f['name']}", "query_url": f["query_url"]} for f in fetched]}
    if kind == "bar":
        spec["categories"] = [label(f) for f in fetched]
        spec["series"] = [{"label": "latest", "data": [f["obs"][max(f["obs"])] for f in fetched]}]
        spec["years"] = [max(f["obs"]) for f in fetched]
    else:
        years = sorted({y for f in fetched for y in f["obs"]})
        spec["x"] = years
        spec["series"] = [{"label": label(f), "data": [f["obs"].get(y) for y in years]} for f in fetched]
    return spec

def _chat_pack(iso, code, offline, sources):
    s = series(iso, code, offline)
    obs = {int(y): v for y, v in s["obs"].items() if v is not None} if s else {}
    if not obs:
        return {"iso": iso, "code": code, "error": "no data available"}
    ys = sorted(obs)
    p = {"country": s["ref_area_name"], "iso": iso, "code": code, "name": s["indicator_name"],
         "unit": s["unit"], "latest": {"year": ys[-1], "value": obs[ys[-1]]},
         "series": obs, "query_url": s["provenance"]["query_url"]}
    sources.append(p); return p

def _chat_exec(name, args, offline, sources, charts):
    if name == "list_indicators":
        return [{"code": c, "name": cedar.CATALOG[c]["name"], "unit": cedar.CATALOG[c]["unit"]} for c in cedar.CATALOG]
    if name == "get_indicator":
        return _chat_pack(str(args.get("iso", "")).upper(), args.get("code", ""), offline, sources)
    if name == "compare_indicator":
        out = []
        for iso in args.get("isos", []):
            p = _chat_pack(str(iso).upper(), args.get("code", ""), offline, sources)
            out.append({"iso": str(iso).upper(), "latest": p.get("latest"), "error": p.get("error")})
        return {"code": args.get("code"), "results": out}
    if name == "get_interventions":
        return interventions(args.get("theme", ""))
    if name == "build_chart":
        spec = _build_chart(args, offline)
        if "error" in spec:
            return spec
        charts.append(spec)
        # return a compact ack to the model (the full spec is attached to the response, not the prompt)
        return {"ok": True, "type": spec["type"], "title": spec["title"],
                "series": len(spec.get("series", [])), "note": "chart built and attached to the response"}
    return {"error": "unknown tool"}

def _tool_detail(name, res):
    if isinstance(res, dict) and res.get("error"):
        return "no data"
    if name == "get_indicator" and isinstance(res, dict):
        lt = res.get("latest")
        return f"{len(res.get('series', {}))} values · {lt['year']}: {lt['value']}" if lt else "ok"
    if name == "compare_indicator" and isinstance(res, dict):
        return f"{len([x for x in res.get('results', []) if not x.get('error')])} countries"
    if name == "list_indicators":
        return f"{len(res)} indicators"
    if name == "get_interventions" and isinstance(res, dict):
        return f"{len(res.get('interventions', []))} interventions"
    if name == "build_chart" and isinstance(res, dict):
        return f"{res.get('type','?')} chart · {res.get('series',0)} series" if res.get("ok") else "no data"
    return "done"

def _chat_chain(tool_log, sources, final, invented):
    """Build a per-prompt evidence chain reflecting what THIS answer actually did."""
    inds = {s.get("code") for s in sources if s.get("code")}
    ctys = {s.get("iso") for s in sources if s.get("iso")}
    datapoints = sum(len(s.get("series", {})) for s in sources)
    grounded = not invented
    spec = [
        ("discover", "Discover", "Agent 1", "Interpret the prompt; choose indicators/countries to fetch.",
         f"{len(tool_log)} tool call(s) · {len(inds)} indicator(s), {len(ctys)} country(ies)"),
        ("retrieve", "Retrieve", "Agent 1", "Call the World Bank API; stamp provenance on every datapoint.",
         f"{len(sources)} series · {datapoints} datapoints"),
        ("verify", "Verify", "Agent 2", "Confirm the retrieved data is present and usable.",
         f"{len(sources)} grounded source(s)"),
        ("analyse", "Analyse", "Agent 3", "Reason over the retrieved values to address the prompt.",
         "computed from retrieved data"),
        ("narrate", "Narrate", "Agent 4", "Compose the answer, citing each figure.",
         f"{len(final.split())} words"),
        ("review", "Review", "Agent 5", "Number-check the answer against the retrieved data.",
         "passed — all figures grounded" if grounded else f"flagged {len(invented)} unverified figure(s): {', '.join(invented)}"),
        ("output", "Output", "—", "Return the answer with its sources and cost.",
         f"{len(sources)} source(s) cited"),
    ]
    return [{"id": a, "step": b, "agent": c, "description": d,
             "status": "done" if (a != "review" or grounded) else "warn", "detail": e}
            for a, b, c, d, e in spec]

def llm_chat(messages, country, api_key, model="gpt-4o-mini", offline=False, base_url="https://api.openai.com/v1"):
    """Agentic, tool-grounded answer. The model must call tools to obtain any number; the result is
    number-checked against retrieved data. Returns answer + sources + per-prompt evidence chain + cost."""
    import urllib.request
    inds = ", ".join(cedar.CATALOG.keys())
    cmap = "; ".join(f"{c['name']}={c['iso3']}" for c in countries())
    sysmsg = {"role": "system", "content":
        (f"You are CEDAR's evidence assistant, helping a policy analyst explore {country}. "
         "NEVER state a statistic you did not obtain from a tool call; call get_indicator / "
         "compare_indicator first. Name the indicator and year for every figure. If data is "
         "unavailable, say so plainly. Call get_interventions when the user asks what works / what "
         "to do. Call build_chart to attach a graph when a trend or comparison would help (you do not "
         "need to restate the chart's numbers in prose). Be concise. You may use light markdown. "
         f"Known indicator codes: {inds}. Country->ISO3: {cmap}. For other countries/indicators use ISO3 / WB codes.")}
    msgs = [sysmsg] + [{"role": m["role"], "content": m.get("content", "")} for m in messages]
    sources, charts, tool_log, tin, tout, final = [], [], [], 0, 0, ""
    for _ in range(5):
        body = json.dumps({"model": model, "temperature": 0, "messages": msgs,
                           "tools": CHAT_TOOLS, "tool_choice": "auto"}).encode()
        req = urllib.request.Request(base_url.rstrip("/") + "/chat/completions", data=body,
                                     headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read().decode())
        m = data["choices"][0]["message"]; u = data.get("usage", {})
        tin += u.get("prompt_tokens", 0); tout += u.get("completion_tokens", 0)
        tcs = m.get("tool_calls")
        if tcs:
            msgs.append(m)
            for tc in tcs:
                try:
                    args = json.loads(tc["function"].get("arguments") or "{}")
                except Exception:
                    args = {}
                name = tc["function"]["name"]
                res = _chat_exec(name, args, offline, sources, charts)
                tool_log.append({"name": name, "args": args, "detail": _tool_detail(name, res)})
                msgs.append({"role": "tool", "tool_call_id": tc["id"], "content": json.dumps(res)})
            continue
        final = m.get("content") or ""; break
    gstr = json.dumps(sources)
    invented = [n for n in cedar._nums(final) if n not in gstr]
    uniq = {}
    for s in sources:
        uniq[(s.get("iso"), s.get("code"))] = s
    return {"answer": final, "grounded": not invented, "unverified_numbers": invented,
            "sources": [{"country": s.get("country"), "iso": s.get("iso"), "code": s.get("code"),
                         "name": s.get("name"), "latest": s.get("latest"), "query_url": s.get("query_url")}
                        for s in uniq.values()],
            "tool_calls": tool_log, "charts": charts,
            "evidence_chain": _chat_chain(tool_log, sources, final, invented),
            "tokens": {"in": tin, "out": tout}, "model": model}

def llm_summary(claims_text, api_key, model="gpt-4o-mini", base_url="https://api.openai.com/v1"):
    """Guardrailed executive summary. Returns dict; never lets the model invent a number."""
    import urllib.request
    system = ("You are an evidence editor for a UN agency. Rewrite the verified findings into a concise "
              "2-3 sentence executive summary for a policymaker. Use ONLY the facts and numbers given; "
              "never introduce a new number, country, year or claim; never speculate.")
    body = json.dumps({"model": model, "temperature": 0,
                       "messages": [{"role": "system", "content": system},
                                    {"role": "user", "content": claims_text}]}).encode()
    req = urllib.request.Request(base_url.rstrip("/") + "/chat/completions", data=body,
                                 headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=40) as r:
        data = json.loads(r.read().decode())
    text = data["choices"][0]["message"]["content"].strip()
    usage = data.get("usage", {})
    invented = [n for n in cedar._nums(text) if n not in claims_text]
    return {"summary": None if invented else text, "blocked": bool(invented),
            "invented_numbers": invented, "model": model,
            "tokens": {"in": usage.get("prompt_tokens", 0), "out": usage.get("completion_tokens", 0)}}
