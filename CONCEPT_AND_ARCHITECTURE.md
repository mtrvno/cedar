# CEDAR — Cited Evidence & Data Analytic Reporting

**UN Open Source Week Hack-A-Thon 2026 · Challenge 3: Agentic Copilots & Analytic Intelligence**
UNICEF Innocenti — Office of Strategy and Evidence, Data & Analytics Section

> *Grounded evidence you can trace to the source — at a fraction of the cost.*

---

## 1. The one-sentence pitch

CEDAR turns a plain-language policy question into a **decision-ready evidence brief in which every single number is traceable**, through a visible chain, back to an authoritative API query — and it does this with **no large language model and no paid API key in its analytic core**, so it works for an over-stretched country office on a zero budget, not only for teams with expensive compute.

## 2. Why this wins the challenge

The brief is explicit about what separates a strong submission from "just a chatbot." It asks for three things that most hackathon entries under-deliver. CEDAR is built around exactly those three, and treats them as the product rather than as add-ons.

| What the challenge asks for | What most entries do | What CEDAR does |
|---|---|---|
| **The evidence chain stays visible** from query to product | Hide reasoning inside a chat bubble | A 7-stage state machine you can watch: Discover → Retrieve → Verify → Analyse → Narrate → Review → Output, each emitting an inspectable artifact |
| **Grounding made visible** — citations, lineage, assumptions, caveats, reproducible queries | A footnote or a link dump | Every claim carries the exact datapoints it stands on; an **evidence ledger** maps claim → datapoint → API query → upstream source; a **caveat engine** turns metadata gaps into honest warnings |
| **Cost & accessibility** so advanced AI isn't only for the well-funded | Ignore cost; assume a frontier model | A **frugal agent**: the analytic core is deterministic and model-free ($0.00/brief), an LLM is optional polish, and a live cost meter proves the saving |

The wedge: **the analytic core is correct and free because it is computed, not generated.** An LLM that invents a number is a liability for an evidence product. CEDAR removes the LLM from every step where a number is produced, and only allows it near the prose — where a reviewer agent still checks that every sentence is backed by a verified datapoint.

## 3. The problem in the field

A UNICEF or government analyst asking "is child survival on track in Kenya?" today must: find the right indicator codes, query several incompatible APIs, reconcile differing vintages and definitions, notice that a key indicator only has survey-year data, compute trends and gaps-to-target by hand, write it up, and cite it. It takes hours, the provenance is rarely preserved, and a generic AI chatbot will happily fill the gaps with plausible but unsourced numbers. For decisions about children, an unsourced number is worse than no number.

## 4. The solution — an agentic evidence-chain workflow

```
   user question
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ AGENT 1  DISCOVER + RETRIEVE                                             │
│   • resolve indicator codes & country codes from the metadata catalog    │
│     (production: Commons knowledge graph / SDMX structure API)           │
│   • call authoritative APIs (World Bank WDI; UNICEF SDMX)                │
│   • stamp PROVENANCE on every datapoint:                                  │
│     publisher · upstream source · query URL · last-updated · retrieved-at │
│   • transparent offline cache fallback (resilience + zero-cost demo)     │
├─────────────────────────────────────────────────────────────────────────┤
│ AGENT 2  VERIFY / QA  (independent grounding gate)                       │
│   • coverage, recency, data-gap detection                                │
│   • CONFIDENCE TIER (High / Medium / Low)                               │
│   • CAVEAT ENGINE — e.g. "survey-only: 3 of 10 years carry a value"     │
│   • value-integrity hash so the analyst provably used these exact numbers │
├─────────────────────────────────────────────────────────────────────────┤
│ AGENT 3  ANALYSE  (deterministic — NO LLM)                              │
│   • trend (first vs latest), CAGR, gap-to-SDG-target, peer comparison     │
│   • emits CLAIMS, each carrying the datapoints it stands on               │
├─────────────────────────────────────────────────────────────────────────┤
│ AGENT 4  NARRATE  (template renderer; LLM optional, off by default)     │
│   • verified claims → prose; every sentence carries a citation token      │
├─────────────────────────────────────────────────────────────────────────┤
│ AGENT 5  REVIEW  (final gate)                                           │
│   • refuses to ship any number without a supporting datapoint            │
└─────────────────────────────────────────────────────────────────────────┘
        │
        ▼
   Brief.md  +  Evidence Ledger (CSV)  +  Provenance graph (JSON)  +  Cost report
```

### Why split it into agents?
Separation of concerns is what makes the chain *visible* and *trustworthy*. The agent that retrieves is not the agent that judges confidence; the agent that computes numbers is not the agent that writes prose; and a final reviewer can veto the whole product. Each boundary is an inspection point — exactly the "discovery, verification, analysis, explanation, output" decomposition the challenge calls for.

## 5. Grounding made visible (the "glass box")

Three concrete artifacts ship with every brief:

1. **Evidence ledger** — one row per datapoint used, with the upstream source, the *exact* re-runnable query URL, the source's last-updated date, and the retrieval timestamp. Lineage is preserved, not flattened: e.g. the under-5 mortality figure is labelled *UN IGME (UNICEF-led) → World Bank WDI*, not just "World Bank."
2. **Provenance JSON** — a machine-readable graph: `claim → datapoints → query → source`, plus the QA verdicts and the cost report. This is what lets a reviewer (human or downstream tool) audit the brief.
3. **Caveat engine output** — assumptions and limitations are derived from the data itself. In the live demo, stunting prevalence has values only for 2014, 2016 and 2022, so CEDAR marks it **Low confidence** and warns against reading a smooth trend — instead of silently drawing one.

**No fabricated numbers, by construction.** The analyst can only reference datapoints the verifier has hashed; the reviewer blocks any claim lacking a datapoint. The LLM never sits between a question and a figure.

## 5b. Drill-down — the same chain, finer grain

Decisions are rarely made on national averages alone; the question a UNICEF analyst asks next is *"who, within the country, is being left behind?"* CEDAR treats drill-down as a **recursive application of the same evidence chain** at a finer level of disaggregation — not a separate feature with separate trust properties.

The demo drills a national figure down by **household wealth quintile**: discover the wealth-disaggregated indicators → retrieve each quintile with its own provenance → verify coverage → analyse the gap (poorest/richest ratio and percentage-point gap) → narrate with citations. The result is grounded and free, exactly like the national brief.

The within-country story is often far starker than the headline. In **Nigeria (2018)**, stunting among the poorest fifth of children is **55.4%** versus **16.8%** among the richest — a **3.3× gap** that the 36.8% national average hides completely. Kenya shows a 2.6× gap (35.9% vs 13.8%, 2014) and India a 2.0× gap (46.1% vs 22.9%, 2021). These are real World Bank *HNP Statistics by Wealth Quintile* values (upstream DHS/MICS surveys).

The same pattern generalises to the other disaggregations the survey data carries — **urban/rural, mother's education, sex, and subnational region**. Subnational geography additionally needs admin-boundary polygons (geoBoundaries / GADM) for choropleth rendering; the equity logic is identical. Because the underlying DHS/UNICEF SDMX endpoints expose these dimensions, extending the drill-down is a matter of catalog entries, not new architecture.

## 6. Cost-aware design (the "frugal agent")

The challenge warns that agentic AI "can increase cost, hide assumptions, or widen the digital divide." CEDAR's cost posture is a feature, not an afterthought:

- **Deterministic core = $0.00.** Discovery, retrieval, verification and analysis use no model. A full Kenya child-survival brief is generated in ~2 ms of compute with zero LLM calls.
- **Tiered routing when an LLM is used.** Narrative polish (optional) routes to a small model via LiteLLM; only genuinely hard synthesis would escalate. The meter prices what each tier costs.
- **Caching.** Authoritative responses are cached (and bundled for offline use), so repeat questions cost nothing and the tool keeps working behind an unreliable connection.
- **Transparent meter.** Every run reports API calls, cache hits, LLM calls, tokens, latency, and a $ estimate — and contrasts it against a naive "stuff everything into one big model" baseline (~$0.097/brief in the demo). CEDAR's saving is ~100% in deterministic mode.

The headline for judges: **a country office with no model budget can still produce a fully-cited brief.** That is the direct answer to the digital-divide concern.

## 7. What we built for the hackathon (this repo)

| Deliverable | File | Status |
|---|---|---|
| Runnable agentic prototype (stdlib-only Python, no install) | `cedar.py` | ✅ runs live + offline |
| Bundled authoritative data cache (real WDI values) | `data/cache_worldbank.json` | ✅ |
| Example generated outputs | `output/brief_*.md`, `ledger_*.csv`, `provenance_*.json` | ✅ |
| Interactive demo (evidence chain, charts, ledger, cost meter) | `index.html` | ✅ self-contained |
| Concept & architecture (this doc) | `CONCEPT_AND_ARCHITECTURE.md` | ✅ |
| Judge-facing pitch deck | `CEDAR_Pitch.pptx` | ✅ |

Run it:
```bash
python3 cedar.py --country KEN --theme child-survival            # live API, falls back to cache
python3 cedar.py --country KEN --theme child-survival --offline  # fully offline, $0.00
python3 cedar.py --list                                          # show the indicator catalog
```

## 8. Production architecture (how it scales beyond the demo)

The prototype is intentionally dependency-free to prove the cost thesis, but the design maps cleanly onto the challenge's recommended stack:

- **Orchestration:** the 5-agent state machine → LangGraph / CrewAI nodes.
- **Discovery:** the hard-coded catalog → the UN System Data Commons knowledge graph + SDMX structure API for live metadata inspection; expose CEDAR itself as an **MCP server** so any MCP client can call `discover`, `retrieve`, `verify`, `analyse`.
- **Retrieval:** add UNICEF SDMX (`sdmx.data.unicef.org`), HDX, IATI, UNData alongside World Bank; DuckDB for the response cache.
- **Evaluation:** Ragas / DeepEval for groundedness & faithfulness scoring; the value-integrity hash already gives a deterministic faithfulness check.
- **Observability:** Langfuse / LiteLLM for token-and-cost tracing in production.
- **Output:** the Markdown brief → Quarto / Observable for publication-grade PDFs and dashboards.

## 9. Data sources & lineage (this demo)

All figures are **real** World Bank World Development Indicators values, retrieved 2026-06-18 (source last updated 2026-04-08):

- **Under-5 mortality** `SH.DYN.MORT`, **Infant mortality** `SP.DYN.IMRT.IN` — UN IGME (UN Inter-agency Group for Child Mortality Estimation, led by UNICEF) → WDI.
- **DPT immunization** `SH.IMM.IDPT` — WHO/UNICEF Estimates of National Immunization Coverage (WUENIC) → WDI.
- **Stunting** `SH.STA.STNT.ZS` — UNICEF/WHO/World Bank Joint Child Malnutrition Estimates → WDI.
- Benchmark: **SDG 3.2.1**, under-5 mortality ≤ 25 per 1,000 live births by 2030.

## 10. Assumptions & honest limitations

- The interactive map covers 36 countries on the headline indicator (under-5 mortality), with Kenya carrying the full four-indicator brief; production discovery is dynamic via the Commons graph and would extend every indicator to every country.
- "Trend" is first-vs-latest plus CAGR — deliberately simple and transparent, not a fitted model; this is stated in the brief's methods section.
- UNICEF SDMX is documented as a connector and partially wired, but the demo's live values are sourced through the World Bank API (which re-publishes the same UN IGME / WHO-UNICEF series) for reliability during judging.
- Cost figures for the "naive" baseline are illustrative June-2026 list prices, shown for contrast, not a benchmark of any specific competitor.

---

*CEDAR is open-source and reproducible. The point is not that an AI wrote a brief — it is that you can check every number it used, and that anyone can afford to run it.*
