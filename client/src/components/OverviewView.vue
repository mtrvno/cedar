<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
import { getCountries, getBrief, getPolycrisis, getBlindspots, getDrilldown } from '@/api/cedar'
import type {
  Country,
  BriefResponse,
  BriefIndicator,
  PolycrisisResponse,
  BlindspotsResponse,
  DrilldownResponse,
} from '@/types/api'
import { useEvidenceLedger } from '@/composables/useEvidenceLedger'

const { setLedger } = useEvidenceLedger()

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
const blindspots = ref<BlindspotsResponse | null>(null)
const loadingBrief = ref(false)
const loadingPoly = ref(false)
const loadingBlind = ref(false)
const errorBrief = ref<string | null>(null)
const errorPoly = ref<string | null>(null)
const drilldown = ref<DrilldownResponse | null>(null)
const loadingDrill = ref(false)
const collapsedPoly = ref(false)
const collapsedGaps = ref(false)
const collapsedDrill = ref(false)

const compareIso = ref('')
const compareSearch = ref('')
const compareDropdownOpen = ref(false)
const brief2 = ref<BriefResponse | null>(null)
const polycrisis2 = ref<PolycrisisResponse | null>(null)
const loadingBrief2 = ref(false)
const loadingPoly2 = ref(false)
const errorBrief2 = ref<string | null>(null)

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
    if (brief.value) {
      setLedger(
        selectedIso.value,
        selectedCountryName.value,
        selectedTheme.value,
        brief.value.indicators,
        brief.value.cost,
      )
    }
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

async function fetchBlindspots() {
  if (!selectedIso.value) return
  loadingBlind.value = true
  blindspots.value = null
  try {
    blindspots.value = await getBlindspots(selectedIso.value)
  } catch {
    // non-critical, silent fail
  } finally {
    loadingBlind.value = false
  }
}

watch([selectedIso, selectedTheme], () => {
  if (selectedIso.value) fetchBrief()
})

async function fetchDrilldown() {
  if (!selectedIso.value) return
  loadingDrill.value = true
  drilldown.value = null
  try {
    drilldown.value = await getDrilldown(selectedIso.value)
  } catch {
    // not all countries have equity data — silent fail
  } finally {
    loadingDrill.value = false
  }
}

watch(selectedIso, () => {
  if (selectedIso.value) {
    fetchPolycrisis()
    fetchBlindspots()
    fetchDrilldown()
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
  if (mx === mn) {
    mx = mn + 1
    mn = mn - 1
  }
  const X = (i: number) => p + (i * (w - 2 * p)) / (entries.length - 1)
  const Y = (v: number) => h - p - ((v - mn) / (mx - mn)) * (h - 2 * p)
  let line = ''
  vals.forEach((v, i) => {
    line += (i ? 'L' : 'M') + X(i).toFixed(1) + ' ' + Y(v).toFixed(1) + ' '
  })
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

function latestObs(
  obs: Record<string, number> | undefined,
): { year: string; value: number } | null {
  if (!obs) return null
  const entries = Object.entries(obs)
    .filter(([, v]) => v != null)
    .sort((a, b) => parseInt(b[0]) - parseInt(a[0]))
  const top = entries[0]
  if (!top) return null
  return { year: top[0], value: top[1] as number }
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
  if (v === 'off-track') return { symbol: '✗', color: '#c0392b' }
  if (v === 'on-track') return { symbol: '✓', color: '#2f6b4f' }
  return { symbol: '—', color: '#9a9f97' }
}

type RichIndicator = BriefIndicator & {
  lo: { year: string; value: number } | null
  sp: ReturnType<typeof spark>
}

const availableIndicators = computed<RichIndicator[]>(() =>
  (brief.value?.indicators ?? [])
    .filter((i) => i.available)
    .map((i) => ({ ...i, lo: latestObs(i.obs), sp: spark(i.obs) })),
)
const unavailableIndicators = computed(() =>
  (brief.value?.indicators ?? []).filter((i) => !i.available),
)

const themeLabel = computed(
  () => THEMES.find((t) => t.key === selectedTheme.value)?.label ?? selectedTheme.value,
)

const filteredCompareCountries = computed(() => {
  const q = compareSearch.value.toLowerCase().trim()
  if (!q) return countries.value
  return countries.value.filter(
    (c) => c.name.toLowerCase().includes(q) || c.iso3.toLowerCase().includes(q),
  )
})

const compareName = computed(
  () => countries.value.find((c) => c.iso3 === compareIso.value)?.name ?? '',
)

const isComparing = computed(() => !!compareIso.value)

function selectCompare(c: Country) {
  compareIso.value = c.iso3
  compareSearch.value = ''
  compareDropdownOpen.value = false
}

function clearCompare() {
  compareIso.value = ''
  brief2.value = null
  polycrisis2.value = null
}

async function fetchBrief2() {
  if (!compareIso.value) return
  loadingBrief2.value = true
  errorBrief2.value = null
  brief2.value = null
  try {
    brief2.value = await getBrief(compareIso.value, selectedTheme.value)
  } catch (e) {
    errorBrief2.value = e instanceof Error ? e.message : 'Failed to load'
  } finally {
    loadingBrief2.value = false
  }
}

async function fetchPolycrisis2() {
  if (!compareIso.value) return
  loadingPoly2.value = true
  polycrisis2.value = null
  try {
    polycrisis2.value = await getPolycrisis(compareIso.value)
  } catch {
    // silent
  } finally {
    loadingPoly2.value = false
  }
}

watch([compareIso, selectedTheme], () => {
  if (compareIso.value) fetchBrief2()
})

watch(compareIso, () => {
  if (compareIso.value) fetchPolycrisis2()
})

const compareRows = computed(() => {
  if (!brief.value && !brief2.value) return []
  const map1 = new Map((brief.value?.indicators ?? []).map((i) => [i.code, i]))
  const map2 = new Map((brief2.value?.indicators ?? []).map((i) => [i.code, i]))
  const codes = [...new Set([...map1.keys(), ...map2.keys()])]
  return codes.map((code) => {
    const a = map1.get(code) ?? null
    const b = map2.get(code) ?? null
    return {
      code,
      name: (a?.name ?? b?.name ?? code) as string,
      unit: (a?.unit ?? b?.unit ?? '') as string,
      a: a ? { ...a, lo: latestObs(a.obs), sp: spark(a.obs) } : null,
      b: b ? { ...b, lo: latestObs(b.obs), sp: spark(b.obs) } : null,
    }
  })
})
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
          <svg width="11" height="11" viewBox="0 0 12 12" style="flex: none; color: #6a6f68">
            <circle cx="6" cy="6" r="4.5" stroke="currentColor" stroke-width="1.3" fill="none" />
            <path
              d="M4 6.5C4.5 8.5 7.5 8.5 8 6.5M4 5.5c.5-2 3.5-2 4 0"
              stroke="currentColor"
              stroke-width="1"
              fill="none"
            />
            <path d="M3 6h6M6 3v6" stroke="currentColor" stroke-width="1" stroke-linecap="round" />
          </svg>
          <span v-if="selectedCountryName">{{ selectedCountryName }}</span>
          <span v-else style="color: #a7aaa2">Select country…</span>
          <svg
            width="10"
            height="10"
            viewBox="0 0 10 10"
            style="flex: none; margin-left: auto; color: #9a9f97"
          >
            <path
              d="M2.5 3.5l2.5 3 2.5-3"
              stroke="currentColor"
              stroke-width="1.2"
              fill="none"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </button>

        <div v-if="dropdownOpen" class="selector-dropdown">
          <div style="padding: 8px 10px; border-bottom: 1px solid #ece9e1">
            <input v-model="countrySearch" placeholder="Search…" class="search-input" autofocus />
          </div>
          <div class="dropdown-list">
            <button
              v-for="c in filteredCountries"
              :key="c.iso3"
              class="dropdown-item"
              :class="{ 'dropdown-item--active': c.iso3 === selectedIso }"
              @click="selectCountry(c)"
            >
              <span
                style="
                  font-family: 'IBM Plex Mono', monospace;
                  font-size: 10px;
                  color: #9a9f97;
                  flex: none;
                  width: 30px;
                "
                >{{ c.iso3 }}</span
              >
              {{ c.name }}
            </button>
            <div
              v-if="filteredCountries.length === 0"
              style="padding: 12px 12px; font-size: 13px; color: #a7aaa2"
            >
              No matches
            </div>
          </div>
        </div>
      </div>

      <!-- Compare selector -->
      <div
        v-if="selectedIso && !isComparing"
        class="selector-wrap"
        v-click-outside="() => (compareDropdownOpen = false)"
      >
        <button
          class="selector-btn selector-btn--compare"
          :class="{ 'selector-btn--active': compareDropdownOpen }"
          @click="compareDropdownOpen = !compareDropdownOpen"
        >
          <svg width="11" height="11" viewBox="0 0 12 12" style="flex: none; color: #9a9f97">
            <path
              d="M2 6h8M6 2v8"
              stroke="currentColor"
              stroke-width="1.3"
              stroke-linecap="round"
            />
          </svg>
          <span style="color: #a7aaa2">Compare with…</span>
          <svg
            width="10"
            height="10"
            viewBox="0 0 10 10"
            style="flex: none; margin-left: auto; color: #9a9f97"
          >
            <path
              d="M2.5 3.5l2.5 3 2.5-3"
              stroke="currentColor"
              stroke-width="1.2"
              fill="none"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </button>
        <div v-if="compareDropdownOpen" class="selector-dropdown">
          <div style="padding: 8px 10px; border-bottom: 1px solid #ece9e1">
            <input v-model="compareSearch" placeholder="Search…" class="search-input" autofocus />
          </div>
          <div class="dropdown-list">
            <button
              v-for="c in filteredCompareCountries"
              :key="c.iso3"
              class="dropdown-item"
              :class="{ 'dropdown-item--active': c.iso3 === compareIso }"
              @click="selectCompare(c)"
            >
              <span
                style="
                  font-family: 'IBM Plex Mono', monospace;
                  font-size: 10px;
                  color: #9a9f97;
                  flex: none;
                  width: 30px;
                "
                >{{ c.iso3 }}</span
              >
              {{ c.name }}
            </button>
            <div
              v-if="filteredCompareCountries.length === 0"
              style="padding: 12px; font-size: 13px; color: #a7aaa2"
            >
              No matches
            </div>
          </div>
        </div>
      </div>

      <!-- Compare active tag -->
      <div v-if="isComparing" class="compare-tag">
        <span
          style="width: 7px; height: 7px; border-radius: 50%; background: #9db1c2; flex: none"
        ></span>
        {{ compareName }}
        <button @click="clearCompare" class="compare-clear-btn" title="Remove comparison">×</button>
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
            <path
              d="M8 16c1.5-6 14.5-6 16 0M8 16c1.5 6 14.5 6 16 0M16 2v28M2 16h28"
              stroke="#ddd9cf"
              stroke-width="1.2"
            />
          </svg>
        </div>
        <div class="empty-title">Select a country</div>
        <div class="empty-desc">
          Choose a country above to see grounded indicators, SDG progress, and polycrisis risk — all
          sourced from live World Bank data with zero LLM calls.
        </div>
      </div>

      <!-- Comparison view -->
      <div v-else-if="isComparing" class="compare-body">
        <!-- Country summary header -->
        <div class="compare-summary">
          <div class="compare-summary-card compare-summary-card--a">
            <div class="compare-summary-name">{{ selectedCountryName }}</div>
            <div
              v-if="polycrisis"
              class="compare-poly-band"
              :style="'color:' + BAND_COLOR[polycrisis.band]"
            >
              {{ BAND_LABEL[polycrisis.band] }}
            </div>
            <div
              v-else-if="loadingPoly"
              style="font-size: 11px; color: #bfc2b9; font-family: 'IBM Plex Mono', monospace"
            >
              Loading…
            </div>
          </div>
          <div class="compare-vs-label">vs</div>
          <div class="compare-summary-card compare-summary-card--b">
            <div class="compare-summary-name">{{ compareName }}</div>
            <div
              v-if="polycrisis2"
              class="compare-poly-band"
              :style="'color:' + BAND_COLOR[polycrisis2.band]"
            >
              {{ BAND_LABEL[polycrisis2.band] }}
            </div>
            <div
              v-else-if="loadingPoly2"
              style="font-size: 11px; color: #bfc2b9; font-family: 'IBM Plex Mono', monospace"
            >
              Loading…
            </div>
          </div>
        </div>

        <!-- Loading -->
        <div v-if="loadingBrief || loadingBrief2" class="loading-state">
          <div class="loading-dots"><span></span><span></span><span></span></div>
          <div
            style="
              font-family: 'IBM Plex Mono', monospace;
              font-size: 11px;
              color: #9a9f97;
              letter-spacing: 0.05em;
            "
          >
            Loading comparison…
          </div>
        </div>

        <!-- Comparison table -->
        <div v-else-if="compareRows.length" class="compare-table-wrap">
          <div class="compare-table-header">
            <div class="ctcol ctcol--label">{{ themeLabel }}</div>
            <div class="ctcol ctcol--heading ctcol--heading-a">{{ selectedCountryName }}</div>
            <div class="ctcol ctcol--heading ctcol--heading-b">{{ compareName }}</div>
          </div>
          <div v-for="row in compareRows" :key="row.code" class="compare-row">
            <!-- Indicator name -->
            <div class="ctcol ctcol--name-cell">
              <div class="compare-ind-name">{{ row.name }}</div>
              <div
                style="
                  font-family: 'IBM Plex Mono', monospace;
                  font-size: 9px;
                  color: #bfc2b9;
                  margin-top: 2px;
                "
              >
                {{ row.code }}
              </div>
            </div>
            <!-- Country A -->
            <div class="ctcol ctcol--data">
              <template v-if="row.a?.available && row.a.lo">
                <div class="compare-cell-value">
                  {{ row.a.lo.value.toLocaleString('en-US', { maximumFractionDigits: 1 }) }}
                  <span class="compare-cell-unit">{{ row.unit }}</span>
                </div>
                <div
                  style="
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    margin-top: 4px;
                    gap: 8px;
                  "
                >
                  <span
                    style="
                      font-family: 'IBM Plex Mono', monospace;
                      font-size: 9.5px;
                      color: #a7aaa2;
                    "
                    >{{ row.a.lo.year }}</span
                  >
                  <svg
                    v-if="row.a.sp"
                    viewBox="0 0 100 26"
                    style="width: 68px; height: 19px; flex: none"
                  >
                    <path :d="row.a.sp.area" style="fill: #eef2f5; stroke: none" />
                    <path
                      :d="row.a.sp.line"
                      style="
                        fill: none;
                        stroke: #2c4a63;
                        stroke-width: 1.4px;
                        stroke-linejoin: round;
                        stroke-linecap: round;
                      "
                    />
                    <circle :cx="row.a.sp.dotX" :cy="row.a.sp.dotY" r="2" style="fill: #2c4a63" />
                  </svg>
                </div>
                <span
                  v-if="row.a.verification?.confidence_tier"
                  :style="
                    tierStyle(row.a.verification.confidence_tier) +
                    'display:inline-block;padding:2px 5px;border-radius:2px;font-family:IBM Plex Mono,monospace;font-size:9px;margin-top:6px'
                  "
                  >{{ tierLabel(row.a.verification.confidence_tier) }} confidence</span
                >
              </template>
              <span v-else style="font-size: 11px; color: #bfc2b9">No data</span>
            </div>
            <!-- Country B -->
            <div class="ctcol ctcol--data">
              <template v-if="row.b?.available && row.b.lo">
                <div class="compare-cell-value">
                  {{ row.b.lo.value.toLocaleString('en-US', { maximumFractionDigits: 1 }) }}
                  <span class="compare-cell-unit">{{ row.unit }}</span>
                </div>
                <div
                  style="
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    margin-top: 4px;
                    gap: 8px;
                  "
                >
                  <span
                    style="
                      font-family: 'IBM Plex Mono', monospace;
                      font-size: 9.5px;
                      color: #a7aaa2;
                    "
                    >{{ row.b.lo.year }}</span
                  >
                  <svg
                    v-if="row.b.sp"
                    viewBox="0 0 100 26"
                    style="width: 68px; height: 19px; flex: none"
                  >
                    <path :d="row.b.sp.area" style="fill: #eef2f5; stroke: none" />
                    <path
                      :d="row.b.sp.line"
                      style="
                        fill: none;
                        stroke: #9db1c2;
                        stroke-width: 1.4px;
                        stroke-linejoin: round;
                        stroke-linecap: round;
                      "
                    />
                    <circle :cx="row.b.sp.dotX" :cy="row.b.sp.dotY" r="2" style="fill: #9db1c2" />
                  </svg>
                </div>
                <span
                  v-if="row.b.verification?.confidence_tier"
                  :style="
                    tierStyle(row.b.verification.confidence_tier) +
                    'display:inline-block;padding:2px 5px;border-radius:2px;font-family:IBM Plex Mono,monospace;font-size:9px;margin-top:6px'
                  "
                  >{{ tierLabel(row.b.verification.confidence_tier) }} confidence</span
                >
              </template>
              <span v-else style="font-size: 11px; color: #bfc2b9">No data</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Split layout: country selected -->
      <div v-else class="content-layout">
        <!-- Main col: brief + KPI cards -->
        <div class="main-col">
          <!-- Loading -->
          <div v-if="loadingBrief" class="loading-state">
            <div class="loading-dots"><span></span><span></span><span></span></div>
            <div
              style="
                font-family: 'IBM Plex Mono', monospace;
                font-size: 11px;
                color: #9a9f97;
                letter-spacing: 0.05em;
              "
            >
              Querying verified sources…
            </div>
          </div>

          <!-- Error -->
          <div v-else-if="errorBrief" class="error-state">
            <svg width="16" height="16" viewBox="0 0 16 16" style="flex: none; color: #c0392b">
              <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.3" fill="none" />
              <path
                d="M8 4.5v4M8 10.5v1"
                stroke="currentColor"
                stroke-width="1.4"
                stroke-linecap="round"
              />
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
                <span
                  >{{ availableIndicators.length }} of {{ brief.indicators.length }} indicators
                  available</span
                >
              </div>
            </div>

            <!-- KPI cards -->
            <div class="kpi-grid">
              <div v-for="ind in availableIndicators" :key="ind.code" class="kpi-card">
                <div class="kpi-name">{{ ind.name }}</div>

                <div
                  style="
                    display: flex;
                    align-items: flex-end;
                    justify-content: space-between;
                    gap: 12px;
                    margin-top: 10px;
                  "
                >
                  <div>
                    <div v-if="ind.lo" class="kpi-value">
                      {{ ind.lo.value.toLocaleString('en-US', { maximumFractionDigits: 1 }) }}
                      <span class="kpi-unit">{{ ind.unit }}</span>
                    </div>
                    <div v-if="ind.lo" class="kpi-year">{{ ind.lo.year }}</div>
                  </div>
                  <svg
                    v-if="ind.sp"
                    viewBox="0 0 100 26"
                    style="width: 100px; height: 26px; display: block; flex: none"
                  >
                    <path :d="ind.sp.area" style="fill: #eef2f5; stroke: none" />
                    <path
                      :d="ind.sp.line"
                      style="
                        fill: none;
                        stroke: #2c4a63;
                        stroke-width: 1.4px;
                        stroke-linejoin: round;
                        stroke-linecap: round;
                      "
                    />
                    <circle :cx="ind.sp.dotX" :cy="ind.sp.dotY" r="2" style="fill: #2c4a63" />
                  </svg>
                </div>

                <!-- Claims row -->
                <div
                  style="
                    margin-top: 11px;
                    padding-top: 10px;
                    border-top: 1px solid #f0ece4;
                    display: flex;
                    align-items: center;
                    gap: 7px;
                    flex-wrap: wrap;
                  "
                >
                  <span
                    :style="
                      tierStyle(ind.verification?.confidence_tier) +
                      'display:inline-block;padding:2px 6px;border-radius:2px;font-family:IBM Plex Mono,monospace;font-size:9.5px;letter-spacing:.03em;'
                    "
                  >
                    {{ tierLabel(ind.verification?.confidence_tier) }} confidence
                  </span>
                  <template v-if="ind.claims">
                    <span
                      v-for="cl in ind.claims.slice(0, 2)"
                      :key="cl.id"
                      class="verdict-chip"
                      :style="'color:' + verdictIcon(cl.verdict).color"
                    >
                      <span style="font-size: 10px">{{ verdictIcon(cl.verdict).symbol }}</span>
                      {{
                        cl.verdict === 'improving'
                          ? 'Improving'
                          : cl.verdict === 'off-track'
                            ? 'Off-track'
                            : cl.verdict === 'on-track'
                              ? 'On-track'
                              : cl.verdict
                      }}
                    </span>
                  </template>
                </div>

                <!-- Headline claim -->
                <div v-if="ind.claims && ind.claims[0]" class="kpi-claim">
                  {{ ind.claims[0].text }}
                </div>

                <!-- Provenance link -->
                <div v-if="ind.provenance?.query_url" style="margin-top: 8px">
                  <a
                    :href="ind.provenance.query_url"
                    target="_blank"
                    rel="noopener"
                    class="prov-link"
                    >Source ↗</a
                  >
                </div>
              </div>

              <!-- Unavailable -->
              <div
                v-for="ind in unavailableIndicators"
                :key="ind.code"
                class="kpi-card kpi-card--empty"
              >
                <div class="kpi-name">{{ ind.name }}</div>
                <div
                  style="
                    margin-top: 8px;
                    font-size: 11.5px;
                    color: #a7aaa2;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                  "
                >
                  <svg width="10" height="10" viewBox="0 0 10 10">
                    <circle cx="5" cy="5" r="4" stroke="#cfccc1" stroke-width="1" fill="none" />
                    <path
                      d="M5 3v2.5M5 6.5v.5"
                      stroke="#cfccc1"
                      stroke-width="1"
                      stroke-linecap="round"
                    />
                  </svg>
                  No data available
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right sidebar: country-level, persists across theme changes -->
        <aside class="country-rail">
          <div class="rail-country-name">{{ selectedCountryName }}</div>

          <!-- Polycrisis -->
          <div class="rail-section">
            <button class="rail-section-head" @click="collapsedPoly = !collapsedPoly">
              <svg width="13" height="13" viewBox="0 0 14 14" style="flex: none">
                <path
                  d="M7 1l1.8 3.6L13 5.6l-3 2.9.7 4.1L7 10.5l-3.7 2.1.7-4.1L1 5.6l4.2-.6L7 1z"
                  stroke="#2c4a63"
                  stroke-width="1.1"
                  fill="none"
                  stroke-linejoin="round"
                />
              </svg>
              <span class="section-label">Polycrisis Risk</span>
              <span
                v-if="polycrisis"
                :style="
                  'margin-left:4px;font-family:IBM Plex Mono,monospace;font-size:10px;color:' +
                  BAND_COLOR[polycrisis.band]
                "
              >
                {{ BAND_LABEL[polycrisis.band] }}
              </span>
              <svg
                class="rail-chevron"
                :class="{ 'rail-chevron--open': !collapsedPoly }"
                width="10"
                height="10"
                viewBox="0 0 10 10"
              >
                <path
                  d="M2 3.5l3 3 3-3"
                  stroke="#9a9f97"
                  stroke-width="1.2"
                  fill="none"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </button>

            <div v-show="!collapsedPoly">
              <div
                v-if="loadingPoly"
                style="height: 48px; display: flex; align-items: center; justify-content: center"
              >
                <span
                  style="font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: #bfc2b9"
                  >Loading…</span
                >
              </div>

              <div v-else-if="polycrisis">
                <div
                  class="poly-band-rail"
                  :style="'border-left-color:' + BAND_COLOR[polycrisis.band]"
                >
                  <div class="poly-band-label" :style="'color:' + BAND_COLOR[polycrisis.band]">
                    {{ BAND_LABEL[polycrisis.band] }}
                  </div>
                  <div style="font-size: 11.5px; color: #5a6068; margin-top: 2px">
                    {{ polycrisis.stressed }}/{{ polycrisis.scored }} domains stressed
                  </div>
                </div>
                <div class="poly-domain-list">
                  <div
                    v-for="d in polycrisis.domains.filter((x) => x.available)"
                    :key="d.indicator"
                    class="rail-domain"
                  >
                    <span
                      :style="
                        'width:6px;height:6px;border-radius:50%;flex:none;display:inline-block;background:' +
                        (d.stressed ? BAND_COLOR.high : '#cfe0d4')
                      "
                    ></span>
                    <span style="flex: 1; font-size: 11.5px; color: #33373d">{{ d.domain }}</span>
                    <span
                      v-if="d.value != null"
                      style="
                        font-family: 'IBM Plex Mono', monospace;
                        font-size: 10px;
                        color: #9a9f97;
                      "
                    >
                      {{ d.value.toLocaleString('en-US', { maximumFractionDigits: 1 }) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Data gaps -->
          <div class="rail-section">
            <button class="rail-section-head" @click="collapsedGaps = !collapsedGaps">
              <svg width="13" height="13" viewBox="0 0 14 14" style="flex: none">
                <circle cx="7" cy="7" r="5.5" stroke="#2c4a63" stroke-width="1.1" fill="none" />
                <path
                  d="M7 4v3.5M7 9v.5"
                  stroke="#2c4a63"
                  stroke-width="1.3"
                  stroke-linecap="round"
                />
              </svg>
              <span class="section-label">Data Gaps</span>
              <span
                v-if="blindspots"
                style="
                  margin-left: 4px;
                  font-family: 'IBM Plex Mono', monospace;
                  font-size: 10px;
                  color: #9a9f97;
                "
              >
                {{ blindspots.gaps }}/{{ blindspots.total }}
              </span>
              <svg
                class="rail-chevron"
                :class="{ 'rail-chevron--open': !collapsedGaps }"
                width="10"
                height="10"
                viewBox="0 0 10 10"
              >
                <path
                  d="M2 3.5l3 3 3-3"
                  stroke="#9a9f97"
                  stroke-width="1.2"
                  fill="none"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </button>

            <div v-show="!collapsedGaps">
              <div
                v-if="loadingBlind"
                style="height: 40px; display: flex; align-items: center; justify-content: center"
              >
                <span
                  style="font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: #bfc2b9"
                  >Loading…</span
                >
              </div>

              <div v-else-if="blindspots" class="gap-list">
                <div v-for="g in blindspots.indicators" :key="g.indicator" class="rail-gap">
                  <span class="rail-gap-dot" :class="'rail-gap-dot--' + g.status"></span>
                  <span style="flex: 1; font-size: 11.5px; color: #33373d; line-height: 1.3">{{
                    g.name
                  }}</span>
                  <span
                    style="
                      font-family: 'IBM Plex Mono', monospace;
                      font-size: 10px;
                      color: #bfc2b9;
                      flex: none;
                    "
                  >
                    {{ g.latest ?? '—' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          <!-- Equity drilldown -->
          <div v-if="drilldown || loadingDrill" class="rail-section">
            <button class="rail-section-head" @click="collapsedDrill = !collapsedDrill">
              <svg width="13" height="13" viewBox="0 0 14 14" style="flex: none">
                <rect
                  x="1"
                  y="8"
                  width="3"
                  height="5"
                  rx="0.5"
                  stroke="#2c4a63"
                  stroke-width="1.1"
                  fill="none"
                />
                <rect
                  x="5.5"
                  y="5"
                  width="3"
                  height="8"
                  rx="0.5"
                  stroke="#2c4a63"
                  stroke-width="1.1"
                  fill="none"
                />
                <rect
                  x="10"
                  y="2"
                  width="3"
                  height="11"
                  rx="0.5"
                  stroke="#2c4a63"
                  stroke-width="1.1"
                  fill="none"
                />
              </svg>
              <span class="section-label">Equity Drilldown</span>
              <span
                v-if="drilldown"
                style="
                  margin-left: 4px;
                  font-family: 'IBM Plex Mono', monospace;
                  font-size: 10px;
                  color: #9a9f97;
                "
              >
                {{ drilldown.year }}
              </span>
              <svg
                class="rail-chevron"
                :class="{ 'rail-chevron--open': !collapsedDrill }"
                width="10"
                height="10"
                viewBox="0 0 10 10"
              >
                <path
                  d="M2 3.5l3 3 3-3"
                  stroke="#9a9f97"
                  stroke-width="1.2"
                  fill="none"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </button>

            <div v-show="!collapsedDrill">
              <div
                v-if="loadingDrill"
                style="height: 48px; display: flex; align-items: center; justify-content: center"
              >
                <span
                  style="font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: #bfc2b9"
                  >Loading…</span
                >
              </div>

              <div v-else-if="drilldown">
                <!-- Gap summary -->
                <div v-if="drilldown.gap_points != null" class="drill-summary">
                  <span style="font-size: 11.5px; color: #5a6068">Poorest vs richest gap</span>
                  <span
                    style="
                      font-family: 'IBM Plex Mono', monospace;
                      font-size: 13px;
                      font-weight: 600;
                      color: #c0392b;
                    "
                  >
                    {{ drilldown.gap_points > 0 ? '+' : ''
                    }}{{ drilldown.gap_points.toFixed(1) }} pp
                  </span>
                </div>

                <!-- Quintile bars -->
                <div class="drill-bars">
                  <div v-for="(q, i) in drilldown.quintiles" :key="q.code" class="drill-bar-row">
                    <div class="drill-bar-label">Q{{ i + 1 }}</div>
                    <div class="drill-bar-track">
                      <div
                        class="drill-bar-fill"
                        :style="
                          'width:' +
                          (q.value != null && drilldown.quintiles[0].value != null
                            ? Math.min(
                                100,
                                (q.value /
                                  Math.max(...drilldown.quintiles.map((x) => x.value ?? 0))) *
                                  100,
                              )
                            : 0) +
                          '%;background:' +
                          (i === 0 ? '#c0392b' : i === 4 ? '#2f6b4f' : '#2c4a63')
                        "
                      ></div>
                    </div>
                    <div class="drill-bar-val">
                      {{ q.value != null ? q.value.toFixed(1) : '—' }}
                    </div>
                  </div>
                </div>

                <!-- National reference -->
                <div v-if="drilldown.national != null" class="drill-national">
                  National avg: <strong>{{ drilldown.national.toFixed(1) }}</strong>
                </div>

                <div style="font-size: 10px; color: #a7aaa2; margin-top: 6px; line-height: 1.4">
                  Stunting rate (%) by wealth quintile
                </div>
              </div>
            </div>
          </div>
        </aside>
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
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* Two-column layout when country selected */
.content-layout {
  flex: 1;
  display: flex;
  min-height: 0;
  overflow: hidden;
}

/* Main column: scrollable brief content */
.main-col {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  padding: 24px 24px 48px;
}

/* Right sidebar: country-level data, fixed width */
.country-rail {
  width: 268px;
  flex: none;
  border-left: 1px solid #e3e1da;
  background: #faf9f6;
  overflow-y: auto;
  padding: 16px 14px 40px;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.rail-country-name {
  font-size: 13px;
  font-weight: 600;
  color: #1b1e23;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e3e1da;
}

.rail-section {
  margin-bottom: 20px;
}

.poly-band-rail {
  border-left: 3px solid transparent;
  padding: 9px 10px;
  background: #fff;
  border-radius: 0 4px 4px 0;
  margin-bottom: 10px;
  border: 1px solid #e3e1da;
  border-left-width: 3px;
}

.poly-domain-list {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.rail-domain {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 5px 6px;
  border-radius: 3px;
}
.rail-domain:hover {
  background: #f0ece4;
}

.gap-list {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.rail-gap {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 5px 6px;
  border-radius: 3px;
}
.rail-gap:hover {
  background: #f0ece4;
}

.rail-gap-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex: none;
}
.rail-gap-dot--recent {
  background: #2f6b4f;
}
.rail-gap-dot--stale {
  background: #9a6a16;
}
.rail-gap-dot--missing {
  background: #c0392b;
}

/* Equity drilldown */
.drill-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 7px 8px;
  background: #fff;
  border: 1px solid #e3e1da;
  border-radius: 4px;
  margin-bottom: 10px;
}

.drill-bars {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-bottom: 8px;
}

.drill-bar-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.drill-bar-label {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  color: #9a9f97;
  width: 16px;
  flex: none;
}

.drill-bar-track {
  flex: 1;
  height: 8px;
  background: #f0ece4;
  border-radius: 2px;
  overflow: hidden;
}

.drill-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.drill-bar-val {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  color: #5a6068;
  width: 32px;
  text-align: right;
  flex: none;
}

.drill-national {
  font-size: 11px;
  color: #6a6f68;
  padding: 5px 0;
  border-top: 1px solid #f0ece4;
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
.loading-dots span:nth-child(2) {
  animation-delay: 0.2s;
}
.loading-dots span:nth-child(3) {
  animation-delay: 0.4s;
}
@keyframes dotPulse {
  0%,
  80%,
  100% {
    opacity: 0.25;
    transform: scale(0.8);
  }
  40% {
    opacity: 1;
    transform: scale(1);
  }
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

.poly-band-label {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.01em;
}

.rail-section-head {
  display: flex;
  align-items: center;
  gap: 7px;
  width: 100%;
  background: none;
  border: none;
  padding: 6px 4px;
  margin-bottom: 8px;
  cursor: pointer;
  border-radius: 4px;
  text-align: left;
}
.rail-section-head:hover {
  background: #ece9e1;
}

.rail-chevron {
  margin-left: auto;
  flex: none;
  transition: transform 0.18s ease;
  transform: rotate(-90deg);
}
.rail-chevron--open {
  transform: rotate(0deg);
}

.prov-link {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  color: #2c4a63;
  text-decoration: none;
  opacity: 0.6;
}
.prov-link:hover {
  opacity: 1;
  text-decoration: underline;
}

/* ── Comparison mode ─────────────────────────────── */
.selector-btn--compare {
  min-width: 160px;
  font-style: italic;
}

.compare-tag {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 6px 10px 6px 12px;
  background: #edf0f3;
  border: 1px solid #c4d0da;
  border-radius: 4px;
  font-size: 13px;
  color: #2c4a63;
  font-weight: 500;
}
.compare-clear-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 17px;
  color: #9db1c2;
  line-height: 1;
  padding: 0 2px;
  margin-left: 2px;
}
.compare-clear-btn:hover {
  color: #2c4a63;
}

.compare-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  box-sizing: border-box;
}

.compare-summary {
  display: flex;
  align-items: stretch;
  gap: 10px;
  margin-bottom: 24px;
  max-width: 860px;
}
.compare-summary-card {
  flex: 1;
  background: #fff;
  border: 1px solid #e3e1da;
  border-radius: 5px;
  padding: 14px 16px;
}
.compare-summary-card--a {
  border-top: 3px solid #2c4a63;
}
.compare-summary-card--b {
  border-top: 3px solid #9db1c2;
}
.compare-summary-name {
  font-size: 15px;
  font-weight: 600;
  color: #1b1e23;
  margin-bottom: 5px;
}
.compare-poly-band {
  font-size: 11.5px;
  font-weight: 500;
  font-family: 'IBM Plex Mono', monospace;
}
.compare-vs-label {
  align-self: center;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  color: #bfc2b9;
  letter-spacing: 0.05em;
  flex: none;
}

.compare-table-wrap {
  background: #fff;
  border: 1px solid #e3e1da;
  border-radius: 5px;
  overflow: hidden;
}
.compare-table-header {
  display: grid;
  grid-template-columns: 200px 1fr 1fr;
  gap: 16px;
  padding: 10px 16px;
  background: #f7f6f3;
  border-bottom: 2px solid #e3e1da;
  align-items: center;
}
.ctcol--label {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #8a6516;
}
.ctcol--heading {
  font-size: 13px;
  font-weight: 600;
}
.ctcol--heading-a {
  color: #2c4a63;
}
.ctcol--heading-b {
  color: #5a7a93;
}

.compare-row {
  display: grid;
  grid-template-columns: 200px 1fr 1fr;
  gap: 16px;
  padding: 14px 16px;
  border-bottom: 1px solid #f0ede5;
}
.compare-row:last-child {
  border-bottom: none;
}
.compare-row:hover {
  background: #faf9f6;
}

.ctcol--name-cell {
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.ctcol--data {
  min-width: 0;
}
.compare-ind-name {
  font-size: 12.5px;
  font-weight: 500;
  color: #33373d;
  line-height: 1.3;
}
.compare-cell-value {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 19px;
  font-weight: 500;
  color: #1b1e23;
  display: flex;
  align-items: baseline;
  gap: 4px;
  line-height: 1;
}
.compare-cell-unit {
  font-size: 10px;
  font-weight: 400;
  color: #9a9f97;
}
</style>
