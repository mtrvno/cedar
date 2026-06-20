"""Offline tests using fixtures captured from the REAL APIs (verified 2026-06-11/12).

Run: python tests/test_fusion.py  (from childsight-mcp/, with src on PYTHONPATH)
"""

import asyncio
import json
import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Stub the mcp package if not installed (sandbox/CI without PyPI access),
# so the fusion logic in server.py can be tested standalone.
try:
    import mcp.server.fastmcp  # noqa: F401
except ImportError:
    import types

    class _FakeFastMCP:
        def __init__(self, *a, **k): ...
        def tool(self, *a, **k):
            return lambda f: f
        def run(self): ...

    _fastmcp = types.ModuleType("mcp.server.fastmcp")
    _fastmcp.FastMCP = _FakeFastMCP
    _server = types.ModuleType("mcp.server")
    _server.fastmcp = _fastmcp
    _mcp = types.ModuleType("mcp")
    _mcp.server = _server
    sys.modules["mcp"] = _mcp
    sys.modules["mcp.server"] = _server
    sys.modules["mcp.server.fastmcp"] = _fastmcp

from childsight import clients  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(self, text: str):
        self.text = text

    def json(self):
        return json.loads(self.text)

    def raise_for_status(self):
        pass


_sdg_context_fixture: dict | None = None


def _sdg_context_data() -> dict:
    global _sdg_context_fixture
    if _sdg_context_fixture is None:
        _sdg_context_fixture = json.loads((FIXTURES / "sdg_context_ken.json").read_text())
    return _sdg_context_fixture


def fake_get(url: str, params: dict | None = None):
    if "gdacs.org" in url:
        return FakeResponse((FIXTURES / "gdacs_events.json").read_text())
    if "CCRI" in url:
        return FakeResponse((FIXTURES / "ccri_ken.csv").read_text())
    if "UNICEF,DM" in url:
        return FakeResponse((FIXTURES / "dm_ken.csv").read_text())
    if "unstats.un.org" in url:
        # SDG context: per-series fixture keyed by seriesCode param
        series_code = (params or {}).get("seriesCode")
        if series_code and series_code in _sdg_context_data():
            return FakeResponse(json.dumps(_sdg_context_data()[series_code]))
        # Fall back to single-series fixture for existing tests
        return FakeResponse((FIXTURES / "sdg_kenya.json").read_text())
    raise AssertionError(f"unexpected url {url}")


def run(coro):
    return asyncio.run(coro)


def main():
    failures = 0
    with mock.patch.object(clients, "_get_sync", side_effect=fake_get):

        # 1. GDACS parsing — fixture contains TWO episodes of event 1102983;
        # dedup must keep only the latest one
        g = run(clients.gdacs_events(alert_levels=["Red"]))
        assert g["count"] == 1, f"episode dedup failed: {g['count']}"
        ev = g["events"][0]
        assert ev["type"] == "FL" and ev["iso3"] == "KEN" and ev["alert_level"] == "Red"
        assert ev["to_date"] == "2026-06-12T00:00:00", "kept wrong episode"
        assert g["provenance"]["source"].startswith("GDACS")
        print("PASS gdacs_events: parsing, filtering, episode dedup, provenance")

        # 2. CCRI parsing — real Kenya CSV
        c = run(clients.unicef_ccri("KEN"))
        assert c["country"] == "Kenya"
        codes = {i["code"]: i for i in c["indicators"]}
        assert codes["CCRI_FLOODS_RIVERINE"]["score"] == 6.4
        assert codes["CCRI_WASH"]["score"] == 9.7
        assert codes["CCRI_CHLD_CLIMATE_ENV_RISK_INDEX"]["category"] == "High"
        print(f"PASS unicef_ccri: {len(c['indicators'])} indicators, numeric scores extracted")

        # 3. DESA SDG parsing — real Kenya poverty JSON
        s = run(clients.sdg_series_data("SI_POV_DAY1", "404"))
        assert s["data"][0]["area"] == "Kenya"
        assert s["data"][0]["nature"] == "G"
        assert s["data"][0]["official_source"]
        print("PASS sdg_series_data: values + nature codes + official source")

        # 4. Fusion: assess flood event in Kenya
        from childsight import server
        out = json.loads(run(server.assess_crisis_impact("1102983")))
        hz = {i["code"] for i in out["child_risk"]["hazard_specific"]}
        assert "CCRI_FLOODS_RIVERINE" in hz, hz  # flood event -> flood vulnerability joined
        assert "CCRI_CHLD_VULNERABILITY" in hz
        sdgs = {t["indicator"] for t in out["threatened_sdg_indicators"]}
        assert "6.1.1" in sdgs and "3.2.1" in sdgs
        print("PASS assess_crisis_impact: FL event joined to flood-specific CCRI + SDG mapping")

        # 5. Ranking
        rank = json.loads(run(server.compare_active_crises()))
        top = rank["ranked_crises"][0]
        assert top["child_priority_score"] == round(3.0 * 6.3, 2), top  # Red x CCRI 6.3
        print("PASS compare_active_crises: Red-alert Kenya flood ranked with CCRI weighting")

        # 6. Brief evidence pack
        brief = json.loads(run(server.generate_situation_brief("1102983")))
        assert brief["situation"]["event_id"] == 1102983 or str(brief["situation"]["event_id"]) == "1102983"
        assert brief["evidence_gaps"] and brief["sources"]
        assert any(b.get("data") for b in brief["sdg_baselines"] if isinstance(b, dict)), "baselines pulled"
        print("PASS generate_situation_brief: structure, gaps, sources, SDG baselines")

        # 7. SDG country context
        ctx = json.loads(run(server.get_sdg_context("KEN")))
        assert ctx["iso3"] == "KEN"
        assert ctx["m49"] == "404"
        goals = ctx["goals"]
        assert "1_poverty" in goals and "3_health" in goals
        # poverty series present with numeric value
        pov = next((s for s in goals["1_poverty"] if s["series"] == "SI_POV_DAY1"), None)
        assert pov and pov["value"] is not None, f"SI_POV_DAY1 missing or null: {pov}"
        # NaN values from API come back as None, not crash
        food = next((s for s in goals["2_hunger"] if s["series"] == "AG_PRD_FIESMS"), None)
        assert food is not None, "AG_PRD_FIESMS missing from hunger goal"
        # provenance present
        assert ctx["provenance"]["source"].startswith("UN DESA")
        print(f"PASS get_sdg_context: {sum(len(v) for v in goals.values())} series across {len(goals)} goals, NaN safe, provenance ok")

    print("\nAll 7 checks passed — parsing and fusion logic verified against real API fixtures.")
    return failures


if __name__ == "__main__":
    sys.exit(main())
