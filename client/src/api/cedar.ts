import type {
  ModeResponse,
  CountriesResponse,
  BriefResponse,
  PolycrisisResponse,
  BlindspotsResponse,
  ChatRequest,
  ChatResponse,
  ProjectResponse,
} from '@/types/api'

const BASE = '/api'

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, init)
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(body.detail ?? `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

export function getMode(): Promise<ModeResponse> {
  return req('/mode')
}

export function setMode(mode: 'deterministic' | 'copilot'): Promise<ModeResponse> {
  return req('/mode', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode }),
  })
}

export function getCountries(): Promise<CountriesResponse> {
  return req('/countries')
}

export function getBrief(country: string, theme = 'child-survival'): Promise<BriefResponse> {
  return req(`/brief/${country}?theme=${theme}`)
}

export function getPolycrisis(country: string): Promise<PolycrisisResponse> {
  return req(`/polycrisis/${country}`)
}

export function getBlindspots(country: string, cutoff = 2022): Promise<BlindspotsResponse> {
  return req(`/blindspots/${country}?cutoff=${cutoff}`)
}

export function getProject(country: string, code: string): Promise<ProjectResponse> {
  return req(`/project/${country}/${code}`)
}

export function postCopilotChat(payload: ChatRequest, apiKey: string): Promise<ChatResponse> {
  return req('/copilot/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-OpenAI-Key': apiKey,
    },
    body: JSON.stringify(payload),
  })
}
