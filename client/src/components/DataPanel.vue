<script setup lang="ts">
import { useCedar } from '@/composables/useCedar'

const { state, panelScrollRef, citesRef, panelData, togglePanel, toggleCites } = useCedar()
</script>

<template>
  <aside class="data-panel" style="animation: cedarSlide 0.3s ease both">
    <!-- Header -->
    <div class="panel-header">
      <span
        style="width: 6px; height: 6px; border-radius: 50%; background: #2f6b4f; flex: none"
      ></span>
      <div class="panel-title">Verified Data</div>
      <button @click="togglePanel" class="close-btn">
        <svg width="13" height="13" viewBox="0 0 14 14">
          <path d="M3 3l8 8M11 3l-8 8" stroke="#8a8f87" stroke-width="1.4" stroke-linecap="round" />
        </svg>
      </button>
    </div>

    <!-- Scrollable content -->
    <div ref="panelScrollRef" style="flex: 1; overflow-y: auto; padding: 16px 16px 22px">
      <div style="font-size: 12px; color: #8a8f87; margin: 2px 2px 14px; line-height: 1.5">
        {{ panelData.contextLabel }}
      </div>

      <!-- SDGs -->
      <div style="margin: 0 0 18px">
        <div style="display: flex; align-items: center; gap: 7px; margin-bottom: 10px">
          <span class="mono-label">SDGs in play</span>
          <span style="font-size: 10px; color: #bfc2b9">weighted by relevance</span>
        </div>
        <div style="display: flex; flex-direction: column; gap: 8px">
          <div v-for="sdg in panelData.sdgs" :key="sdg.n" class="sdg-card">
            <div style="display: flex; align-items: center; gap: 9px">
              <div
                :style="{
                  width: '22px',
                  height: '22px',
                  borderRadius: '3px',
                  background: sdg.color,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flex: 'none',
                }"
              >
                <span
                  style="
                    font-family: 'IBM Plex Mono', monospace;
                    font-weight: 600;
                    font-size: 11px;
                    color: #fff;
                  "
                  >{{ sdg.n }}</span
                >
              </div>
              <span
                style="font-size: 11.5px; line-height: 1.25; color: #42474e; flex: 1; min-width: 0"
                >{{ sdg.label }}</span
              >
              <span
                style="
                  font-family: 'IBM Plex Mono', monospace;
                  font-size: 12px;
                  font-weight: 500;
                  color: #33373d;
                  flex: none;
                "
                >{{ sdg.weight }}%</span
              >
            </div>
            <div
              style="
                height: 5px;
                border-radius: 3px;
                background: #eeece6;
                margin-top: 9px;
                overflow: hidden;
              "
            >
              <div
                :style="{
                  height: '100%',
                  width: sdg.weight + '%',
                  background: sdg.color,
                  borderRadius: '3px',
                }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- KPI cards -->
      <div style="display: flex; flex-direction: column; gap: 12px">
        <div v-for="kpi in panelData.kpis" :key="kpi.indicator" class="kpi-card">
          <div
            style="
              font-size: 12.5px;
              font-weight: 500;
              color: #42474e;
              margin-bottom: 10px;
              line-height: 1.35;
            "
          >
            {{ kpi.indicator }}
          </div>
          <div
            style="display: flex; align-items: flex-end; justify-content: space-between; gap: 12px"
          >
            <div style="display: flex; align-items: baseline; gap: 5px">
              <span
                style="
                  font-family: 'IBM Plex Mono', monospace;
                  font-size: 27px;
                  font-weight: 500;
                  color: #1b1e23;
                  line-height: 1;
                  letter-spacing: -0.01em;
                "
                >{{ kpi.value }}</span
              >
              <span style="font-size: 11px; color: #9a9f97">{{ kpi.unit }}</span>
            </div>
            <svg
              viewBox="0 0 124 30"
              style="width: 124px; height: 30px; display: block; flex: none"
            >
              <path :d="kpi.area" style="fill: #eef2f5; stroke: none" />
              <path
                :d="kpi.line"
                style="
                  fill: none;
                  stroke: #2c4a63;
                  stroke-width: 1.5px;
                  stroke-linejoin: round;
                  stroke-linecap: round;
                "
              />
              <circle :cx="kpi.dotX" :cy="kpi.dotY" r="2.3" style="fill: #2c4a63" />
            </svg>
          </div>
          <div
            style="
              display: flex;
              align-items: center;
              gap: 8px;
              margin-top: 13px;
              padding-top: 11px;
              border-top: 1px solid #efece4;
            "
          >
            <span
              :style="
                (kpi.pillStyle || '') +
                'display:inline-block;padding:2px 7px;border-radius:2px;font-family:IBM Plex Mono,monospace;font-size:10px;letter-spacing:.03em;'
              "
              >{{ kpi.confidence }}</span
            >
            <span
              style="font-family: 'IBM Plex Mono', monospace; font-size: 10.5px; color: #a7aaa2"
              >{{ kpi.year }}</span
            >
            <span
              style="
                margin-left: auto;
                font-size: 10.5px;
                color: #9a9f97;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
                max-width: 140px;
              "
              >{{ kpi.source }}</span
            >
          </div>
        </div>
      </div>

      <!-- Decision-ready actions -->
      <div style="margin-top: 20px; border-top: 1px solid #e7e4dc; padding-top: 15px">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 11px">
          <svg width="13" height="13" viewBox="0 0 14 14" style="flex: none">
            <path
              d="M2 7l3.5 3.5L12 3.5"
              stroke="#2c4a63"
              stroke-width="1.5"
              fill="none"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
          <span class="section-label">Insights</span>
        </div>
        <div style="display: flex; flex-direction: column; gap: 8px">
          <div v-for="act in panelData.actions" :key="act.idx" class="action-card">
            <div style="display: flex; gap: 11px">
              <span
                style="
                  font-family: 'IBM Plex Mono', monospace;
                  font-size: 11px;
                  color: #2c4a63;
                  flex: none;
                  line-height: 1.4;
                "
                >{{ act.idx }}</span
              >
              <span style="font-size: 12px; line-height: 1.45; color: #3a3f46; text-wrap: pretty">{{
                act.text
              }}</span>
            </div>
            <div
              v-if="act.hasChips"
              style="display: flex; gap: 6px; flex-wrap: wrap; padding-left: 22px"
            >
              <button v-for="chip in act.chips" :key="chip.n" @click="chip.run()" class="chip-btn">
                <svg width="9" height="9" viewBox="0 0 10 10" style="flex: none">
                  <path
                    d="M3.5 6.5L6.5 3.5M4 3.5h2.5V6"
                    stroke="#2c4a63"
                    stroke-width="1"
                    fill="none"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
                Source {{ chip.n }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Citations -->
      <div ref="citesRef" style="margin-top: 18px; border-top: 1px solid #e7e4dc; padding-top: 6px">
        <button @click="toggleCites" class="cites-toggle">
          <span class="section-label">Citations</span>
          <span
            style="font-family: 'IBM Plex Mono', monospace; font-size: 10.5px; color: #bfc2b9"
            >{{ panelData.citations.length }}</span
          >
          <span style="margin-left: auto; color: #a7aaa2">{{ state.citesOpen ? '−' : '+' }}</span>
        </button>
        <div v-if="state.citesOpen" style="padding: 2px 2px 4px">
          <div v-for="c in panelData.citations" :key="c.n" :style="c.rowStyle">
            <span
              style="
                font-family: 'IBM Plex Mono', monospace;
                font-size: 11px;
                color: #2c4a63;
                flex: none;
                width: 13px;
              "
              >{{ c.n }}</span
            >
            <div style="min-width: 0">
              <div style="font-size: 11.5px; line-height: 1.5; color: #5a6068">{{ c.text }}</div>
              <div
                style="
                  display: flex;
                  align-items: center;
                  gap: 5px;
                  margin-top: 4px;
                  font-family: 'IBM Plex Mono', monospace;
                  font-size: 10px;
                  color: #2c4a63;
                "
              >
                <svg width="9" height="9" viewBox="0 0 10 10">
                  <path
                    d="M3.5 6.5L6.5 3.5M4 3.5h2.5V6"
                    stroke="#2c4a63"
                    stroke-width="1"
                    fill="none"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
                {{ c.host }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="panel-footer">
      Figures reconciled across source APIs. Confidence reflects data recency and method.
      Illustrative values.
    </div>
  </aside>
</template>

<style scoped>
.data-panel {
  width: 392px;
  flex: none;
  border-left: 1px solid #e3e1da;
  background: #faf9f6;
  display: flex;
  flex-direction: column;
}

.panel-header {
  height: 57px;
  flex: none;
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 0 18px;
  border-bottom: 1px solid #ece9e1;
}
.panel-title {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #33373d;
  font-weight: 500;
}
.close-btn {
  margin-left: auto;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 3px;
  cursor: pointer;
}
.close-btn:hover {
  background: #ece9e1;
}

.mono-label {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #a7aaa2;
}
.section-label {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10.5px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #33373d;
  font-weight: 500;
}

.sdg-card {
  background: #fff;
  border: 1px solid #e3e1da;
  border-radius: 4px;
  padding: 9px 11px;
}

.kpi-card {
  background: #fff;
  border: 1px solid #e3e1da;
  border-radius: 4px;
  padding: 14px 15px;
}

.action-card {
  display: flex;
  flex-direction: column;
  gap: 9px;
  background: #fff;
  border: 1px solid #e3e1da;
  border-left: 2px solid #2c4a63;
  border-radius: 3px;
  padding: 11px 12px;
}

.chip-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 8px;
  background: #f1f4f7;
  border: 1px solid #dce6ee;
  border-radius: 3px;
  cursor: pointer;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.02em;
  color: #2c4a63;
}
.chip-btn:hover {
  background: #e2eaf1;
  border-color: #bcd0e0;
}

.cites-toggle {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 2px;
  background: transparent;
  border: none;
  cursor: pointer;
}

.panel-footer {
  flex: none;
  border-top: 1px solid #ece9e1;
  padding: 11px 16px;
  font-size: 10px;
  color: #a7aaa2;
  line-height: 1.5;
}
</style>
