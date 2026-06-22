<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted, nextTick } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { getCountries, getBrief, getPolycrisis, getBlindspots, getDrilldown, getClimateRisk } from '@/api/cedar'
import type { Country, BriefResponse, BriefIndicator, PolycrisisResponse, BlindspotsResponse, DrilldownResponse } from '@/types/api'
import { useEvidenceLedger } from '@/composables/useEvidenceLedger'

const { setLedger } = useEvidenceLedger()

interface HazardPoint {
  iso3: string; name: string; lat: number; lon: number; ccri: number; type: 'high' | 'medium' | 'low'
  alertlevel?: string; type_name?: string
}
const hazardPoints = ref<HazardPoint[]>([])

const TYPE_COLOR: Record<string, string> = {
  high: '#c0392b',
  medium: '#e67e22',
  low: '#2f6b4f',
}

function ccriColor(ccri: number): string {
  if (ccri >= 7) return '#c0392b'
  if (ccri >= 4) return '#e6a817'
  return '#2f6b4f'
}

// SVG inner paths (24×24 viewBox, white stroke on transparent)
const HAZARD_PATHS: Record<string, string> = {
  Earthquake:
    '<polyline points="2,12 6,6 9,16 12,4 15,14 18,8 22,12" stroke="white" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
  Flood:
    '<path d="M3 10 Q6 6 9 10 Q12 14 15 10 Q18 6 21 10" stroke="white" stroke-width="2" fill="none" stroke-linecap="round"/>' +
    '<path d="M3 16 Q6 12 9 16 Q12 20 15 16 Q18 12 21 16" stroke="white" stroke-width="2" fill="none" stroke-linecap="round"/>',
  'Tropical cyclone':
    '<path d="M12 12 m-7 0 a7 7 0 1 0 14 0" stroke="white" stroke-width="2" fill="none"/>' +
    '<path d="M12 5 Q17 7 19 12 Q17 17 12 19 Q7 17 5 12 Q7 7 12 5" stroke="white" stroke-width="1.5" fill="none"/>' +
    '<circle cx="12" cy="12" r="2" fill="white"/>',
  Drought:
    '<circle cx="12" cy="12" r="4" stroke="white" stroke-width="2" fill="none"/>' +
    '<line x1="12" y1="3" x2="12" y2="6" stroke="white" stroke-width="2" stroke-linecap="round"/>' +
    '<line x1="12" y1="18" x2="12" y2="21" stroke="white" stroke-width="2" stroke-linecap="round"/>' +
    '<line x1="3" y1="12" x2="6" y2="12" stroke="white" stroke-width="2" stroke-linecap="round"/>' +
    '<line x1="18" y1="12" x2="21" y2="12" stroke="white" stroke-width="2" stroke-linecap="round"/>' +
    '<line x1="5.6" y1="5.6" x2="7.8" y2="7.8" stroke="white" stroke-width="2" stroke-linecap="round"/>' +
    '<line x1="16.2" y1="16.2" x2="18.4" y2="18.4" stroke="white" stroke-width="2" stroke-linecap="round"/>',
  Volcano:
    '<path d="M12 3 L20 21 H4 Z" stroke="white" stroke-width="2" fill="none" stroke-linejoin="round"/>' +
    '<path d="M9 12 L12 8 L15 12" stroke="white" stroke-width="1.5" fill="none" stroke-linejoin="round"/>',
  Wildfire:
    '<path d="M12 21 C8 21 5 18 5 14 C5 10 8 8 10 6 C10 9 12 10 12 10 C12 10 14 7 13 4 C16 6 19 10 19 14 C19 18 16 21 12 21 Z" stroke="white" stroke-width="2" fill="none"/>',
}
const HAZARD_PATHS_DEFAULT =
  '<path d="M12 3 L21 20 H3 Z" stroke="white" stroke-width="2" fill="none" stroke-linejoin="round"/>' +
  '<line x1="12" y1="10" x2="12" y2="14" stroke="white" stroke-width="2" stroke-linecap="round"/>' +
  '<circle cx="12" cy="17.5" r="1" fill="white"/>'

function hazardDivIcon(typeName: string, fillColor: string, strokeColor: string): L.DivIcon {
  const paths = HAZARD_PATHS[typeName] ?? HAZARD_PATHS_DEFAULT
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">${paths}</svg>`
  return L.divIcon({
    html: `<div style="width:32px;height:32px;border-radius:50%;background:${fillColor};border:3px solid ${strokeColor};box-shadow:0 2px 6px rgba(0,0,0,0.35);display:flex;align-items:center;justify-content:center;">${svg}</div>`,
    className: '',
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    tooltipAnchor: [0, -18],
  })
}

const mapEl = ref<HTMLElement | null>(null)
let leafletMap: L.Map | null = null

function initMap() {
  if (!mapEl.value || leafletMap) return
  leafletMap = L.map(mapEl.value, {
    center: [10, 20],
    zoom: 2,
    minZoom: 1,
    maxZoom: 8,
    zoomControl: true,
    attributionControl: true,
  })

  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OSM</a> © <a href="https://carto.com/">CARTO</a>',
    subdomains: 'abcd',
    maxZoom: 19,
  }).addTo(leafletMap)

  for (const pt of hazardPoints.value) {
    const alertColor = TYPE_COLOR[pt.type]
    const strokeColor = ccriColor(pt.ccri)
    const icon = hazardDivIcon(pt.type_name ?? '', alertColor, strokeColor)
    const marker = L.marker([pt.lat, pt.lon], { icon }).addTo(leafletMap)

    const hazardLine = pt.type_name ? `${pt.type_name} · GDACS <span style="color:${alertColor}">${pt.alertlevel ?? ''}</span>` : `${pt.type} risk`
    marker.bindTooltip(
      `<div style="font-family:'IBM Plex Mono',monospace;font-size:11px;line-height:1.6;">
        <strong style="font-size:12px;color:#1b1e23;">${pt.name}</strong><br>
        CCRI <strong style="color:${strokeColor}">${pt.ccri.toFixed(1)}/10</strong> &nbsp;·&nbsp; <span style="font-size:10px;">${hazardLine}</span>
      </div>`,
      { className: 'cedar-map-tooltip', sticky: false },
    )

    marker.on('click', () => {
      const country = countries.value.find((c) => c.iso3 === pt.iso3)
      if (country) {
        selectCountry(country)
      } else {
        selectedIso.value = pt.iso3
        dropdownOpen.value = false
      }
    })
  }
}

onMounted(async () => {
  const [countriesRes, riskRes] = await Promise.allSettled([getCountries(), getClimateRisk()])
  if (countriesRes.status === 'fulfilled') {
    countries.value = countriesRes.value.countries.sort((a, b) => a.name.localeCompare(b.name))
  }
  if (riskRes.status === 'fulfilled') {
    hazardPoints.value = riskRes.value.underestimated_alerts
      .filter((a) => a.lat != null && a.lon != null)
      .map((a) => ({
        iso3: a.iso3,
        name: a.country,
        lat: a.lat!,
        lon: a.lon!,
        ccri: a.ccri,
        type: a.alertlevel === 'Red' ? 'high' : a.alertlevel === 'Orange' ? 'medium' : 'low',
        alertlevel: a.alertlevel,
        type_name: a.type_name,
      }))
  }
  await nextTick()
  initMap()
})

onUnmounted(() => {
  if (leafletMap) { leafletMap.remove(); leafletMap = null }
})

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
      setLedger(selectedIso.value, selectedCountryName.value, selectedTheme.value, brief.value.indicators, brief.value.cost)
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

function latestObs(obs: Record<string, number> | undefined): { year: string; value: number } | null {
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
    .map((i) => ({ ...i, lo: latestObs(i.obs), sp: spark(i.obs) }))
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

      <!-- Theme tabs: only when country selected -->
      <div v-if="selectedIso" class="theme-tabs">
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

      <!-- Hazard map (shown until country selected) -->
      <div v-show="!selectedIso" class="map-container">
        <div ref="mapEl" style="width:100%;height:100%;"></div>
        <!-- Legend -->
        <div class="map-legend">
          <div class="map-legend-title">Fill — GDACS Alert</div>
          <div class="map-legend-row"><span class="map-legend-dot" style="background:#2f6b4f"></span><span>Green (underestimated)</span></div>
          <div class="map-legend-row"><span class="map-legend-dot" style="background:#e67e22"></span><span>Orange (underestimated)</span></div>
          <div class="map-legend-row"><span class="map-legend-dot" style="background:#c0392b"></span><span>Red</span></div>
          <div class="map-legend-title" style="margin-top:10px;">Border — CCRI (0–10)</div>
          <div class="map-legend-row"><span class="map-legend-dot" style="background:#fff;border:3px solid #c0392b;box-sizing:border-box;"></span><span>≥ 7 Extremely High</span></div>
          <div class="map-legend-row"><span class="map-legend-dot" style="background:#fff;border:3px solid #e6a817;box-sizing:border-box;"></span><span>4–7 High</span></div>
          <div class="map-legend-row"><span class="map-legend-dot" style="background:#fff;border:3px solid #2f6b4f;box-sizing:border-box;"></span><span>&lt; 4 Medium/Low</span></div>
          <div class="map-legend-title" style="margin-top:10px;">Hazard Type</div>
          <div class="map-legend-row"><span class="map-legend-icon">〰</span><span>Earthquake</span></div>
          <div class="map-legend-row"><span class="map-legend-icon">🌊</span><span>Flood</span></div>
          <div class="map-legend-row"><span class="map-legend-icon">🌀</span><span>Cyclone</span></div>
          <div class="map-legend-row"><span class="map-legend-icon">☀</span><span>Drought</span></div>
          <div class="map-legend-row"><span class="map-legend-icon">🌋</span><span>Volcano</span></div>
          <div style="margin-top:8px;color:#9a9f97;font-size:9px;line-height:1.5;">
            GDACS alert in tooltip · Click to select
          </div>
        </div>
        <!-- Subtitle pill -->
        <div class="map-subtitle">
          Underestimated GDACS alerts (Green/Orange) in CCRI > 7 countries · {{ hazardPoints.length }} alerts live
        </div>
      </div>

      <!-- Split layout: country selected -->
      <div v-if="selectedIso" class="content-layout">

        <!-- Main col: brief + KPI cards -->
        <div class="main-col">
          <!-- Loading -->
          <div v-if="loadingBrief" class="loading-state">
            <div class="loading-dots"><span></span><span></span><span></span></div>
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
              <div v-for="ind in availableIndicators" :key="ind.code" class="kpi-card">
                <div class="kpi-name">{{ ind.name }}</div>

                <div style="display:flex;align-items:flex-end;justify-content:space-between;gap:12px;margin-top:10px;">
                  <div>
                    <div v-if="ind.lo" class="kpi-value">
                      {{ ind.lo.value.toLocaleString('en-US', { maximumFractionDigits: 1 }) }}
                      <span class="kpi-unit">{{ ind.unit }}</span>
                    </div>
                    <div v-if="ind.lo" class="kpi-year">{{ ind.lo.year }}</div>
                  </div>
                  <svg v-if="ind.sp" viewBox="0 0 100 26" style="width:100px;height:26px;display:block;flex:none;">
                    <path :d="ind.sp.area" style="fill:#eef2f5;stroke:none;" />
                    <path :d="ind.sp.line" style="fill:none;stroke:#2c4a63;stroke-width:1.4px;stroke-linejoin:round;stroke-linecap:round;" />
                    <circle :cx="ind.sp.dotX" :cy="ind.sp.dotY" r="2" style="fill:#2c4a63;" />
                  </svg>
                </div>

                <!-- Claims row -->
                <div style="margin-top:11px;padding-top:10px;border-top:1px solid #f0ece4;display:flex;align-items:center;gap:7px;flex-wrap:wrap;">
                  <span :style="tierStyle(ind.verification?.confidence_tier) + 'display:inline-block;padding:2px 6px;border-radius:2px;font-family:IBM Plex Mono,monospace;font-size:9.5px;letter-spacing:.03em;'">
                    {{ tierLabel(ind.verification?.confidence_tier) }}
                  </span>
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
                <div v-if="ind.claims && ind.claims[0]" class="kpi-claim">{{ ind.claims[0].text }}</div>

                <!-- Provenance link -->
                <div v-if="ind.provenance?.query_url" style="margin-top:8px;">
                  <a :href="ind.provenance.query_url" target="_blank" rel="noopener" class="prov-link">Source ↗</a>
                </div>
              </div>

              <!-- Unavailable -->
              <div v-for="ind in unavailableIndicators" :key="ind.code" class="kpi-card kpi-card--empty">
                <div class="kpi-name">{{ ind.name }}</div>
                <div style="margin-top:8px;font-size:11.5px;color:#a7aaa2;display:flex;align-items:center;gap:6px;">
                  <svg width="10" height="10" viewBox="0 0 10 10"><circle cx="5" cy="5" r="4" stroke="#cfccc1" stroke-width="1" fill="none"/><path d="M5 3v2.5M5 6.5v.5" stroke="#cfccc1" stroke-width="1" stroke-linecap="round"/></svg>
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
              <svg width="13" height="13" viewBox="0 0 14 14" style="flex:none;">
                <path d="M7 1l1.8 3.6L13 5.6l-3 2.9.7 4.1L7 10.5l-3.7 2.1.7-4.1L1 5.6l4.2-.6L7 1z" stroke="#2c4a63" stroke-width="1.1" fill="none" stroke-linejoin="round" />
              </svg>
              <span class="section-label">Polycrisis Risk</span>
              <span v-if="polycrisis" :style="'margin-left:4px;font-family:IBM Plex Mono,monospace;font-size:10px;color:' + BAND_COLOR[polycrisis.band]">
                {{ BAND_LABEL[polycrisis.band] }}
              </span>
              <svg class="rail-chevron" :class="{ 'rail-chevron--open': !collapsedPoly }" width="10" height="10" viewBox="0 0 10 10">
                <path d="M2 3.5l3 3 3-3" stroke="#9a9f97" stroke-width="1.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>

            <div v-show="!collapsedPoly">
              <div v-if="loadingPoly" style="height:48px;display:flex;align-items:center;justify-content:center;">
                <span style="font-family:'IBM Plex Mono',monospace;font-size:11px;color:#bfc2b9;">Loading…</span>
              </div>

              <div v-else-if="polycrisis">
                <div class="poly-band-rail" :style="'border-left-color:' + BAND_COLOR[polycrisis.band]">
                  <div class="poly-band-label" :style="'color:' + BAND_COLOR[polycrisis.band]">{{ BAND_LABEL[polycrisis.band] }}</div>
                  <div style="font-size:11.5px;color:#5a6068;margin-top:2px;">
                    {{ polycrisis.stressed }}/{{ polycrisis.scored }} domains stressed
                  </div>
                </div>
                <div class="poly-domain-list">
                  <div
                    v-for="d in polycrisis.domains.filter(x => x.available)"
                    :key="d.indicator"
                    class="rail-domain"
                  >
                    <span :style="'width:6px;height:6px;border-radius:50%;flex:none;display:inline-block;background:' + (d.stressed ? BAND_COLOR.high : '#cfe0d4')"></span>
                    <span style="flex:1;font-size:11.5px;color:#33373d;">{{ d.domain }}</span>
                    <span v-if="d.value != null" style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:#9a9f97;">
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
              <svg width="13" height="13" viewBox="0 0 14 14" style="flex:none;">
                <circle cx="7" cy="7" r="5.5" stroke="#2c4a63" stroke-width="1.1" fill="none"/>
                <path d="M7 4v3.5M7 9v.5" stroke="#2c4a63" stroke-width="1.3" stroke-linecap="round"/>
              </svg>
              <span class="section-label">Data Gaps</span>
              <span v-if="blindspots" style="margin-left:4px;font-family:'IBM Plex Mono',monospace;font-size:10px;color:#9a9f97;">
                {{ blindspots.gaps }}/{{ blindspots.total }}
              </span>
              <svg class="rail-chevron" :class="{ 'rail-chevron--open': !collapsedGaps }" width="10" height="10" viewBox="0 0 10 10">
                <path d="M2 3.5l3 3 3-3" stroke="#9a9f97" stroke-width="1.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>

            <div v-show="!collapsedGaps">
              <div v-if="loadingBlind" style="height:40px;display:flex;align-items:center;justify-content:center;">
                <span style="font-family:'IBM Plex Mono',monospace;font-size:11px;color:#bfc2b9;">Loading…</span>
              </div>

              <div v-else-if="blindspots" class="gap-list">
                <div
                  v-for="g in blindspots.indicators"
                  :key="g.indicator"
                  class="rail-gap"
                >
                  <span class="rail-gap-dot" :class="'rail-gap-dot--' + g.status"></span>
                  <span style="flex:1;font-size:11.5px;color:#33373d;line-height:1.3;">{{ g.name }}</span>
                  <span style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:#bfc2b9;flex:none;">
                    {{ g.latest ?? '—' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          <!-- Equity drilldown -->
          <div v-if="drilldown || loadingDrill" class="rail-section">
            <button class="rail-section-head" @click="collapsedDrill = !collapsedDrill">
              <svg width="13" height="13" viewBox="0 0 14 14" style="flex:none;">
                <rect x="1" y="8" width="3" height="5" rx="0.5" stroke="#2c4a63" stroke-width="1.1" fill="none"/>
                <rect x="5.5" y="5" width="3" height="8" rx="0.5" stroke="#2c4a63" stroke-width="1.1" fill="none"/>
                <rect x="10" y="2" width="3" height="11" rx="0.5" stroke="#2c4a63" stroke-width="1.1" fill="none"/>
              </svg>
              <span class="section-label">Equity Drilldown</span>
              <span v-if="drilldown" style="margin-left:4px;font-family:'IBM Plex Mono',monospace;font-size:10px;color:#9a9f97;">
                {{ drilldown.year }}
              </span>
              <svg class="rail-chevron" :class="{ 'rail-chevron--open': !collapsedDrill }" width="10" height="10" viewBox="0 0 10 10">
                <path d="M2 3.5l3 3 3-3" stroke="#9a9f97" stroke-width="1.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>

            <div v-show="!collapsedDrill">
              <div v-if="loadingDrill" style="height:48px;display:flex;align-items:center;justify-content:center;">
                <span style="font-family:'IBM Plex Mono',monospace;font-size:11px;color:#bfc2b9;">Loading…</span>
              </div>

              <div v-else-if="drilldown">
                <!-- Gap summary -->
                <div v-if="drilldown.gap_points != null" class="drill-summary">
                  <span style="font-size:11.5px;color:#5a6068;">Poorest vs richest gap</span>
                  <span style="font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:600;color:#c0392b;">
                    {{ drilldown.gap_points > 0 ? '+' : '' }}{{ drilldown.gap_points.toFixed(1) }} pp
                  </span>
                </div>

                <!-- Quintile bars -->
                <div class="drill-bars">
                  <div
                    v-for="(q, i) in drilldown.quintiles"
                    :key="q.code"
                    class="drill-bar-row"
                  >
                    <div class="drill-bar-label">Q{{ i + 1 }}</div>
                    <div class="drill-bar-track">
                      <div
                        class="drill-bar-fill"
                        :style="'width:' + (q.value != null && drilldown.quintiles[0].value != null ? Math.min(100, (q.value / Math.max(...drilldown.quintiles.map(x => x.value ?? 0))) * 100) : 0) + '%;background:' + (i === 0 ? '#c0392b' : i === 4 ? '#2f6b4f' : '#2c4a63')"
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

                <div style="font-size:10px;color:#a7aaa2;margin-top:6px;line-height:1.4;">Stunting rate (%) by wealth quintile</div>
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
  z-index: 1001;
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
.rail-gap-dot--recent  { background: #2f6b4f; }
.rail-gap-dot--stale   { background: #9a6a16; }
.rail-gap-dot--missing { background: #c0392b; }

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

/* Hazard map */
.map-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.map-legend {
  position: absolute;
  top: 14px;
  right: 14px;
  z-index: 500;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #e3e1da;
  border-radius: 4px;
  padding: 10px 13px;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.08em;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  pointer-events: none;
}
.map-legend-title {
  text-transform: uppercase;
  color: #33373d;
  font-weight: 600;
  margin-bottom: 8px;
}
.map-legend-row {
  display: flex;
  align-items: center;
  gap: 7px;
  color: #5a6068;
  margin-bottom: 5px;
}
.map-legend-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  flex: none;
}
.map-legend-icon {
  width: 16px;
  font-size: 12px;
  flex: none;
  text-align: center;
  line-height: 1;
}

.map-subtitle {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 500;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid #e3e1da;
  border-radius: 20px;
  padding: 6px 16px;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.05em;
  color: #8a8f87;
  white-space: nowrap;
  pointer-events: none;
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

</style>

<style>
.cedar-map-tooltip {
  background: #fff !important;
  border: 1px solid #e3e1da !important;
  border-radius: 4px !important;
  box-shadow: 0 2px 10px rgba(0,0,0,.1) !important;
  padding: 8px 11px !important;
}
.cedar-map-tooltip::before {
  display: none !important;
}
</style>
