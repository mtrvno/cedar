#!/usr/bin/env python3
"""CEDAR API server — exposes cedar.py via HTTP for the Vue client (stdlib only, no pip)."""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cedar

PORT = int(os.environ.get("CEDAR_PORT", "8000"))

SDG_META: dict = {
    "child-survival": [
        {"n": 2, "label": "Zero Hunger", "color": "#DDA63A", "weight": 50},
        {"n": 3, "label": "Good Health & Well-being", "color": "#4C9F38", "weight": 50},
    ],
    "economy-poverty": [
        {"n": 1, "label": "No Poverty", "color": "#E5243B", "weight": 55},
        {"n": 8, "label": "Decent Work & Growth", "color": "#A21942", "weight": 45},
    ],
    "education": [
        {"n": 4, "label": "Quality Education", "color": "#C5192D", "weight": 100},
    ],
    "health-system": [
        {
            "n": 3,
            "label": "Good Health & Well-being",
            "color": "#4C9F38",
            "weight": 100,
        },
    ],
    "wash": [
        {
            "n": 6,
            "label": "Clean Water & Sanitation",
            "color": "#26BDE2",
            "weight": 100,
        },
    ],
    "energy-climate": [
        {
            "n": 7,
            "label": "Affordable & Clean Energy",
            "color": "#FDB713",
            "weight": 70,
        },
        {"n": 13, "label": "Climate Action", "color": "#3F7E44", "weight": 30},
    ],
}


def _last_n(obs: dict, n: int = 5) -> list:
    years = sorted(y for y, v in obs.items() if v is not None)
    return [obs[y] for y in years[-n:]]


def _display(val: float) -> str:
    return str(int(val)) if val == int(val) else str(round(val, 2))


def _host(url: str) -> str:
    try:
        return url.split("//", 1)[1].split("/")[0]
    except Exception:
        return "data.worldbank.org"


def _to_scenario(
    packs: list, theme: str, country: str, country_name: str, cost_report: dict
) -> dict:
    kpis, citations, paragraphs, actions = [], [], [], []

    for i, p in enumerate(packs):
        s = p["series"]
        v = p["verify"]
        obs = {y: val for y, val in s["obs"].items() if val is not None}
        if not obs:
            continue

        years = sorted(obs.keys())
        latest_year = years[-1]
        latest_val = obs[latest_year]

        conf_map = {"High": "High", "Medium": "Med", "Low": "Low"}

        kpis.append(
            {
                "indicator": cedar.CATALOG[s["indicator_code"]]["name"],
                "value": _display(latest_val),
                "unit": s["unit"],
                "year": str(latest_year),
                "confidence": conf_map.get(v["confidence_tier"], "Low"),
                "source": s["provenance"]["upstream_source"],
                "values": _last_n(obs),
            }
        )

        cite_n = i + 1
        citations.append(
            {
                "n": cite_n,
                "text": (
                    f"{s['provenance']['upstream_source']} — "
                    f"{cedar.CATALOG[s['indicator_code']]['name']} ({latest_year})."
                ),
                "host": _host(s["provenance"]["query_url"]),
            }
        )

        if p["claims"]:
            paragraphs.append({"text": p["claims"][0]["text"], "cite": cite_n})
            if len(p["claims"]) > 1:
                paragraphs.append({"text": p["claims"][1]["text"], "cite": cite_n})

    if kpis:
        actions.append(
            {
                "text": (
                    f"Review {cedar.THEMES[theme]['label'].split('(')[0].strip()} "
                    f"indicators against SDG targets for {country_name}."
                ),
                "cites": [1],
            }
        )
        if len(kpis) > 1:
            actions.append(
                {
                    "text": f"Cross-reference {len(kpis)} tracked indicators to identify compounding risks.",
                    "cites": list(range(1, len(kpis) + 1)),
                }
            )

    theme_short = cedar.THEMES[theme]["label"].split(" (")[0]
    return {
        "key": f"{country}_{theme}",
        "title": f"{theme_short} — {country_name}",
        "contextLabel": f"{country_name} · {theme_short}",
        "query": f"What is the state of {cedar.THEMES[theme]['label'].lower()} in {country_name}?",
        "domain": theme,
        "country": country,
        "countryName": country_name,
        "tokens": {"in": 0, "out": cost_report.get("cedar_llm_cost_usd", 0)},
        "sdgs": SDG_META.get(theme, []),
        "kpis": kpis,
        "citations": citations,
        "paragraphs": paragraphs,
        "actions": actions,
        "cost_report": cost_report,
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"  [api] {args[0]} {args[1]}")

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def send_json(self, data, status: int = 200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        def q(key, default=""):
            return qs.get(key, [default])[0]

        if parsed.path == "/api/health":
            self.send_json({"status": "ok"})

        elif parsed.path == "/api/themes":
            self.send_json(
                {
                    "themes": [
                        {"key": k, "label": v["label"]} for k, v in cedar.THEMES.items()
                    ]
                }
            )

        elif parsed.path == "/api/brief":
            country = (q("country") or "KEN").upper()
            theme = q("theme") or "child-survival"
            offline = q("offline", "false").lower() in ("1", "true", "yes")

            if theme not in cedar.THEMES:
                self.send_json({"error": f"Unknown theme '{theme}'"}, 400)
                return
            try:
                meter = cedar.CostMeter()
                retr = cedar.Retriever(meter, offline=offline)
                verifier = cedar.Verifier()
                analyst = cedar.Analyst(retr.cache)
                spec = cedar.THEMES[theme]
                comparator = (
                    retr.fetch(spec["headline"], spec["comparator"])
                    if spec.get("comparator")
                    else None
                )

                packs = []
                for code in spec["indicators"]:
                    series = retr.fetch(code, country)
                    if not series:
                        continue
                    verify = verifier.assess(series)
                    comp = comparator if code == spec["headline"] else None
                    claims = analyst.analyse(series, comparator=comp)
                    packs.append({"series": series, "verify": verify, "claims": claims})

                if not packs:
                    self.send_json({"error": f"No data for {country}/{theme}"}, 404)
                    return

                country_name = packs[0]["series"]["ref_area_name"]
                self.send_json(
                    _to_scenario(packs, theme, country, country_name, meter.report())
                )

            except Exception as e:
                self.send_json({"error": str(e)}, 500)

        elif parsed.path == "/api/polycrisis":
            country = (q("country") or "KEN").upper()
            offline = q("offline", "false").lower() in ("1", "true", "yes")
            try:
                self.send_json(cedar.run_polycrisis(country, offline=offline))
            except Exception as e:
                self.send_json({"error": str(e)}, 500)

        else:
            self.send_json({"error": "Not found"}, 404)


class ReuseServer(HTTPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    server = ReuseServer(("0.0.0.0", PORT), Handler)
    print(f"CEDAR API  →  http://localhost:{PORT}")
    print(f"  GET /api/themes")
    print(f"  GET /api/brief?country=KEN&theme=child-survival[&offline=true]")
    print(f"  GET /api/polycrisis?country=KEN[&offline=true]")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
