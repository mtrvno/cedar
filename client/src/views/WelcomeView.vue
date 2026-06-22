<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const goApp = () => router.push('/app')

let observer: IntersectionObserver | null = null

onMounted(() => {
  const els = document.querySelectorAll('[data-reveal]')
  if (!('IntersectionObserver' in window) || !els.length) {
    els.forEach((el) => el.classList.add('is-visible'))
    return
  }
  observer = new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        if (e.isIntersecting) {
          ;(e.target as HTMLElement).classList.add('is-visible')
          observer?.unobserve(e.target)
        }
      }
    },
    { threshold: 0.12, rootMargin: '0px 0px -8% 0px' },
  )
  els.forEach((el) => observer!.observe(el))
})

onUnmounted(() => observer?.disconnect())

const stages = [
  { n: '01', label: 'Discover', detail: 'resolve indicator & country codes' },
  { n: '02', label: 'Retrieve', detail: 'call authoritative APIs, stamp provenance' },
  { n: '03', label: 'Verify', detail: 'coverage, recency, confidence tier' },
  { n: '04', label: 'Analyse', detail: 'trend, CAGR, gap-to-SDG-target — no LLM' },
  { n: '05', label: 'Narrate', detail: 'verified claims → cited prose' },
  { n: '06', label: 'Review', detail: 'veto any number without a datapoint' },
  { n: '07', label: 'Output', detail: 'brief + ledger + provenance + cost' },
]

const pillars = [
  {
    n: '01',
    title: 'Visible evidence chain',
    body: 'A 7-stage state machine you can watch — each step emits an inspectable artifact, not a hidden chat reasoning.',
  },
  {
    n: '02',
    title: 'Grounding by construction',
    body: 'Every claim links to the datapoints it stands on. An evidence ledger preserves lineage (UN IGME → WDI); a caveat engine turns data gaps into honest warnings.',
  },
  {
    n: '03',
    title: 'Frugal by design',
    body: 'A deterministic, model-free core runs at $0.00 per brief. The LLM is optional polish — and the cost meter proves the saving.',
  },
]

const themes = [
  { name: 'child-survival', sdg: '2.2 · 3.2' },
  { name: 'economy-poverty', sdg: '1 · 8' },
  { name: 'education', sdg: '4' },
  { name: 'health-system', sdg: '3' },
  { name: 'wash', sdg: '6' },
  { name: 'energy-climate', sdg: '7 · 13' },
  { name: 'polycrisis', sdg: 'cross-cutting' },
]

const original = [
  {
    tag: 'Blind-spot radar',
    body: 'Missing data treated as a headline finding. CEDAR scans the core SDG indicators and flags what is missing or stale — the most important number is often the one that isn’t there.',
  },
  {
    tag: 'Time-to-SDG-target',
    body: 'Every off-track indicator gets a forward projection: at the recent pace, the target is reached around 2037 — 7 years late. Decision intelligence, not just back-reporting.',
  },
  {
    tag: 'Equity drill-down',
    body: 'The same chain re-runs at finer grain. In Nigeria (2018) the poorest fifth of children are stunted at 55.4% vs 16.8% in the richest — a 3.3× gap the national average hides.',
  },
]
</script>

<template>
  <div class="welcome">
    <!-- soft breathing background -->
    <div class="welcome__bg" aria-hidden="true"></div>

    <!-- top bar -->
    <header class="topbar">
      <div class="topbar__brand">
        <div class="cedar-mark"><div class="cedar-mark__dot"></div></div>
        <span class="topbar__title">CEDAR</span>
        <span class="topbar__version">v0.4</span>
      </div>
      <div class="topbar__meta">
        <span class="topbar__chip">UN Open Source Week · 2026</span>
        <button class="enter-btn enter-btn--sm" @click="goApp">
          Enter the copilot
          <svg width="13" height="13" viewBox="0 0 14 14" aria-hidden="true">
            <path d="M2 7h10M8 3.5L11.5 7 8 10.5" stroke="currentColor" stroke-width="1.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
    </header>

    <main class="welcome__main">
      <!-- hero -->
      <section class="hero" data-reveal>
        <div class="overline">Cited Evidence &amp; Data Analytic Reporting</div>
        <h1 class="hero-title">
          Grounded evidence you can trace to the source<span class="hero-period">.</span>
        </h1>
        <p class="hero-sub">
          CEDAR turns a plain-language policy question into a decision-ready evidence brief where every
          number is traceable — through a visible 7-stage chain — back to an authoritative API query.
          Its analytic core runs with no LLM and no paid key, so it works on a zero budget.
        </p>
        <div class="hero-actions">
          <button class="enter-btn" @click="goApp">
            Enter the copilot
            <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
              <path d="M2 7h10M8 3.5L11.5 7 8 10.5" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <span class="hero-footnote">No sign-in · runs in the browser · $0.00 analytic core</span>
        </div>

        <!-- slow-breathing mark -->
        <div class="hero-mark" aria-hidden="true">
          <div class="hero-mark__ring"></div>
          <div class="hero-mark__dot"></div>
        </div>
      </section>

      <!-- wedge / pitch -->
      <section class="wedge" data-reveal>
        <div class="mono-label">The wedge</div>
        <p class="wedge-quote">
          The analytic core is correct and free because it is
          <em>computed, not generated</em>. An LLM that invents a number is a liability for an evidence
          product — so CEDAR removes the LLM from every step where a number is produced, and only allows
          it near the prose, where a reviewer still checks every sentence against a verified datapoint.
        </p>
      </section>

      <!-- evidence chain -->
      <section class="chain" data-reveal>
        <div class="section-head">
          <div class="mono-label">The evidence chain</div>
          <h2 class="section-title">Seven inspectable stages, query to brief.</h2>
        </div>

        <div class="chain__rail" aria-hidden="true">
          <div class="chain__line"></div>
          <div class="chain__traveler"></div>
        </div>

        <ol class="chain__nodes">
          <li v-for="s in stages" :key="s.n" class="chain__node">
            <span class="chain__n">{{ s.n }}</span>
            <span class="chain__label">{{ s.label }}</span>
            <span class="chain__detail">{{ s.detail }}</span>
          </li>
        </ol>
      </section>

      <!-- three ideas -->
      <section class="pillars" data-reveal>
        <div class="section-head">
          <div class="mono-label">What separates a strong submission</div>
          <h2 class="section-title">Three ideas, treated as the product.</h2>
        </div>
        <div class="pillars__grid">
          <article v-for="p in pillars" :key="p.n" class="pillar">
            <div class="pillar__top">
              <span class="pillar__n">{{ p.n }}</span>
              <span class="pillar__tick"></span>
            </div>
            <h3 class="pillar__title">{{ p.title }}</h3>
            <p class="pillar__body">{{ p.body }}</p>
          </article>
        </div>
      </section>

      <!-- themes -->
      <section class="themes" data-reveal>
        <div class="section-head">
          <div class="mono-label">SDG-mapped themes</div>
          <h2 class="section-title">One grounded chain, seven briefs.</h2>
        </div>
        <div class="themes__grid">
          <div v-for="t in themes" :key="t.name" class="theme-chip">
            <span class="theme-chip__name">{{ t.name }}</span>
            <span class="theme-chip__sdg">SDG {{ t.sdg }}</span>
          </div>
        </div>
      </section>

      <!-- what makes it original -->
      <section class="original" data-reveal>
        <div class="section-head">
          <div class="mono-label">What makes it original</div>
          <h2 class="section-title">Beyond a generic copilot.</h2>
        </div>
        <div class="original__list">
          <article v-for="(o, i) in original" :key="o.tag" class="orig-row">
            <span class="orig-row__n">{{ String(i + 1).padStart(2, '0') }}</span>
            <div>
              <div class="orig-row__tag">{{ o.tag }}</div>
              <p class="orig-row__body">{{ o.body }}</p>
            </div>
          </article>
        </div>
      </section>

      <!-- final CTA -->
      <section class="cta" data-reveal>
        <div class="cta__mark" aria-hidden="true"><div class="cta__dot"></div></div>
        <h2 class="cta__title">Check every number it used. Anyone can afford to run it.</h2>
        <p class="cta__sub">
          The point is not that an AI wrote a brief — it is that you can trace every figure to its
          source, and that a country office with no model budget can still produce a fully-cited one.
        </p>
        <button class="enter-btn enter-btn--lg" @click="goApp">
          Enter the copilot
          <svg width="15" height="15" viewBox="0 0 14 14" aria-hidden="true">
            <path d="M2 7h10M8 3.5L11.5 7 8 10.5" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </section>
    </main>

    <footer class="welcome__footer">
      <span>CEDAR · Cited Evidence &amp; Data Analytic Reporting</span>
      <span class="welcome__footer-sep">·</span>
      <span>UNICEF Innocenti — Challenge 3</span>
      <span class="welcome__footer-sep">·</span>
      <span>Open-source &amp; reproducible</span>
    </footer>
  </div>
</template>

<style scoped>
.welcome {
  position: relative;
  min-height: 100vh;
  font-family: 'IBM Plex Sans', system-ui, sans-serif;
  color: #1b1e23;
  background: #f4f3ef;
  overflow: hidden;
}

/* slow breathing background — constant, calm */
.welcome__bg {
  position: fixed;
  inset: -12%;
  pointer-events: none;
  z-index: 0;
  background:
    radial-gradient(60% 50% at 18% 22%, rgba(44, 74, 99, 0.06), transparent 60%),
    radial-gradient(55% 45% at 82% 78%, rgba(138, 101, 22, 0.05), transparent 60%),
    radial-gradient(40% 35% at 50% 50%, rgba(255, 255, 255, 0.55), transparent 70%);
  animation: cedarDrift 26s ease-in-out infinite;
  will-change: transform;
}

/* ---------- top bar ---------- */
.topbar {
  position: relative;
  z-index: 2;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  border-bottom: 1px solid #e3e1da;
  background: rgba(247, 246, 243, 0.82);
  backdrop-filter: saturate(140%) blur(6px);
}
.topbar__brand { display: flex; align-items: center; gap: 9px; }
.cedar-mark {
  width: 22px; height: 22px;
  border: 1.5px solid #2c4a63;
  display: flex; align-items: center; justify-content: center;
  flex: none;
}
.cedar-mark__dot { width: 7px; height: 7px; background: #2c4a63; }
.topbar__title { font-weight: 600; letter-spacing: .14em; font-size: 14px; color: #1b1e23; }
.topbar__version {
  margin-left: 4px;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 9.5px; letter-spacing: .06em; color: #a7aaa2;
}
.topbar__meta { display: flex; align-items: center; gap: 16px; }
.topbar__chip {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10.5px; letter-spacing: .08em; text-transform: uppercase;
  color: #8a8f87;
}
@media (max-width: 720px) { .topbar__chip { display: none; } }

/* ---------- buttons ---------- */
.enter-btn {
  display: inline-flex; align-items: center; gap: 9px;
  padding: 10px 16px;
  background: #2c4a63;
  border: 1px solid #2c4a63;
  border-radius: 3px;
  cursor: pointer;
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 13.5px; font-weight: 500; color: #fff;
  transition: background .2s ease, border-color .2s ease, transform .2s ease, box-shadow .2s ease;
}
.enter-btn svg { transition: transform .2s ease; }
.enter-btn:hover { background: #22405a; border-color: #22405a; }
.enter-btn:hover svg { transform: translateX(2px); }
.enter-btn--sm { padding: 7px 12px; font-size: 12.5px; }
.enter-btn--lg { padding: 13px 22px; font-size: 15px; }

/* ---------- layout ---------- */
.welcome__main {
  position: relative;
  z-index: 1;
  max-width: 1080px;
  margin: 0 auto;
  padding: 0 28px;
}

.section-head { margin-bottom: 30px; }
.mono-label {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10.5px; letter-spacing: .12em; text-transform: uppercase;
  color: #a7aaa2;
  display: block;
  margin-bottom: 12px;
}
.overline {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11px; letter-spacing: .16em; text-transform: uppercase;
  color: #8a6516;
  margin-bottom: 20px;
}
.section-title {
  font-family: 'Source Serif 4', Georgia, serif;
  font-weight: 400;
  font-size: 27px; line-height: 1.25; letter-spacing: -.01em;
  color: #1b1e23; margin: 0; max-width: 640px;
}

/* ---------- hero ---------- */
.hero {
  position: relative;
  padding: 120px 0 96px;
  max-width: 760px;
}
.hero-title {
  font-family: 'Source Serif 4', Georgia, serif;
  font-weight: 400;
  font-size: 46px; line-height: 1.18; letter-spacing: -.012em;
  color: #1b1e23; margin: 0 0 22px;
  text-wrap: balance;
}
.hero-period { color: #2c4a63; }
.hero-sub {
  font-size: 16px; line-height: 1.65; color: #5a6068;
  margin: 0 0 34px; max-width: 560px;
}
.hero-actions { display: flex; align-items: center; gap: 18px; flex-wrap: wrap; }
.hero-footnote {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10.5px; letter-spacing: .04em; color: #9a9f97;
}

.hero-mark {
  position: absolute;
  top: 96px; right: 0;
  width: 120px; height: 120px;
  display: flex; align-items: center; justify-content: center;
  pointer-events: none;
}
.hero-mark__ring {
  position: absolute; inset: 0;
  border: 1px solid #ddd9cf;
  border-radius: 50%;
}
.hero-mark__ring::after {
  content: ''; position: absolute; inset: 14px;
  border: 1px solid #e7e4dc;
  border-radius: 50%;
}
.hero-mark__dot {
  width: 12px; height: 12px; background: #2c4a63;
  animation: cedarBreathe 3.4s ease-in-out infinite;
  will-change: transform, opacity;
}
@media (max-width: 820px) { .hero-mark { display: none; } }
@media (max-width: 640px) {
  .hero { padding: 64px 0 56px; }
  .hero-title { font-size: 34px; }
}

/* ---------- wedge ---------- */
.wedge {
  padding: 40px 0 64px;
  border-top: 1px solid #e3e1da;
  max-width: 760px;
}
.wedge-quote {
  font-family: 'Source Serif 4', Georgia, serif;
  font-size: 21px; line-height: 1.55; color: #2a2e34;
  margin: 4px 0 0; text-wrap: pretty;
}
.wedge-quote em { color: #2c4a63; font-style: italic; }

/* ---------- chain ---------- */
.chain {
  padding: 56px 0 64px;
  border-top: 1px solid #e3e1da;
}
.chain__rail {
  position: relative;
  height: 1px;
  margin: 34px 0 26px;
  overflow: visible;
}
.chain__line {
  position: absolute; inset: 0;
  background: linear-gradient(90deg, transparent, #d8d4c9 8%, #d8d4c9 92%, transparent);
}
.chain__traveler {
  position: absolute;
  top: -3px;
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #2c4a63;
  box-shadow: 0 0 0 4px rgba(44, 74, 99, 0.12);
  animation: cedarTravel 7.5s cubic-bezier(.45, 0, .55, 1) infinite;
  will-change: left, opacity;
}
.chain__nodes {
  list-style: none; margin: 0; padding: 0;
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 10px;
}
.chain__node {
  display: flex; flex-direction: column; gap: 6px;
  padding: 14px 12px 14px 0;
  border-top: 1px solid #ece9e1;
}
.chain__n {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10.5px; color: #2c4a63; font-weight: 500;
  letter-spacing: .04em;
}
.chain__label {
  font-size: 13.5px; font-weight: 600; color: #1b1e23;
  letter-spacing: .01em;
}
.chain__detail {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10.5px; line-height: 1.45; color: #8a8f87;
}
@media (max-width: 920px) {
  .chain__nodes { grid-template-columns: repeat(2, 1fr); gap: 0; }
  .chain__node { padding: 14px 14px 14px 0; border-bottom: 1px solid #ece9e1; }
}

/* ---------- pillars ---------- */
.pillars {
  padding: 56px 0 64px;
  border-top: 1px solid #e3e1da;
}
.pillars__grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 22px;
}
.pillar {
  background: #fff;
  border: 1px solid #e3e1da;
  border-radius: 4px;
  padding: 22px 22px 24px;
  transition: border-color .2s ease, transform .25s ease, box-shadow .25s ease;
}
.pillar:hover {
  border-color: #c8c3b6;
  transform: translateY(-2px);
  box-shadow: 0 6px 22px -16px rgba(40, 47, 61, 0.22);
}
.pillar__top { display: flex; align-items: center; gap: 10px; margin-bottom: 18px; }
.pillar__n {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11px; color: #2c4a63; font-weight: 500;
  letter-spacing: .04em;
}
.pillar__tick { flex: 1; height: 1px; background: #ece9e1; }
.pillar__title {
  font-family: 'Source Serif 4', Georgia, serif;
  font-weight: 500; font-size: 18px; line-height: 1.3;
  color: #1b1e23; margin: 0 0 10px;
}
.pillar__body { font-size: 14px; line-height: 1.6; color: #5a6068; margin: 0; }
@media (max-width: 860px) { .pillars__grid { grid-template-columns: 1fr; } }

/* ---------- themes ---------- */
.themes {
  padding: 56px 0 64px;
  border-top: 1px solid #e3e1da;
}
.themes__grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
.theme-chip {
  display: flex; flex-direction: column; gap: 8px;
  padding: 16px 16px 18px;
  background: #faf9f6;
  border: 1px solid #e3e1da;
  border-radius: 3px;
  transition: border-color .2s ease, background .2s ease;
}
.theme-chip:hover { border-color: #2c4a63; background: #fff; }
.theme-chip__name {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 12.5px; color: #1b1e23; letter-spacing: .02em;
}
.theme-chip__sdg {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px; color: #9a9f97; letter-spacing: .04em;
}
@media (max-width: 860px) { .themes__grid { grid-template-columns: repeat(2, 1fr); } }

/* ---------- original ---------- */
.original {
  padding: 56px 0 64px;
  border-top: 1px solid #e3e1da;
}
.original__list { display: flex; flex-direction: column; gap: 0; }
.orig-row {
  display: grid;
  grid-template-columns: 64px 1fr;
  gap: 18px;
  padding: 24px 0;
  border-top: 1px solid #ece9e1;
}
.orig-row:first-child { border-top: none; padding-top: 6px; }
.orig-row__n {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11px; color: #2c4a63; font-weight: 500;
  letter-spacing: .04em; padding-top: 4px;
}
.orig-row__tag {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11px; letter-spacing: .1em; text-transform: uppercase;
  color: #8a6516; margin-bottom: 8px;
}
.orig-row__body {
  font-family: 'Source Serif 4', Georgia, serif;
  font-size: 17px; line-height: 1.6; color: #2a2e34; margin: 0;
  max-width: 640px; text-wrap: pretty;
}
@media (max-width: 640px) { .orig-row { grid-template-columns: 1fr; gap: 8px; } }

/* ---------- CTA ---------- */
.cta {
  padding: 80px 0 88px;
  border-top: 1px solid #e3e1da;
  text-align: center;
  display: flex; flex-direction: column; align-items: center; gap: 18px;
}
.cta__mark {
  width: 26px; height: 26px;
  border: 1.5px solid #2c4a63;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 4px;
}
.cta__dot {
  width: 8px; height: 8px; background: #2c4a63;
  animation: cedarBreathe 3.4s ease-in-out infinite;
}
.cta__title {
  font-family: 'Source Serif 4', Georgia, serif;
  font-weight: 400; font-size: 28px; line-height: 1.28; letter-spacing: -.01em;
  color: #1b1e23; margin: 0; max-width: 620px; text-wrap: balance;
}
.cta__sub {
  font-size: 15px; line-height: 1.65; color: #5a6068;
  margin: 0; max-width: 540px;
}

/* ---------- footer ---------- */
.welcome__footer {
  position: relative; z-index: 1;
  border-top: 1px solid #e3e1da;
  background: #f7f6f3;
  padding: 20px 28px;
  display: flex; align-items: center; justify-content: center; gap: 12px; flex-wrap: wrap;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10.5px; letter-spacing: .04em; color: #9a9f97;
}
.welcome__footer-sep { color: #c4c1b6; }

/* ---------- scroll reveal ---------- */
[data-reveal] {
  opacity: 0;
  transform: translateY(14px);
  transition: opacity .7s ease, transform .7s ease;
}
[data-reveal].is-visible { opacity: 1; transform: none; }
</style>
