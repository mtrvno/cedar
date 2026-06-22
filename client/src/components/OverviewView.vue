<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
import { getCountries, getBrief, getPolycrisis } from '@/api/cedar'
import type { Country, BriefResponse, BriefIndicator, PolycrisisResponse } from '@/types/api'

const THEMES = [
  { key: 'child-survival', label: 'Child Survival' },
  { key: 'economy-poverty', label: 'Economy & Poverty' },
  { key: 'education', label: 'Education' },
  { key: 'health-system', label: 'Health System' },
  { key: 'wash', label: 'Water & Sanitation' },
  { key: 'energy-climate', label: 'Energy & Climate' },
]

const BAND_LABEL: Record<string, string> = {
  high: 'High stress',
  elevated: 'Elevated stress',
  lower: 'Lower stress',
}
const BAND_COLOR: Record<string, string> = {
  high: '#c0392b',
  elevated: '#e67e22',
  lower: '#2f6b4f',
}

const countries = ref<Country[]>([])
const countrySearch = ref('')
const selectedIso = ref('')
const selectedTheme = ref('child-survival')
const dropdownOpen = ref(false)

const brief = ref<BriefResponse | null>(null)
const polycrisis = ref<PolycrisisResponse | null>(null)
const loadingBrief = ref(false)
const loadingPoly = ref(false)
const errorBrief = ref<string | null>(null)
const errorPoly = ref<string | null>(null)

onMounted(async () => {
  try {
    const res = await getCountries()
    countries.value = res.countries.sort((a, b) => a.name.localeCompare(b.name))
  } catch {
    // backend offline
  }
})

const filteredCountries = computed(() => {
  const q = countrySearch.value.toLowerCase().trim()
  if (!q) return countries.value
  return countries.value.filter(
    (c) => c.name.toLowerCase().includes(q) || c.iso3.toLowerCase().includes(q),
  )
})

const selectedCountryName = computed(
  () => countries.value.find((c) => c.iso3 === selectedIso.value)?.name ?? '',
)

function selectCountry(c: Country) {
  selectedIso.value = c.iso3
  countrySearch.value = ''
  dropdownOpen.value = false
}

async function fetchBrief() {
  if (!selectedIso.value) return
  loadingBrief.value = true
  errorBrief.value = null
  brief.value = null
  try {
    brief.value = await getBrief(selectedIso.value, selectedTheme.value)
  } catch (e) {
    errorBrief.value = e instanceof Error ? e.message : 'Failed to load brief'
  } finally {
    loadingBrief.value = false
  }
}

async function fetchPolycrisis() {
  if (!selectedIso.value) return
  loadingPoly.value = true
  errorPoly.value = null
  polycrisis.value = null
  try {
    polycrisis.value = await getPolycrisis(selectedIso.value)
  } catch (e) {
    errorPoly.value = e instanceof Error ? e.message : 'Failed to load polycrisis'
  } finally {
    loadingPoly.value = false
  }
}

watch([selectedIso, selectedTheme], () => {
  if (selectedIso.value) {
    fetchBrief()
    fetchPolycrisis()
  }
})

// Spark SVG from obs dict
function spark(obs: Record<string, number> | undefined) {
  if (!obs) return null
  const entries = Object.entries(obs)
    .map(([y, v]) => ({ y: parseInt(y), v }))
    .sort((a, b) => a.y - b.y)
  if (entries.length < 2) return null
  const vals = entries.map((e) => e.v)
  const w = 100,
    h = 26,
    p = 2
  let mn = Math.min(...vals),
    mx = Math.max(...vals)
  if (mx === mn) { mx = mn + 1; mn = mn - 1 }
  const X = (i: number) => p + (i * (w - 2 * p)) / (entries.length - 1)
  const Y = (v: number) => h - p - ((v - mn) / (mx - mn)) * (h - 2 * p)
  let line = ''
  vals.forEach((v, i) => { line += (i ? 'L' : 'M') + X(i).toFixed(1) + ' ' + Y(v).toFixed(1) + ' ' })
  const n = vals.length
  const area =
    line + 'L' + X(n - 1).toFixed(1) + ' ' + (h - p) + ' L' + X(0).toFixed(1) + ' ' + (h - p) + ' Z'
  const last = vals[n - 1] ?? 0
  return {
    line: line.trim(),
    area,
    dotX: X(n - 1).toFixed(1),
    dotY: Y(last).toFixed(1),
    first: entries[0],
    last: entries[n - 1],
  }
}

function latestObs(ind: BriefIndicator): { year: string; value: number } | null {
  if (!ind.obs) return null
  const entries = Object.entries(ind.obs).sort((a, b) => parseInt(b[0]) - parseInt(a[0]))
  const top = entries[0]
  if (!top) return null
  return { year: top[0], value: top[1] }
}

function tierStyle(t: string | undefined) {
  const tier = t === 'Medium' ? 'Med' : (t ?? '')
  if (tier === 'High') return 'color:#2f6b4f;background:#e7efe9;border:1px solid #cfe0d4;'
  if (tier === 'Med') return 'color:#8a6516;background:#f4ecd8;border:1px solid #e7d9b6;'
  return 'color:#6d7178;background:#ecebe4;border:1px solid #ddd9cf;'
}

function tierLabel(t: string | undefined) {
  return t === 'Medium' ? 'Med' : (t ?? '—')
}

function verdictIcon(v: string | undefined) {
  if (v === 'improving') return { symbol: '↑', color: '#2f6b4f' }
  if (v === 'off-track') return { symbol: '↗', color: '#c0392b' }
  if (v === 'on-track') return { symbol: '✓', color: '#2f6b4f' }
  return { symbol: '—', color: '#9a9f97' }
}

const availableIndicators = computed(() =>
  (brief.value?.indicators ?? []).filter((i) => i.available),
)
const unavailableIndicators = computed(() =>
  (brief.value?.indicators ?? []).filter((i) => !i.available),
)

const themeLabel = computed(
  () => THEMES.find((t) => t.key === selectedTheme.value)?.label ?? selectedTheme.value,
)
</script>

<template>
  <div class="overview-root">
    <!-- Controls bar -->
    <div class="controls-bar">
      <!-- Country selector -->
      <div class="selector-wrap" v-click-outside="() => (dropdownOpen = false)">
        <button
          class="selector-btn"
          :class="{ 'selector-btn--active': dropdownOpen }"
          @click="dropdownOpen = !dropdownOpen"
        >
          <svg width="11" height="11" viewBox="0 0 12 12" style="flex:none;color:#6a6f68;">
            <circle cx="6" cy="6" r="4.5" stroke="currentColor" stroke-width="1.3" fill="none" />
            <path d="M4 6.5C4.5 8.5 7.5 8.5 8 6.5M4 5.5c.5-2 3.5-2 4 0" stroke="currentColor" stroke-width="1" fill="none" />
            <path d="M3 6h6M6 3v6" stroke="currentColor" stroke-width="1" stroke-linecap="round" />
          </svg>
          <span v-if="selectedCountryName">{{ selectedCountryName }}</span>
          <span v-else style="color:#a7aaa2;">Select country…</span>
          <svg width="10" height="10" viewBox="0 0 10 10" style="flex:none;margin-left:auto;color:#9a9f97;">
            <path d="M2.5 3.5l2.5 3 2.5-3" stroke="currentColor" stroke-width="1.2" fill="none" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>

        <div v-if="dropdownOpen" class="selector-dropdown">
          <div style="padding:8px 10px;border-bottom:1px solid #ece9e1;">
            <input
              v-model="countrySearch"
              placeholder="Search…"
              class="search-input"
              autofocus
            />
          </div>
          <div class="dropdown-list">
            <button
              v-for="c in filteredCountries"
              :key="c.iso3"
              class="dropdown-item"
              :class="{ 'dropdown-item--active': c.iso3 === selectedIso }"
              @click="selectCountry(c)"
            >
              <span style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:#9a9f97;flex:none;width:30px;">{{ c.iso3 }}</span>
              {{ c.name }}
            </button>
            <div v-if="filteredCountries.length === 0" style="padding:12px 12px;font-size:13px;color:#a7aaa2;">No matches</div>
          </div>
        </div>
      </div>

      <!-- Theme tabs -->
      <div class="theme-tabs">
        <button
          v-for="th in THEMES"
          :key="th.key"
          class="theme-tab"
          :class="{ 'theme-tab--active': th.key === selectedTheme }"
          @click="selectedTheme = th.key"
        >
          {{ th.label }}
        </button>
      </div>
    </div>

    <!-- Content -->
    <div class="overview-body">

      <!-- Empty state -->
      <div v-if="!selectedIso" class="empty-state">
        <div class="empty-icon">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <circle cx="16" cy="16" r="14" stroke="#ddd9cf" stroke-width="1.5" />
            <path d="M8 16c1.5-6 14.5-6 16 0M8 16c1.5 6 14.5 6 16 0M16 2v28M2 16h28" stroke="#ddd9cf" stroke-width="1.2" />
          </svg>
        </div>
        <div class="empty-title">Select a country</div>
        <div class="empty-desc">
          Choose a country above to see grounded indicators, SDG progress, and polycrisis risk — all sourced from live World Bank data with zero LLM calls.
        </div>
      </div>

      <!-- Loading -->
      <div v-else-if="loadingBrief" class="loading-state">
        <div class="loading-dots">
          <span></span><span></span><span></span>
        </div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;color:#9a9f97;letter-spacing:.05em;">Querying verified sources…</div>
      </div>

      <!-- Error -->
      <div v-else-if="errorBrief" class="error-state">
        <svg width="16" height="16" viewBox="0 0 16 16" style="flex:none;color:#c0392b;">
          <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.3" fill="none" />
          <path d="M8 4.5v4M8 10.5v1" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" />
        </svg>
        <span>{{ errorBrief }}</span>
      </div>

      <!-- Data -->
      <div v-else-if="brief" class="data-grid">

        <!-- Brief header -->
        <div class="brief-header">
          <div>
            <div class="brief-label">{{ brief.label }}</div>
            <div class="brief-country">{{ selectedCountryName }} · {{ themeLabel }}</div>
          </div>
          <div class="brief-meta">
            <span>{{ availableIndicators.length }} of {{ brief.indicators.length }} indicators available</span>
          </div>
        </div>

        <!-- KPI cards -->
        <div class="kpi-grid">
          <div
            v-for="ind in availableIndicators"
            :key="ind.code"
            class="kpi-card"
          >
            <div class="kpi-name">{{ ind.name }}</div>

            <div style="display:flex;align-items:flex-end;justify-content:space-between;gap:12px;margin-top:10px;">
              <div>
                <div v-if="latestObs(ind)" class="kpi-value">
                  {{ latestObs(ind)!.value.toLocaleString('en-US', { maximumFractionDigits: 1 }) }}
                  <span class="kpi-unit">{{ ind.unit }}</span>
                </div>
                <div v-if="latestObs(ind)" class="kpi-year">{{ latestObs(ind)!.year }}</div>
              </div>

              <template v-if="spark(ind.obs)">
                <svg viewBox="0 0 100 26" style="width:100px;height:26px;display:block;flex:none;">
                  <path :d="spark(ind.obs)!.area" style="fill:#eef2f5;stroke:none;" />
                  <path :d="spark(ind.obs)!.line" style="fill:none;stroke:#2c4a63;stroke-width:1.4px;stroke-linejoin:round;stroke-linecap:round;" />
                  <circle :cx="spark(ind.obs)!.dotX" :cy="spark(ind.obs)!.dotY" r="2" style="fill:#2c4a63;" />
                </svg>
              </template>
            </div>

            <!-- Claims row -->
            <div style="margin-top:11px;padding-top:10px;border-top:1px solid #f0ece4;display:flex;align-items:center;gap:7px;flex-wrap:wrap;">
              <span
                :style="tierStyle(ind.verification?.confidence_tier) + 'display:inline-block;padding:2px 6px;border-radius:2px;font-family:IBM Plex Mono,monospace;font-size:9.5px;letter-spacing:.03em;'"
              >{{ tierLabel(ind.verification?.confidence_tier) }}</span>

              <template v-if="ind.claims">
                <span
                  v-for="cl in ind.claims.slice(0, 2)"
                  :key="cl.id"
                  class="verdict-chip"
                  :style="'color:' + verdictIcon(cl.verdict).color"
                >
                  <span style="font-size:10px;">{{ verdictIcon(cl.verdict).symbol }}</span>
                  {{ cl.verdict === 'improving' ? 'Improving' : cl.verdict === 'off-track' ? 'Off-track' : cl.verdict === 'on-track' ? 'On-track' : cl.verdict }}
                </span>
              </template>
            </div>

            <!-- Headline claim -->
            <div v-if="ind.claims && ind.claims[0]" class="kpi-claim">
              {{ ind.claims[0].text }}
            </div>
          </div>

          <!-- Unavailable indicators -->
          <div
            v-for="ind in unavailableIndicators"
            :key="ind.code"
            class="kpi-card kpi-card--empty"
          >
            <div class="kpi-name">{{ ind.name }}</div>
            <div style="margin-top:8px;font-size:11.5px;color:#a7aaa2;display:flex;align-items:center;gap:6px;">
              <svg width="10" height="10" viewBox="0 0 10 10"><circle cx="5" cy="5" r="4" stroke="#cfccc1" stroke-width="1" fill="none"/><path d="M5 3v2.5M5 6.5v.5" stroke="#cfccc1" stroke-width="1" stroke-linecap="round"/></svg>
              No data available
            </div>
          </div>
        </div>

        <!-- Polycrisis band -->
        <div v-if="polycrisis" class="poly-section">
          <div class="section-head">
            <svg width="13" height="13" viewBox="0 0 14 14" style="flex:none;">
              <path d="M7 1l1.8 3.6L13 5.6l-3 2.9.7 4.1L7 10.5l-3.7 2.1.7-4.1L1 5.6l4.2-.6L7 1z" stroke="#2c4a63" stroke-width="1.1" fill="none" stroke-linejoin="round" />
            </svg>
            <span class="section-label">Polycrisis Risk</span>
          </div>

          <div class="poly-card">
            <div class="poly-band" :style="'border-left-color:' + BAND_COLOR[polycrisis.band]">
              <div>
                <div class="poly-band-label" :style="'color:' + BAND_COLOR[polycrisis.band]">
                  {{ BAND_LABEL[polycrisis.band] }}
                </div>
                <div style="font-size:12.5px;color:#5a6068;margin-top:3px;">
                  {{ polycrisis.stressed }} of {{ polycrisis.scored }} scored domains under stress
                </div>
              </div>
              <div class="poly-score">
                <span style="font-family:'IBM Plex Mono',monospace;font-size:28px;font-weight:500;color:#1b1e23;line-height:1;">{{ polycrisis.stressed }}</span>
                <span style="font-size:11px;color:#9a9f97;">/ {{ polycrisis.scored }}</span>
              </div>
            </div>

            <div class="poly-domains">
              <div
                v-for="d in polycrisis.domains.filter(x => x.available)"
                :key="d.indicator"
                class="poly-domain"
                :class="{ 'poly-domain--stressed': d.stressed }"
              >
                <div style="display:flex;align-items:center;gap:7px;">
                  <span
                    :style="'width:7px;height:7px;border-radius:50%;flex:none;background:' + (d.stressed ? BAND_COLOR.high : '#cfe0d4')"
                  ></span>
                  <span style="font-size:12px;font-weight:500;color:#33373d;">{{ d.domain }}</span>
                </div>
                <div v-if="d.value != null" style="font-family:'IBM Plex Mono',monospace;font-size:11px;color:#5a6068;margin-top:3px;padding-left:14px;">
                  {{ d.value.toLocaleString('en-US', { maximumFractionDigits: 1 }) }}
                  <span style="color:#a7aaa2;margin-left:2px;">{{ d.unit }}</span>
                  <span style="color:#bfc2b9;margin-left:5px;">{{ d.year }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Polycrisis loading -->
        <div v-else-if="loadingPoly" class="poly-section">
          <div class="section-head">
            <span class="section-label">Polycrisis Risk</span>
          </div>
          <div style="height:60px;display:flex;align-items:center;justify-content:center;">
            <span style="font-family:'IBM Plex Mono',monospace;font-size:11px;color:#bfc2b9;">Loading…</span>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script lang="ts">
// v-click-outside directive
export default {
  directives: {
    clickOutside: {
      mounted(el: HTMLElement, binding: { value: () => void }) {
        ;(el as unknown as Record<string, unknown>)._clickOutsideHandler = (e: MouseEvent) => {
          if (!el.contains(e.target as Node)) binding.value()
        }
        document.addEventListener(
          'click',
          (el as unknown as Record<string, unknown>)._clickOutsideHandler as EventListener,
        )
      },
      unmounted(el: HTMLElement) {
        document.removeEventListener(
          'click',
          (el as unknown as Record<string, unknown>)._clickOutsideHandler as EventListener,
        )
      },
    },
  },
}
</script>

<style scoped>
.overview-root {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  background: #f4f3ef;
}

.controls-bar {
  flex: none;
  border-bottom: 1px solid #e3e1da;
  background: #f7f6f3;
  padding: 10px 20px;
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

/* Country selector */
.selector-wrap {
  position: relative;
  flex: none;
}

.selector-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 11px;
  background: #fff;
  border: 1px solid #ddd9cf;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  color: #33373d;
  min-width: 200px;
}
.selector-btn:hover,
.selector-btn--active {
  border-color: #2c4a63;
}

.selector-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  z-index: 50;
  background: #fff;
  border: 1px solid #ddd9cf;
  border-radius: 4px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  width: 260px;
}

.search-input {
  width: 100%;
  box-sizing: border-box;
  border: 1px solid #e3e1da;
  border-radius: 3px;
  padding: 6px 9px;
  font-size: 13px;
  outline: none;
  background: #faf9f6;
}
.search-input:focus {
  border-color: #2c4a63;
}

.dropdown-list {
  max-height: 280px;
  overflow-y: auto;
  padding: 4px;
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 8px;
  border: none;
  border-radius: 3px;
  background: transparent;
  cursor: pointer;
  font-size: 13px;
  color: #33373d;
  text-align: left;
}
.dropdown-item:hover {
  background: #f0ede5;
}
.dropdown-item--active {
  background: #edf0f3;
  color: #2c4a63;
  font-weight: 500;
}

/* Theme tabs */
.theme-tabs {
  display: flex;
  gap: 3px;
  flex-wrap: wrap;
}

.theme-tab {
  padding: 5px 11px;
  border: 1px solid transparent;
  border-radius: 3px;
  background: transparent;
  cursor: pointer;
  font-size: 12.5px;
  color: #6a6f68;
  white-space: nowrap;
}
.theme-tab:hover {
  background: #ece9e1;
  color: #33373d;
}
.theme-tab--active {
  background: #fff;
  border-color: #ddd9cf;
  color: #2c4a63;
  font-weight: 500;
}

/* Overview body */
.overview-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px 24px 48px;
}

/* Empty / loading / error */
.empty-state {
  max-width: 440px;
  margin: 10vh auto 0;
  text-align: center;
  padding: 0 20px;
}
.empty-icon {
  margin-bottom: 20px;
}
.empty-title {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #a7aaa2;
  margin-bottom: 10px;
}
.empty-desc {
  font-size: 14px;
  line-height: 1.65;
  color: #6a6f68;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  padding: 10vh 0 0;
}
.loading-dots {
  display: flex;
  gap: 6px;
}
.loading-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #2c4a63;
  animation: dotPulse 1.2s ease-in-out infinite;
}
.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes dotPulse {
  0%, 80%, 100% { opacity: 0.25; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1); }
}

.error-state {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 14px 16px;
  background: #fdf3f2;
  border: 1px solid #f5c6c2;
  border-radius: 4px;
  font-size: 13px;
  color: #c0392b;
  max-width: 520px;
  margin: 24px auto;
}

/* Data grid */
.data-grid {
  max-width: 1100px;
  margin: 0 auto;
}

.brief-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.brief-label {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #8a6516;
  margin-bottom: 5px;
}
.brief-country {
  font-size: 20px;
  font-weight: 500;
  color: #1b1e23;
  letter-spacing: -0.01em;
}
.brief-meta {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10.5px;
  color: #a7aaa2;
  padding-top: 4px;
}

/* KPI grid */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
  margin-bottom: 28px;
}

.kpi-card {
  background: #fff;
  border: 1px solid #e3e1da;
  border-radius: 5px;
  padding: 16px 16px 14px;
}
.kpi-card--empty {
  opacity: 0.55;
}

.kpi-name {
  font-size: 12.5px;
  font-weight: 500;
  color: #42474e;
  line-height: 1.35;
}

.kpi-value {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 26px;
  font-weight: 500;
  color: #1b1e23;
  line-height: 1;
  letter-spacing: -0.01em;
  display: flex;
  align-items: baseline;
  gap: 5px;
}
.kpi-unit {
  font-size: 11px;
  font-weight: 400;
  color: #9a9f97;
}
.kpi-year {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  color: #a7aaa2;
  margin-top: 3px;
}

.verdict-chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.02em;
}

.kpi-claim {
  margin-top: 8px;
  font-size: 11.5px;
  line-height: 1.5;
  color: #6a6f68;
  border-left: 2px solid #e3e1da;
  padding-left: 9px;
}

/* Polycrisis section */
.poly-section {
  margin-top: 8px;
}

.section-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.section-label {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10.5px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #33373d;
  font-weight: 500;
}

.poly-card {
  background: #fff;
  border: 1px solid #e3e1da;
  border-radius: 5px;
  overflow: hidden;
}

.poly-band {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 18px;
  border-bottom: 1px solid #f0ece4;
  border-left: 4px solid transparent;
}

.poly-band-label {
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.01em;
}

.poly-score {
  display: flex;
  align-items: baseline;
  gap: 3px;
}

.poly-domains {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1px;
  background: #f0ece4;
}

.poly-domain {
  background: #faf9f6;
  padding: 10px 14px;
}
.poly-domain--stressed {
  background: #fff8f7;
}
</style>
