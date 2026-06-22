import { reactive, computed, nextTick, ref } from 'vue'
import type {
  KPI,
  Citation,
  SDG,
  ActionItem,
  Paragraph,
  Step,
  Source,
  Scenario,
  Message,
  PanelData,
  TokenInfo,
  HistoryGroup,
  EnrichedAction,
} from '@/types'

const SCENARIOS: Record<string, Scenario> = {
  kenya: {
    key: 'kenya',
    title: 'Maternal health — Kenya',
    contextLabel: 'Kenya · Maternal & reproductive health',
    query: 'What is the maternal mortality ratio in Kenya, and how has it changed since 2000?',
    domain: 'maternal & reproductive health',
    tokens: { in: 1240, out: 690 },
    sdgs: [
      { n: 3, label: 'Good Health & Well-being', color: '#4C9F38', weight: 65 },
      { n: 5, label: 'Gender Equality', color: '#FF3A21', weight: 35 },
    ],
    actions: [
      {
        text: 'Prioritise the 8 counties above 600 / 100k for emergency obstetric investment',
        cites: [1],
      },
      {
        text: 'Sustain skilled-attendance funding to hold the 70% trajectory toward 2030',
        cites: [2],
      },
      { text: 'Close civil-registration gaps to raise future estimate confidence', cites: [1, 3] },
    ],
    paragraphs: [
      {
        text: "Kenya's maternal mortality ratio stood at 530 deaths per 100,000 live births in 2020, down from roughly 708 in 2000 — a decline of about 25% over two decades.",
        cite: 1,
      },
      {
        text: 'Progress has been driven largely by gains in skilled birth attendance, now reaching 70% of deliveries, though the ratio remains well above the SDG target of 70 per 100,000 by 2030.',
        cite: 2,
      },
      {
        text: 'Confidence in the headline figure is high: it is drawn from the WHO/UN MMEIG joint estimates, which reconcile civil registration, survey and census data.',
        cite: 1,
      },
    ],
    kpis: [
      {
        indicator: 'Maternal mortality ratio',
        value: '530',
        unit: 'per 100k',
        year: '2020',
        confidence: 'High',
        source: 'WHO/UN MMEIG',
        values: [708, 617, 560, 542, 530],
      },
      {
        indicator: 'Skilled birth attendance',
        value: '70',
        unit: '% births',
        year: '2022',
        confidence: 'High',
        source: 'DHS / World Bank',
        values: [42, 44, 52, 62, 70],
      },
      {
        indicator: 'Under-5 mortality',
        value: '37',
        unit: 'per 1k',
        year: '2022',
        confidence: 'Med',
        source: 'UN IGME',
        values: [99, 73, 52, 43, 37],
      },
    ],
    citations: [
      {
        n: 1,
        text: 'World Health Organization — Trends in Maternal Mortality 2000–2020 (MMEIG), 2023.',
        host: 'who.int',
      },
      {
        n: 2,
        text: 'Kenya Demographic and Health Survey (KDHS) 2022, via World Bank Health indicators.',
        host: 'data.worldbank.org',
      },
      {
        n: 3,
        text: 'UN Inter-agency Group for Child Mortality Estimation, 2023.',
        host: 'childmortality.org',
      },
    ],
  },
  bangladesh: {
    key: 'bangladesh',
    title: 'Energy access — Bangladesh',
    contextLabel: 'Bangladesh · Energy access',
    query:
      "How much of Bangladesh's population has access to electricity, and how clean is its power supply?",
    domain: 'energy access & power mix',
    tokens: { in: 1110, out: 640 },
    sdgs: [
      { n: 7, label: 'Affordable & Clean Energy', color: '#FDB713', weight: 70 },
      { n: 13, label: 'Climate Action', color: '#3F7E44', weight: 30 },
    ],
    actions: [
      { text: 'Tie new generation capacity to a binding renewable-share floor', cites: [2] },
      {
        text: 'Commission a 2023 generation audit to lift the renewables estimate to High',
        cites: [2],
      },
      { text: 'Pair near-universal access with demand-side efficiency programs', cites: [1] },
    ],
    paragraphs: [
      {
        text: "As of 2021, 99% of Bangladesh's population had access to electricity — up from just 32% in 2000, one of the fastest electrification gains recorded in South Asia.",
        cite: 1,
      },
      {
        text: 'That access remains carbon-intensive: renewable sources account for only about 1.1% of electricity output, with the grid still dominated by natural gas.',
        cite: 2,
      },
      {
        text: 'Access figures carry high confidence, but the renewable-share estimate is rated medium pending 2023 generation data.',
        cite: 2,
      },
    ],
    kpis: [
      {
        indicator: 'Access to electricity',
        value: '99',
        unit: '% pop.',
        year: '2021',
        confidence: 'High',
        source: 'World Bank / IEA',
        values: [32, 55, 76, 92, 99],
      },
      {
        indicator: 'Renewable electricity output',
        value: '1.1',
        unit: '% total',
        year: '2021',
        confidence: 'Med',
        source: 'IEA / Ember',
        values: [1.6, 1.4, 1.3, 1.2, 1.1],
      },
      {
        indicator: 'CO₂ from power',
        value: '0.62',
        unit: 't / cap',
        year: '2021',
        confidence: 'Low',
        source: 'Global Carbon Project',
        values: [0.2, 0.32, 0.45, 0.55, 0.62],
      },
    ],
    citations: [
      {
        n: 1,
        text: 'World Bank — Access to electricity (% of population), 2023 update.',
        host: 'data.worldbank.org',
      },
      {
        n: 2,
        text: 'International Energy Agency, World Energy Balances 2023; Ember Global Electricity Review.',
        host: 'iea.org',
      },
      {
        n: 3,
        text: 'Global Carbon Project, 2023 (modelled estimate).',
        host: 'globalcarbonproject.org',
      },
    ],
  },
  rwanda: {
    key: 'rwanda',
    title: 'Growth & poverty — Rwanda',
    contextLabel: 'Rwanda · Growth & poverty',
    query: "What's the trend in Rwanda's GDP per capita and poverty rate?",
    domain: 'growth & poverty',
    tokens: { in: 1185, out: 705 },
    sdgs: [
      { n: 1, label: 'No Poverty', color: '#E5243B', weight: 55 },
      { n: 8, label: 'Decent Work & Growth', color: '#A21942', weight: 45 },
    ],
    actions: [
      {
        text: 'Schedule the next EICV household survey to refresh the 2017 poverty figure',
        cites: [2],
      },
      { text: 'Protect post-pandemic growth gains with targeted rural transfers', cites: [1] },
      { text: 'Benchmark GDP per capita against the 2035 middle-income threshold', cites: [1] },
    ],
    paragraphs: [
      {
        text: "Rwanda's GDP per capita reached US$966 in 2022, more than doubling from US$430 in 2010 in current dollars, sustained by annual growth averaging above 7% before the pandemic.",
        cite: 1,
      },
      {
        text: 'Poverty has fallen in parallel: the share of people below the national poverty line dropped to roughly 38% in 2017, the most recent official survey year.',
        cite: 2,
      },
      {
        text: 'The poverty figure is rated medium confidence — it predates the pandemic and awaits the next household survey.',
        cite: 2,
      },
    ],
    kpis: [
      {
        indicator: 'GDP per capita',
        value: '966',
        unit: 'US$',
        year: '2022',
        confidence: 'High',
        source: 'World Bank WDI',
        values: [430, 560, 710, 820, 966],
      },
      {
        indicator: 'Poverty headcount',
        value: '38',
        unit: '% nat. line',
        year: '2017',
        confidence: 'Med',
        source: 'NISR / World Bank',
        values: [57, 49, 45, 40, 38],
      },
      {
        indicator: 'GDP growth',
        value: '8.2',
        unit: '% annual',
        year: '2022',
        confidence: 'High',
        source: 'IMF WEO',
        values: [7.3, 6.9, 8.6, -3.4, 8.2],
      },
    ],
    citations: [
      { n: 1, text: 'World Bank World Development Indicators, 2023.', host: 'data.worldbank.org' },
      {
        n: 2,
        text: 'National Institute of Statistics of Rwanda (NISR), EICV survey; World Bank.',
        host: 'statistics.gov.rw',
      },
      { n: 3, text: 'IMF World Economic Outlook, Oct 2023.', host: 'imf.org' },
    ],
  },
  nigeria: {
    key: 'nigeria',
    title: 'Education spending — Nigeria',
    contextLabel: '',
    query: 'Summarise the main challenges in measuring education spending in Nigeria.',
    paragraphs: [
      {
        text: "Comparable education-spending data for Nigeria is sparse: the most recent harmonised figure in the World Bank's EdStats predates 2018, and sub-national budgets are not consistently reported.",
        cite: 0,
      },
      {
        text: "Because no single indicator currently meets CEDAR's confidence threshold here, no data panel is shown. I can instead point you to the underlying budget documents, or estimate from the latest available year with the caveat clearly flagged.",
        cite: 0,
      },
    ],
    kpis: [],
    citations: [],
  },
}

function spark(values: number[]) {
  const w = 124,
    h = 30,
    p = 3
  const vals = values && values.length ? values : [0, 0]
  const n = vals.length
  let mn = Math.min(...vals),
    mx = Math.max(...vals)
  if (mx === mn) {
    mx = mn + 1
    mn = mn - 1
  }
  const X = (i: number) => p + (i * (w - 2 * p)) / (n - 1)
  const Y = (v: number) => h - p - ((v - mn) / (mx - mn)) * (h - 2 * p)
  let line = ''
  vals.forEach((v, i) => {
    line += (i ? 'L' : 'M') + X(i).toFixed(1) + ' ' + Y(v).toFixed(1) + ' '
  })
  const area =
    line + 'L' + X(n - 1).toFixed(1) + ' ' + (h - p) + ' L' + X(0).toFixed(1) + ' ' + (h - p) + ' Z'
  return { line: line.trim(), area, dotX: X(n - 1).toFixed(1), dotY: Y(vals[n - 1] ?? 0).toFixed(1) }
}

function tierStyle(t: string) {
  if (t === 'High') return 'color:#2f6b4f;background:#e7efe9;border:1px solid #cfe0d4;'
  if (t === 'Med') return 'color:#8a6516;background:#f4ecd8;border:1px solid #e7d9b6;'
  return 'color:#6d7178;background:#ecebe4;border:1px solid #ddd9cf;'
}

function enrichKpis(kpis: KPI[]): KPI[] {
  return (kpis || []).map((k) => {
    const sp = spark(k.values)
    return {
      ...k,
      line: sp.line,
      area: sp.area,
      dotX: sp.dotX,
      dotY: sp.dotY,
      pillStyle: tierStyle(k.confidence),
    }
  })
}

const COUNTRY_CODES: Record<string, string> = {
  kenya: 'KEN', bangladesh: 'BGD', rwanda: 'RWA', nigeria: 'NGA',
  ghana: 'GHA', ethiopia: 'ETH', uganda: 'UGA', tanzania: 'TZA',
  india: 'IND', pakistan: 'PAK', cambodia: 'KHM', mali: 'MLI',
  senegal: 'SEN', mozambique: 'MOZ', zambia: 'ZMB', malawi: 'MWI',
  cameroon: 'CMR', burkina: 'BFA', niger: 'NER', chad: 'TCD',
}

const THEME_KEYWORDS: Array<[RegExp, string]> = [
  [/maternal|obstetric|mmeig/, 'health-system'],
  [/child|under.?5|infant|stunting|immuniz|dpt|imrt/, 'child-survival'],
  [/poverty|gdp|economic|income|unemploy|wages|ppp/, 'economy-poverty'],
  [/education|school|literacy|completion|enrolment/, 'education'],
  [/water|sanitation|wash|drinking|latrine/, 'wash'],
  [/energy|electric|renewable|climate|co2|carbon|emission/, 'energy-climate'],
  [/health|life expectancy|hospital|mortality/, 'health-system'],
]

function detectApiParams(text: string): { country: string; theme: string } | null {
  const t = text.toLowerCase()
  let country: string | undefined
  for (const [name, code] of Object.entries(COUNTRY_CODES)) {
    if (t.includes(name)) { country = code; break }
  }
  let theme: string | undefined
  for (const [pattern, th] of THEME_KEYWORDS) {
    if (pattern.test(t)) { theme = th; break }
  }
  return country && theme ? { country, theme } : null
}

function matchScenario(text: string): Scenario | null {
  const t = (text || '').toLowerCase()
  if (/kenya|maternal|mortality/.test(t)) return SCENARIOS.kenya ?? null
  if (/bangladesh|electric|energy|power|renewable/.test(t)) return SCENARIOS.bangladesh ?? null
  if (/rwanda|gdp|poverty|growth/.test(t)) return SCENARIOS.rwanda ?? null
  if (/nigeria|education|spend|school/.test(t)) return SCENARIOS.nigeria ?? null
  return null
}

function buildUserMessage(text: string): Message {
  return { role: 'user', isUser: true, isAssistant: false, text }
}

function buildAssistantMessage(sc: Scenario | null): Message {
  if (!sc) {
    return {
      role: 'assistant',
      isAssistant: true,
      isUser: false,
      hasData: false,
      contextLabel: '',
      kpiCount: 0,
      kpis: [],
      citations: [],
      sdgs: [],
      actions: [],
      tokens: { in: 420, out: 180 },
      sources: [],
      steps: [],
      paragraphs: [
        {
          text: 'I can return verified indicators once you name a country and a development measure — for example "maternal mortality in Kenya" or "electricity access in Bangladesh." Each figure I return is traced to its source API.',
          cite: 0,
        },
      ],
    }
  }
  const country = (sc.contextLabel || '').split(' ·')[0] || sc.title
  const apiList = [...new Set((sc.kpis || []).map((k) => k.source))]
  const sdgNums = (sc.sdgs || []).map((s) => 'SDG ' + s.n).join(', ')
  const sources: Source[] = (sc.citations || []).map((c) => ({ n: c.n, host: c.host }))
  const steps: Step[] =
    sc.kpis && sc.kpis.length
      ? [
          { label: 'Parse query', detail: country + ' · ' + (sc.domain || '') },
          { label: 'Select indicators', detail: sc.kpis.length + ' matched from catalogue' },
          { label: 'Query source APIs', detail: apiList.join('  ·  ') },
          { label: 'Reconcile & score', detail: 'Cross-checked series, confidence tiers assigned' },
          { label: 'Map to SDGs', detail: sdgNums },
          {
            label: 'Compose answer',
            detail:
              sc.paragraphs.length +
              ' traceable claims · ' +
              (sc.citations || []).length +
              ' citations',
          },
        ]
      : []
  return {
    role: 'assistant',
    isAssistant: true,
    isUser: false,
    hasData: !!(sc.kpis && sc.kpis.length),
    contextLabel: sc.contextLabel || '',
    paragraphs: sc.paragraphs,
    citations: sc.citations || [],
    kpis: sc.kpis || [],
    kpiCount: (sc.kpis || []).length,
    sdgs: sc.sdgs || [],
    actions: sc.actions || [],
    tokens: sc.tokens || { in: 0, out: 0 },
    sources,
    steps,
  }
}

// Module-level singleton state
const state = reactive({
  sidebarOpen: true,
  panelOpen: false,
  citesOpen: true,
  view: 'chat' as 'chat' | 'brief',
  input: '',
  thinking: false,
  messages: [] as Message[],
  activeKey: null as string | null,
  convTitle: 'New query',
  highlightCite: null as number | null,
})

const scrollRef = ref<HTMLElement | null>(null)
const panelScrollRef = ref<HTMLElement | null>(null)
const citesRef = ref<HTMLElement | null>(null)

let thinkingTimer: ReturnType<typeof setTimeout> | null = null

async function ask(text: string) {
  const v = (text || '').trim()
  if (!v) return

  state.messages = [...state.messages, buildUserMessage(v)]
  state.input = ''
  state.thinking = true
  state.view = 'chat'
  state.panelOpen = false
  if (thinkingTimer) clearTimeout(thinkingTimer)

  let sc: Scenario | null = null
  const params = detectApiParams(v)

  if (params) {
    try {
      const res = await fetch(`/api/brief?country=${params.country}&theme=${params.theme}`)
      if (res.ok) sc = (await res.json()) as Scenario
    } catch {
      /* API not running — fall through to mock */
    }
  }

  if (!sc) sc = matchScenario(v)

  thinkingTimer = setTimeout(() => {
    const a = buildAssistantMessage(sc)
    state.messages = [...state.messages, a]
    state.thinking = false
    state.panelOpen = a.hasData ?? false
    state.activeKey = sc ? sc.key : state.activeKey
    state.convTitle = sc ? sc.title : 'New query'
    nextTick(() => {
      if (scrollRef.value) scrollRef.value.scrollTop = scrollRef.value.scrollHeight
    })
  }, 350)
}

function loadConv(key: string) {
  const sc = SCENARIOS[key] ?? null
  if (!sc) return
  const a = buildAssistantMessage(sc)
  state.messages = [buildUserMessage(sc.query), a]
  state.thinking = false
  state.panelOpen = a.hasData ?? false
  state.view = 'chat'
  state.activeKey = key
  state.convTitle = sc.title
  state.input = ''
  state.highlightCite = null
}

function newQuery() {
  state.messages = []
  state.panelOpen = false
  state.view = 'chat'
  state.activeKey = null
  state.convTitle = 'New query'
  state.input = ''
  state.highlightCite = null
}

function clickCite(n: number) {
  state.citesOpen = true
  state.highlightCite = n
  setTimeout(() => {
    const sc = panelScrollRef.value
    const t = citesRef.value
    if (sc && t) sc.scrollTop = (t as HTMLElement).offsetTop - 10
  }, 70)
}

function togglePanel() {
  state.panelOpen = !state.panelOpen
}
function toggleSidebar() {
  state.sidebarOpen = !state.sidebarOpen
}
function toggleCites() {
  state.citesOpen = !state.citesOpen
}
function openBrief() {
  state.view = 'brief'
}
function closeBrief() {
  state.view = 'chat'
}
function onInput(e: Event) {
  state.input = (e.target as HTMLInputElement).value
}
function onKey(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    ask(state.input)
  }
}

// Computed values
const enrichedMessages = computed(() =>
  state.messages.map((m) => {
    if (!m.isAssistant) return m
    const steps = (m.steps || []).map((s, i, arr) => ({
      ...s,
      idx: String(i + 1),
      notLast: i < arr.length - 1,
    }))
    return { ...m, kpis: enrichKpis(m.kpis || []), steps, stepCount: steps.length }
  }),
)

const lastDataMessage = computed(
  () => [...enrichedMessages.value].reverse().find((m) => m.isAssistant && m.hasData) ?? null,
)

const isChat = computed(() => state.view === 'chat')
const hasData = computed(() => !!lastDataMessage.value)

const panelShown = computed(() => state.panelOpen && isChat.value && hasData.value)
const showBriefBtn = computed(() => isChat.value && hasData.value)
const showPanelBtn = computed(() => isChat.value && hasData.value)

const panelBtnStyle = computed(
  () =>
    'display:flex;align-items:center;gap:7px;padding:7px 12px;background:' +
    (state.panelOpen ? '#eef2f5' : 'transparent') +
    ';border:1px solid ' +
    (state.panelOpen ? '#dce6ee' : '#ddd9cf') +
    ';border-radius:3px;cursor:pointer;font-family:inherit;font-size:12.5px;font-weight:500;color:#2c4a63;',
)

const panelBtnLabel = computed(() => (state.panelOpen ? 'Hide data' : 'Show data'))

const hlBase =
  'display:flex;gap:10px;padding:9px;margin:0 -9px;border-top:1px solid #efece4;border-radius:3px;transition:background .2s;'

const panelData = computed<PanelData>(() => {
  const ld = lastDataMessage.value
  if (!ld) return { contextLabel: '', kpis: [], citations: [], sdgs: [], actions: [] }
  const citations: Citation[] = (ld.citations || []).map((c) => ({
    ...c,
    rowStyle:
      hlBase +
      (c.n === state.highlightCite ? 'background:#e8eef3;box-shadow:inset 2px 0 0 #2c4a63;' : ''),
  }))
  const actions: EnrichedAction[] = (ld.actions || []).map((a, i) => ({
    idx: String(i + 1),
    text: (a as ActionItem).text,
    hasChips: ((a as ActionItem).cites || []).length > 0,
    chips: ((a as ActionItem).cites || []).map((n) => ({ n, run: () => clickCite(n) })),
  }))
  const sdgs: SDG[] = (ld.sdgs || []).map((s) => ({ ...s, weight: s.weight || 0 }))
  return { contextLabel: ld.contextLabel || '', kpis: ld.kpis || [], citations, sdgs, actions }
})

const fmt = (n: number) => (n || 0).toLocaleString('en-US')

const tokenInfo = computed<TokenInfo>(() => {
  const ld = lastDataMessage.value
  const tk = ld ? ld.tokens || { in: 0, out: 0 } : { in: 0, out: 0 }
  const total = (tk.in || 0) + (tk.out || 0)
  return {
    inStr: fmt(tk.in || 0),
    outStr: fmt(tk.out || 0),
    totalStr: fmt(total),
    inPct: total ? Math.round(((tk.in || 0) / total) * 100) : 0,
  }
})

const sources = computed<Source[]>(() =>
  lastDataMessage.value ? lastDataMessage.value.sources || [] : [],
)

const brief = computed(() => {
  const ld = lastDataMessage.value
  if (!ld)
    return {
      contextLabel: '',
      paragraphs: [],
      kpis: [] as KPI[],
      citations: [] as Citation[],
      kpiCount: 0,
    }
  return {
    contextLabel: ld.contextLabel || '',
    paragraphs: ld.paragraphs || [],
    kpis: ld.kpis || [],
    citations: ld.citations || [],
    kpiCount: (ld.kpis || []).length,
  }
})

const HIST_DEF = [
  { label: 'Today', keys: ['kenya'] },
  { label: 'Earlier this week', keys: ['bangladesh', 'rwanda'] },
  { label: 'Older', keys: ['nigeria'] },
]

const historyGroups = computed<HistoryGroup[]>(() =>
  HIST_DEF.map((g) => ({
    label: g.label,
    items: g.keys.map((k) => {
      const active = state.activeKey === k
      return {
        key: k,
        title: SCENARIOS[k]?.title ?? '',
        run: () => loadConv(k),
        dot: active ? '#2c4a63' : '#cfccc1',
        style:
          'width:100%;display:flex;align-items:center;gap:9px;padding:8px 10px;margin-bottom:1px;background:' +
          (active ? '#edf0f3' : 'transparent') +
          ';border:none;border-radius:3px;cursor:pointer;font-family:inherit;font-size:13px;font-weight:' +
          (active ? '500' : '400') +
          ';color:' +
          (active ? '#23496a' : '#4a4f57') +
          ';text-align:left;',
      }
    }),
  })),
)

const EXAMPLES = [
  { label: 'Maternal mortality in Kenya since 2000', q: SCENARIOS.kenya?.query ?? '' },
  { label: 'Electricity access in Bangladesh', q: SCENARIOS.bangladesh?.query ?? '' },
  { label: 'GDP per capita and poverty in Rwanda', q: SCENARIOS.rwanda?.query ?? '' },
]

const examples = computed(() => EXAMPLES.map((e) => ({ ...e, run: () => ask(e.q) })))

export function useCedar() {
  return {
    state,
    scrollRef,
    panelScrollRef,
    citesRef,
    enrichedMessages,
    lastDataMessage,
    isChat,
    hasData,
    panelShown,
    showBriefBtn,
    showPanelBtn,
    panelBtnStyle,
    panelBtnLabel,
    panelData,
    tokenInfo,
    sources,
    brief,
    historyGroups,
    examples,
    ask,
    loadConv,
    newQuery,
    clickCite,
    togglePanel,
    toggleSidebar,
    toggleCites,
    openBrief,
    closeBrief,
    onInput,
    onKey,
    enrichKpis,
    tierStyle,
  }
}
