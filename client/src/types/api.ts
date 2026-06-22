export interface ModeCapabilities {
  deterministic: boolean
  llm_copilot: boolean
  openai_key_in_env: boolean
}

export interface ModeResponse {
  mode: 'deterministic' | 'copilot'
  modes: string[]
  capabilities: ModeCapabilities
  note: string
}

export interface Country {
  iso3: string
  name: string
}

export interface CountriesResponse {
  countries: Country[]
}

export interface BriefClaim {
  id: string
  text: string
  verdict: string
  datapoints: string[]
  benchmark?: number
}

export interface BriefVerification {
  n_values: number
  span_years: number
  coverage: number
  latest_year: number
  confidence_tier: 'High' | 'Medium' | 'Low'
  caveats: string[]
  value_hash: string
}

export interface BriefIndicator {
  code: string
  name: string
  unit?: string
  available: boolean
  obs?: Record<string, number>
  verification?: BriefVerification
  claims?: BriefClaim[]
  provenance?: Record<string, unknown>
}

export interface BriefResponse {
  country: string
  theme: string
  label: string
  generated_at: string
  indicators: BriefIndicator[]
  cost: Record<string, unknown>
}

export interface PolycrisisDomain {
  domain: string
  indicator: string
  name?: string
  unit?: string
  available: boolean
  value?: number
  year?: number
  benchmark?: number | null
  status?: string
  stressed?: boolean
  confidence?: string
  query_url?: string
}

export interface PolycrisisResponse {
  country: string
  stressed: number
  scored: number
  band: 'high' | 'elevated' | 'lower'
  domains: PolycrisisDomain[]
  cost: Record<string, unknown>
}

export interface BlindspotIndicator {
  indicator: string
  name: string
  status: 'recent' | 'stale' | 'missing'
  latest: number | null
}

export interface BlindspotsResponse {
  country: string
  cutoff: number
  total: number
  missing: number
  stale: number
  recent: number
  gaps: number
  indicators: BlindspotIndicator[]
  cost: Record<string, unknown>
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatSource {
  country: string
  iso: string
  code: string
  name: string
  latest: { year: number; value: number }
  query_url: string
}

export interface ChatRequest {
  country: string
  messages: ChatMessage[]
  model?: string
}

export interface ChatResponse {
  answer: string
  grounded: boolean
  unverified_numbers: string[]
  sources: ChatSource[]
  tokens: { in: number; out: number }
  model: string
}

export interface DrilldownQuintile {
  code: string
  quintile: string
  value: number | null
  query_url: string | null
}

export interface DrilldownResponse {
  country: string
  dimension: string
  indicator: string
  year: number
  national: number | null
  quintiles: DrilldownQuintile[]
  ratio_poorest_to_richest: number | null
  gap_points: number | null
  cost: Record<string, unknown>
}

export interface ProjectResponse {
  country: string
  indicator: string
  latest?: number
  latest_year?: number
  target?: number
  direction?: string
  met?: boolean
  projectable: boolean
  reach_year?: number | null
  years_late?: number | null
  diverging?: boolean
  on_time?: boolean
  note?: string
  reason?: string
}
