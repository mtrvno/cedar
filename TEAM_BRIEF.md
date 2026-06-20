# CEDAR — Team Brief

*Cited Evidence & Data Analytic Reporting · UN Open Source Week Hack-A-Thon 2026 · Challenge 3 (UNICEF Innocenti)*

This is the 5-minute onboarding for the team. For the full write-up see `CONCEPT_AND_ARCHITECTURE.md`; for the judge pitch see `CEDAR_Pitch.pptx`.

---

## The 30-second version (paste this in the group chat)

> **CEDAR** turns a plain-language question like *"is child survival on track in Kenya?"* into a **decision-ready, fully-cited evidence brief**. Every number traces back through a visible chain to an authoritative API query — and the analytic core runs with **no LLM and no paid key**, so it costs **$0.00** per brief and works for an under-resourced country office. The challenge rewards three things — a *visible evidence chain*, *grounding you can audit*, and *cost/accessibility* — and CEDAR is built around exactly those three. Live demo: a 36-country map + an equity drill-down; data is real World Bank / UN IGME.

---

## Why this should win (the wedge)

Most teams will build "a chatbot over UN data." The challenge brief explicitly asks for more, and penalises the things chatbots do badly. Our one-line bet:

> **Never let the language model sit between a question and a number.**

Every figure is *computed deterministically and cited*; the LLM is removed from every step that produces a number (it's optional, only for prose polish). That makes the output **correct, reproducible, and free** — which is exactly what an evidence product for decisions about children needs.

| The challenge asks for… | What CEDAR does |
|---|---|
| The evidence chain stays **visible** | A 7-step pipeline you can watch, each step inspectable |
| **Grounding** you can audit | Every claim links to its datapoints; an evidence ledger preserves lineage; a caveat engine flags data gaps |
| **Cost & accessibility** | Deterministic core = $0.00; live cost meter vs a naive "one big model" baseline |

## How it works (plain language)

A question flows through seven steps. Think of it as an assembly line where each station can be inspected and nothing downstream trusts a number an earlier station didn't verify:

1. **Discover** — figure out which indicator(s) and country the question needs.
2. **Retrieve** — pull the data from authoritative APIs and stamp each datapoint with its source, query URL, and date.
3. **Verify / QA** — check coverage and recency, assign a confidence tier, and auto-write caveats (e.g. "survey-only data").
4. **Analyse** — compute the trend, the gap to the SDG target, peer comparison. *Deterministic — no AI.*
5. **Narrate** — turn the verified numbers into sentences, each carrying a citation.
6. **Review** — refuse to ship any sentence whose number isn't backed by a datapoint.
7. **Output** — a brief + an evidence ledger (CSV) + a provenance file (JSON) + a cost report.

**Drill-down** is the same chain run one level finer — e.g. stunting broken down by household wealth quintile, exposing the inequality a national average hides (in Nigeria: 55.4% stunting among the poorest fifth vs 16.8% among the richest — a 3.3× gap).

## What's in the repo

| File / folder | What it is |
|---|---|
| `index.html` | The interactive demo (single static file). Four tabs: Overview · Country map (36 countries) · Equity drill-down · Evidence & cost. This is what deploys to GitHub Pages. |
| `cedar.py` | The agentic engine as a runnable CLI. Stdlib-only, no install. Generates briefs + ledger + provenance. |
| `data/cache_worldbank.json` | Bundled real World Bank values so it runs offline / $0. |
| `output/` | Example generated briefs (national + drill-down). |
| `CONCEPT_AND_ARCHITECTURE.md` | The full design, judging-criteria mapping, production roadmap. |
| `CEDAR_Pitch.pptx` | The judge-facing deck. |
| `README.md` | Quick start + deployment. |

## Run it in two minutes

```bash
# 1. See the demo: just open index.html in any browser (no server needed).

# 2. Run the engine (Python 3.8+, no dependencies):
python3 cedar.py --country KEN --theme child-survival --offline   # a full national brief, $0.00
python3 cedar.py --country NGA --drilldown wealth --offline        # the equity drill-down
python3 cedar.py --list                                            # see the indicator catalog
```
Outputs land in `output/`.

## Where you can plug in (suggested workstreams)

These are independent enough to parallelise:

- **Data / connectors** — wire live UNICEF SDMX & DHS endpoints (currently World Bank API + bundled cache); add indicators and countries to the catalog in `cedar.py` and `data/`.
- **Front-end** — `index.html` is self-contained; extend the map (a second indicator toggle, a subnational/regional choropleth), polish the report layout.
- **Engine / agents** — strengthen the Verify and Review steps, add an optional LLM narration path (LiteLLM) with the cost meter wired in, add evaluation (Ragas/DeepEval).
- **Narrative / pitch** — own `CEDAR_Pitch.pptx` and the live demo script; prep the 3-minute walkthrough.
- **Grounding & QA** — sanity-check every figure against the source APIs; expand the caveat rules.

## Likely questions from judges (and our answers)

- **"How do we know the AI didn't make up a number?"** It can't — the analyst only references datapoints the verifier hashed, and the reviewer blocks any uncited claim. The LLM never touches the numbers.
- **"Is this affordable for low-resource teams?"** Yes — the core needs no model and no paid key; a brief costs $0.00 and runs offline from cache.
- **"Is the data real and current?"** Yes — World Bank WDI (re-publishing UN IGME / WHO-UNICEF estimates), last updated 2026-04-08; every figure has a re-runnable query link.
- **"What's genuinely novel?"** Treating grounding, auditability, and cost as *the product* rather than features — and making drill-down a recursive use of the same auditable chain.

---

*Keep it honest: we ground every claim, show our sources, and flag what we don't know. That's the whole point of CEDAR.*
