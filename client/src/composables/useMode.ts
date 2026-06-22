import { reactive, ref, computed } from 'vue'
import { getMode, setMode } from '@/api/cedar'
import type { ModeResponse } from '@/types/api'

type AppMode = 'deterministic' | 'copilot'

const state = reactive({
  mode: 'deterministic' as AppMode,
  capabilities: { deterministic: true, llm_copilot: false, openai_key_in_env: false },
  apiKey: localStorage.getItem('cedar_openai_key') ?? '',
  keyModalOpen: false,
  loading: false,
  error: null as string | null,
})

async function syncMode() {
  try {
    const res: ModeResponse = await getMode()
    state.mode = res.mode
    state.capabilities = res.capabilities
    if (res.capabilities.openai_key_in_env && !state.apiKey) {
      state.apiKey = '__env__'
    }
  } catch {
    // backend offline — stay deterministic
  }
}

async function switchMode(target: AppMode) {
  if (target === 'copilot' && !state.apiKey) {
    state.keyModalOpen = true
    return
  }
  state.loading = true
  state.error = null
  try {
    const res = await setMode(target)
    state.mode = res.mode
    state.capabilities = res.capabilities
  } catch (e) {
    state.error = e instanceof Error ? e.message : 'Failed to switch mode'
  } finally {
    state.loading = false
  }
}

function saveApiKey(key: string) {
  state.apiKey = key.trim()
  localStorage.setItem('cedar_openai_key', state.apiKey)
  state.keyModalOpen = false
  if (state.mode !== 'copilot') switchMode('copilot')
}

function clearApiKey() {
  state.apiKey = ''
  localStorage.removeItem('cedar_openai_key')
  switchMode('deterministic')
}

function openKeyModal() {
  state.keyModalOpen = true
}
function closeKeyModal() {
  state.keyModalOpen = false
}

const isCopilot = computed(() => state.mode === 'copilot')
const isEvidence = computed(() => state.mode === 'deterministic')
const hasKey = computed(() => !!state.apiKey)

export function useMode() {
  return {
    state,
    isCopilot,
    isEvidence,
    hasKey,
    syncMode,
    switchMode,
    saveApiKey,
    clearApiKey,
    openKeyModal,
    closeKeyModal,
  }
}
