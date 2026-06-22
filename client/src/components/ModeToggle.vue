<script setup lang="ts">
import { useMode } from '@/composables/useMode'

const { state, switchMode } = useMode()
</script>

<template>
  <div class="mode-toggle" role="group" aria-label="Analysis mode">
    <button
      class="mode-btn"
      :class="{ 'mode-btn--active': state.mode === 'deterministic' }"
      @click="switchMode('deterministic')"
    >
      <svg width="11" height="11" viewBox="0 0 12 12" style="flex:none;">
        <circle cx="6" cy="6" r="4.5" stroke="currentColor" stroke-width="1.2" fill="none" />
        <path d="M3.5 6h5M6 3.5v5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" />
      </svg>
      Evidence
    </button>
    <button
      class="mode-btn"
      :class="{ 'mode-btn--active': state.mode === 'copilot' }"
      @click="switchMode('copilot')"
    >
      <svg width="11" height="11" viewBox="0 0 12 12" style="flex:none;">
        <path
          d="M2 9.5L3.5 6 6 2.5 8.5 6 10 9.5H2z"
          stroke="currentColor"
          stroke-width="1.1"
          fill="none"
          stroke-linejoin="round"
        />
      </svg>
      Copilot
    </button>
  </div>
</template>

<style scoped>
.mode-toggle {
  display: flex;
  align-items: center;
  gap: 2px;
  background: #eae8e1;
  border-radius: 4px;
  padding: 3px;
}

.mode-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 11px;
  border: none;
  border-radius: 3px;
  cursor: pointer;
  font-family: 'IBM Plex Sans', system-ui, sans-serif;
  font-size: 12px;
  font-weight: 500;
  color: #6a6f68;
  background: transparent;
  transition: background 0.12s, color 0.12s;
  white-space: nowrap;
}

.mode-btn:hover:not(.mode-btn--active) {
  background: #d8d5cd;
  color: #33373d;
}

.mode-btn--active {
  background: #fff;
  color: #2c4a63;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
}
</style>
