import { ref } from 'vue'
import type { BriefIndicator } from '@/types/api'

// Module-level = singleton shared between OverviewView and AppSidebar
const country = ref('')
const countryName = ref('')
const theme = ref('')
const indicators = ref<BriefIndicator[]>([])
const cost = ref<Record<string, unknown> | null>(null)
const retrievedAt = ref<string | null>(null)

export function useEvidenceLedger() {
  function setLedger(
    iso: string,
    name: string,
    thm: string,
    inds: BriefIndicator[],
    c: Record<string, unknown>,
  ) {
    country.value = iso
    countryName.value = name
    theme.value = thm
    indicators.value = inds
    cost.value = c
    retrievedAt.value = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
  }

  return { country, countryName, theme, indicators, cost, retrievedAt, setLedger }
}
