# ChildSight MCP

**From data to action:** an MCP server that fuses live crisis signals with UNICEF child-vulnerability data and official UN SDG indicators, turning the world's most valuable public data into decision-ready, fully-sourced evidence.

> CCRI tells you which children are at risk *in general*.
> ChildSight tells you which children are at risk **right now**.

## Why this isn't "another API wrapper"

Existing MCP servers give LLMs access to single datasets. ChildSight's tools answer **decision questions** by joining sources no one joins today:

```
GDACS live event (what's happening, where, how severe)
   × UNICEF CCRI (how vulnerable are children to THIS hazard, there)
   × UNICEF Demography (how many children)
   × DESA SDG Database (which official indicators are threatened, baselines)
   = sourced situation brief in seconds, not days
```

All four APIs: public, keyless, verified live (see `../api-verification.md`).

## Tools

| Tool | Decision question |
|---|---|
| `get_active_crises` | What is happening right now? (GDACS + NASA EONET) |
| `get_child_risk_profile` | How vulnerable are children in country X? (CCRI, 27 indicators) |
| `get_child_population` | How many children are there? |
| `get_sdg_baseline` | What does the official evidence say? (DESA, with nature codes) |
| `assess_crisis_impact` | **Fusion**: event × child vulnerability × SDG framework |
| `compare_active_crises` | Which crisis should we prioritize? (transparent ranking) |
| `generate_situation_brief` | Decision-ready evidence pack, USG-policy-brief style |

## Anti-hallucination by design

- Every tool response carries `provenance` (source, URL, retrieval timestamp)
- DESA values include official **nature codes** (Country-reported / Estimated / Modeled) and footnotes
- Server instructions forbid the LLM from stating numbers not present in tool output
- Briefs include an explicit **EVIDENCE GAPS** section — saying what we *don't* know is part of trustworthy evidence

## Quickstart

```bash
cd childsight-mcp
conda create -n childsight python=3.11 -y
conda activate childsight
pip install -e .   # installs mcp + requests into the conda env
```

(Plain pip/venv works too: `pip install -e .`)

Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "childsight": {
      "command": "/path/to/anaconda3/envs/childsight/bin/python",
      "args": ["-m", "childsight.server"],
      "cwd": "/path/to/childsight-mcp/src"
    }
  }
}
```

Use the conda env's full python path (`conda activate childsight && which python` to find it) — Claude Desktop doesn't inherit your shell's conda activation.

Or run directly: `python -m childsight.server` (stdio transport).

## Demo script (60 seconds)

1. *"What crises are active right now that most threaten children?"*
   → `compare_active_crises` ranks live events by GDACS alert × CCRI child vulnerability
2. *"Generate a situation brief for the top one."*
   → `generate_situation_brief` returns the full sourced evidence pack
3. The LLM formats it as a UN-style brief — every number traceable, gaps declared.

## Demo-day resilience

- **In-memory cache** (10 min TTL) — repeated tool calls during a demo are instant
- **Automatic retry** — one retry with backoff on any API hiccup
- **Offline snapshot fallback** — run `python scripts/capture_demo_snapshots.py` on demo morning; if venue wifi dies, the server serves the snapshots and provenance honestly reports `"served": "snapshot (captured ...)"` instead of pretending it's live

## Data sources

- [GDACS](https://www.gdacs.org) — UN OCHA / EC JRC disaster alerts
- [NASA EONET](https://eonet.gsfc.nasa.gov) — satellite-observed natural events
- [UNICEF Data Warehouse (SDMX)](https://sdmx.data.unicef.org) — CCRI, demography, nutrition, conflict exposure
- [UN DESA Global SDG Indicators Database](https://unstats.un.org/sdgapi/swagger/) — official SDG series

## Roadmap

- Subnational exposure via WorldPop raster overlay (event polygon → child population)
- HDX joins: food insecurity (IPC), displacement (IDMC/UNHCR)
- GDACS webhook streaming for push alerts
- CCRI-DRM subnational risk model integration
