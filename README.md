# CEDAR — Cited Evidence & Data Analytic Reporting

**UN Open Source Week Hack-A-Thon 2026 · Challenge 3 (UNICEF Innocenti): Agentic Copilots & Analytic Intelligence**

> Grounded evidence you can trace to the source — at a fraction of the cost.

CEDAR turns a plain-language policy question into a **decision-ready evidence brief where every number is traceable** back to an authoritative API query, through a visible 7-stage evidence chain. Its analytic core runs with **no LLM and no paid API key**, so it works on a zero budget — the direct answer to the challenge's digital-divide concern.

## Quick start (no dependencies)
```bash
python3 cedar.py --country KEN --theme child-survival --offline  # a themed SDG brief, $0.00
python3 cedar.py --country KEN --theme energy-climate --offline  # another SDG theme
python3 cedar.py --country KEN --polycrisis --offline            # cross-SDG composite risk read
python3 cedar.py --country NGA --drilldown wealth --offline      # within-country equity drill-down
python3 cedar.py --list                                          # show all themes + indicators
```

## Themes & briefs (SDG-mapped)
Each theme is a curated set of authoritative indicators with SDG benchmarks; a brief is generated the same grounded way for any of them:

| Theme | SDGs | Headline indicators |
|---|---|---|
| `child-survival` | 2.2, 3.2 | under-5 & infant mortality, DPT immunization, stunting |
| `economy-poverty` | 1, 8 | poverty rate ($3.00/day), GDP per capita, unemployment |
| `education` | 4 | primary completion rate |
| `health-system` | 3 | life expectancy, maternal mortality, under-5 mortality |
| `wash` | 6 | basic drinking-water & sanitation coverage |
| `energy-climate` | 7, 13 | electricity access, renewable share, CO₂ per capita |
| `--polycrisis` | cross-cutting | one headline per domain → a single country risk read (e.g. Kenya: **5 of 7 fronts off-track → HIGH stress**) |

Adding a theme or indicator is a catalog edit (`THEMES` + `CATALOG` in `cedar.py`, plus a cache/API entry) — not new architecture. Coverage varies by SDG; the caveat engine flags sparse or stale series (e.g. survey-only poverty, 2016 education) as Low confidence rather than hiding the gap.
Outputs land in `./output/`: the cited brief (`.md`), the evidence ledger (`.csv`), and the machine-readable provenance + cost report (`.json`).

## What's here
| File | What it is |
|---|---|
| `cedar.py` | The agentic engine: Discover → Retrieve → Verify → Analyse → Narrate → Review → Output |
| `index.html` | Self-contained interactive demo (open in any browser) — **GDACS-style world map of 36 countries**, evidence chain, charts, ledger, cost meter. Click any country to generate its brief. |
| `CONCEPT_AND_ARCHITECTURE.md` | Full concept, architecture, judging-criteria mapping, production roadmap |
| `CEDAR_Pitch.pptx` | Judge-facing pitch deck |
| `data/cache_worldbank.json` | Real World Bank WDI values (offline cache) |
| `output/` | Example generated brief, ledger, and provenance |

## The three ideas that win
1. **Visible evidence chain** — a 7-stage state machine, each step an inspectable artifact, not a hidden chat reasoning.
2. **Grounding by construction** — every claim links to the datapoints it stands on; an evidence ledger preserves lineage (UN IGME → WDI); a caveat engine turns data gaps into honest warnings; the LLM never sits between a question and a number.
3. **Frugal by design** — deterministic core = $0.00; LLM optional; live cost meter vs a naive single-big-model baseline.

## Drill-down (within-country equity)
The same evidence chain re-runs at finer granularity. Click a country in the demo (or run `--drilldown wealth`) to break a national figure down by **household wealth quintile** — exposing the disparity the average hides. Real example: in Nigeria (2018) the poorest fifth of children are stunted at **55.4%** vs **16.8%** in the richest — a **3.3× gap** the 36.8% national average conceals. Live for Kenya, Nigeria and India; the architecture extends to urban/rural, mother's education and subnational regions via the UNICEF SDMX / DHS connectors.

All figures are real World Bank / UN IGME / DHS-MICS data — Kenya's full four-indicator brief, under-5 mortality for 36 countries on the map, and wealth-quintile equity for 3 countries — retrieved 2026-06-18 (sources updated 2022–2026). Open-source and reproducible.

## Live demo & deployment (GitHub Pages)
The front-end is a single static file (`index.html`) with no build step, so it deploys on **GitHub Pages** for free:

1. Push this repo to GitHub (see below).
2. On GitHub: **Settings → Pages → Build and deployment → Source: Deploy from a branch → `main` / `/ (root)` → Save.**
3. Your live demo appears at `https://<your-username>.github.io/<repo>/` within ~1 minute.

The map and charts load Leaflet and Chart.js from CDN over HTTPS, so they work on Pages with no server. The `cedar.py` CLI is a standalone, dependency-free tool (Python 3.8+) and is not part of the web deployment.

## Push to GitHub
This folder is already an initialized git repo with an initial commit. Connect your remote and push:
```bash
# Option A — GitHub CLI (simplest; creates the repo and pushes)
gh repo create cedar --public --source=. --remote=origin --push

# Option B — manual (create an empty repo named "cedar" on github.com first, no README)
git branch -M main
git remote add origin https://github.com/<your-username>/cedar.git
git push -u origin main
```

## Optional: enabling the LLM (prose polish only)
CEDAR runs at **$0.00 with no model by default**. If you *want* an LLM to add a short, readable **executive summary** on top of the verified findings, set three environment variables and pass `--llm`. The LLM is given only the already-verified claims; a guardrail rejects its output if it introduces any number not in those claims, so it can never fabricate a figure. The cost meter then reports the real token cost.

```bash
# OpenAI
export CEDAR_LLM_API_KEY="sk-..."
python3 cedar.py --country KEN --theme child-survival --llm

# Any OpenAI-compatible provider (OpenRouter, Together, etc.)
export CEDAR_LLM_API_KEY="..."
export CEDAR_LLM_BASE_URL="https://openrouter.ai/api/v1"
export CEDAR_LLM_MODEL="meta-llama/llama-3.1-8b-instruct"
python3 cedar.py --country KEN --theme child-survival --llm

# Local & free (Ollama / LM Studio — keeps everything offline)
export CEDAR_LLM_API_KEY="local"          # any non-empty value
export CEDAR_LLM_BASE_URL="http://localhost:11434/v1"
export CEDAR_LLM_MODEL="llama3.1"
python3 cedar.py --country KEN --theme child-survival --llm
```
If the key is missing or the call fails, CEDAR silently falls back to the deterministic $0.00 narration — the brief, ledger, citations and numbers are identical either way. The LLM only ever rewrites prose; it never sits between a question and a number.
