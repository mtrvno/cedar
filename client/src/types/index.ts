export interface KPI {
  indicator: string
  value: string
  unit: string
  year: string
  confidence: 'High' | 'Med' | 'Low'
  source: string
  values: number[]
  line?: string
  area?: string
  dotX?: string
  dotY?: string
  pillStyle?: string
}

export interface Citation {
  n: number
  text: string
  host: string
  rowStyle?: string
}

export interface SDG {
  n: number
  label: string
  color: string
  weight: number
}

export interface ActionItem {
  text: string
  cites: number[]
}

export interface Paragraph {
  text: string
  cite?: number
}

export interface Step {
  label: string
  detail: string
  idx?: string
  notLast?: boolean
}

export interface Source {
  n: number
  host: string
}

export interface Scenario {
  key: string
  title: string
  contextLabel: string
  query: string
  domain?: string
  tokens?: { in: number; out: number }
  sdgs?: SDG[]
  actions?: ActionItem[]
  paragraphs: Paragraph[]
  kpis?: KPI[]
  citations?: Citation[]
}

export interface Message {
  role: 'user' | 'assistant'
  isUser: boolean
  isAssistant: boolean
  text?: string
  hasData?: boolean
  contextLabel?: string
  paragraphs?: Paragraph[]
  citations?: Citation[]
  kpis?: KPI[]
  kpiCount?: number
  sdgs?: SDG[]
  actions?: ActionItem[]
  tokens?: { in: number; out: number }
  sources?: Source[]
  steps?: Step[]
  stepCount?: number
}

export interface HistoryItem {
  key: string
  title: string
  run: () => void
  dot: string
  style: string
}

export interface HistoryGroup {
  label: string
  items: HistoryItem[]
}

export interface EnrichedAction {
  idx: string
  text: string
  hasChips: boolean
  chips: { n: number; run: () => void }[]
}

export interface PanelData {
  contextLabel: string
  kpis: KPI[]
  citations: Citation[]
  sdgs: SDG[]
  actions: EnrichedAction[]
}

export interface TokenInfo {
  inStr: string
  outStr: string
  totalStr: string
  inPct: number
}
