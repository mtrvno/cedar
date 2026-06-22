<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const stages = [
  { n: '01', label: 'Discover', detail: 'resolving indicator & country codes' },
  { n: '02', label: 'Retrieve', detail: 'calling authoritative APIs' },
  { n: '03', label: 'Verify', detail: 'coverage, recency, confidence tier' },
  { n: '04', label: 'Analyse', detail: 'trend, gap-to-SDG-target — no LLM' },
  { n: '05', label: 'Narrate', detail: 'verified claims → cited prose' },
  { n: '06', label: 'Review', detail: 'veto any number without a datapoint' },
  { n: '07', label: 'Output', detail: 'brief + ledger + provenance + cost' },
]

const active = ref(0)
const pct = ref(0)
let raf = 0
let start = 0
const DURATION = 4600

const tick = (now: number) => {
  if (!start) start = now
  const t = Math.min(1, (now - start) / DURATION)
  const eased = 1 - Math.pow(1 - t, 3)
  pct.value = Math.round(eased * 100)
  active.value = Math.min(stages.length - 1, Math.floor(eased * stages.length))
  if (t < 1) {
    raf = requestAnimationFrame(tick)
  } else {
    setTimeout(() => router.push('/app'), 580)
  }
}

onMounted(() => {
  raf = requestAnimationFrame(tick)
})
onUnmounted(() => cancelAnimationFrame(raf))

const goApp = () => router.push('/app')
</script>

<template>
  <div class="loading">
    <div class="loading__bg" aria-hidden="true"></div>

    <main class="loading__main">
      <!-- breathing mark -->
      <div class="loading__mark" aria-hidden="true">
        <div class="loading__ring"></div>
        <div class="loading__dot"></div>
      </div>

      <div class="overline">CEDAR · preparing the copilot</div>
      <h1 class="loading__title">
        Consulting verified sources<span class="loading__period">…</span>
      </h1>
      <p class="loading__sub">
        Every figure traces back to its source. Setting up the evidence chain.
      </p>

      <!-- progress -->
      <div class="progress">
        <div class="progress__track">
          <div class="progress__fill" :style="{ width: pct + '%' }"></div>
        </div>
        <div class="progress__meta">
          <span class="progress__stage">{{ stages[active].n }} · {{ stages[active].label }}</span>
          <span class="progress__pct">{{ pct }}%</span>
        </div>
        <div class="progress__detail">{{ stages[active].detail }}</div>
      </div>

      <!-- stage list -->
      <ol class="stages">
        <li
          v-for="(s, i) in stages"
          :key="s.n"
          class="stage"
          :class="{ 'stage--done': i < active, 'stage--active': i === active }"
        >
          <span class="stage__dot" aria-hidden="true"></span>
          <span class="stage__n">{{ s.n }}</span>
          <span class="stage__label">{{ s.label }}</span>
        </li>
      </ol>

      <button class="skip-btn" @click="goApp">
        Skip
        <svg width="11" height="11" viewBox="0 0 14 14" aria-hidden="true">
          <path
            d="M2 7h10M8 3.5L11.5 7 8 10.5"
            stroke="currentColor"
            stroke-width="1.4"
            fill="none"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </button>
    </main>
  </div>
</template>

<style scoped>
.loading {
  position: relative;
  min-height: 100vh;
  font-family: 'IBM Plex Sans', system-ui, sans-serif;
  color: #1b1e23;
  background: #f4f3ef;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading__bg {
  position: fixed;
  inset: -12%;
  pointer-events: none;
  z-index: 0;
  background:
    radial-gradient(60% 50% at 18% 22%, rgba(44, 74, 99, 0.06), transparent 60%),
    radial-gradient(55% 45% at 82% 78%, rgba(138, 101, 22, 0.05), transparent 60%),
    radial-gradient(40% 35% at 50% 50%, rgba(255, 255, 255, 0.55), transparent 70%);
  animation: cedarDrift 26s ease-in-out infinite;
  will-change: transform;
}

.loading__main {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 520px;
  padding: 40px 28px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  animation: cedarFade 0.5s ease both;
}

/* breathing mark */
.loading__mark {
  position: relative;
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 28px;
}
.loading__ring {
  position: absolute;
  inset: 0;
  border: 1px solid #ddd9cf;
  border-radius: 50%;
}
.loading__ring::after {
  content: '';
  position: absolute;
  inset: 10px;
  border: 1px solid #e7e4dc;
  border-radius: 50%;
  animation: cedarBreathe 3.4s ease-in-out infinite;
}
.loading__dot {
  width: 10px;
  height: 10px;
  background: #2c4a63;
  animation: cedarBreathe 2.6s ease-in-out infinite;
  will-change: transform, opacity;
}

.overline {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #8a6516;
  margin-bottom: 16px;
}

.loading__title {
  font-family: 'Source Serif 4', Georgia, serif;
  font-weight: 400;
  font-size: 28px;
  line-height: 1.25;
  letter-spacing: -0.01em;
  color: #1b1e23;
  margin: 0 0 12px;
  text-wrap: balance;
}
.loading__period {
  color: #2c4a63;
}

.loading__sub {
  font-size: 14.5px;
  line-height: 1.6;
  color: #6a6f68;
  margin: 0 0 36px;
  max-width: 380px;
}

/* progress */
.progress {
  width: 100%;
  max-width: 440px;
  margin-bottom: 28px;
}
.progress__track {
  position: relative;
  height: 3px;
  background: #e3e1da;
  border-radius: 2px;
  overflow: hidden;
}
.progress__fill {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: #2c4a63;
  border-radius: 2px;
  transition: width 0.12s linear;
}
.progress__meta {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-top: 11px;
}
.progress__stage {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11px;
  color: #2c4a63;
  font-weight: 500;
  letter-spacing: 0.04em;
}
.progress__pct {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11px;
  color: #9a9f97;
}
.progress__detail {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10.5px;
  color: #a7aaa2;
  margin-top: 6px;
  text-align: left;
  min-height: 14px;
}

/* stages list */
.stages {
  list-style: none;
  margin: 0 0 28px;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0;
  width: 100%;
  max-width: 320px;
}
.stage {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 4px;
  border-top: 1px solid #ece9e1;
  opacity: 0.4;
  transition: opacity 0.3s ease;
}
.stage:last-child {
  border-bottom: 1px solid #ece9e1;
}
.stage__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #c4c1b6;
  flex: none;
  transition:
    background 0.3s ease,
    box-shadow 0.3s ease;
}
.stage__n {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10.5px;
  color: #a7aaa2;
  letter-spacing: 0.04em;
  width: 22px;
  flex: none;
}
.stage__label {
  font-size: 12.5px;
  color: #6a6f68;
}

.stage--done {
  opacity: 0.55;
}
.stage--done .stage__dot {
  background: #2c4a63;
}
.stage--done .stage__n {
  color: #2c4a63;
}
.stage--done .stage__label {
  color: #42474e;
}

.stage--active {
  opacity: 1;
}
.stage--active .stage__dot {
  background: #2c4a63;
  box-shadow: 0 0 0 4px rgba(44, 74, 99, 0.12);
  animation: cedarPulse 1.1s ease-in-out infinite;
}
.stage--active .stage__n {
  color: #2c4a63;
  font-weight: 500;
}
.stage--active .stage__label {
  color: #1b1e23;
  font-weight: 500;
}

/* skip */
.skip-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 7px 12px;
  background: transparent;
  border: 1px solid #ddd9cf;
  border-radius: 3px;
  cursor: pointer;
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 12px;
  color: #8a8f87;
  transition:
    color 0.2s ease,
    border-color 0.2s ease;
}
.skip-btn:hover {
  color: #2c4a63;
  border-color: #2c4a63;
}
.skip-btn svg {
  transition: transform 0.2s ease;
}
.skip-btn:hover svg {
  transform: translateX(2px);
}
</style>
