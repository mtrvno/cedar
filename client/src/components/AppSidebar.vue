<script setup lang="ts">
import { computed } from 'vue'
import { useCedar } from '@/composables/useCedar'
import { useMode } from '@/composables/useMode'
import { useEvidenceLedger } from '@/composables/useEvidenceLedger'

const { state, historyGroups, tokenInfo, sources, hasData, newQuery } = useCedar()
const { isCopilot, isEvidence, hasKey, state: openKeyModal, clearApiKey } = useMode()
const { countryName, theme, indicators, cost, retrievedAt } = useEvidenceLedger()

const THEME_LABELS: Record<string, string> = {
  'child-survival': 'Child Survival',
  'economy-poverty': 'Economy & Poverty',
  education: 'Education',
  'health-system': 'Health System',
  wash: 'Water & Sanitation',
  'energy-climate': 'Energy & Climate',
}

const ledgerSources = computed(() =>
  indicators.value
    .filter((i) => i.available && i.provenance?.query_url)
    .map((i) => ({
      name: i.name,
      code: i.code,
      year: i.provenance?.retrieved_at as string | undefined,
      served: i.provenance?.served as string | undefined,
      url: i.provenance?.query_url as string,
    })),
)

const apiCalls = computed(() => {
  const c = cost.value as Record<string, unknown> | null
  return c
    ? ((c.api_calls as number | undefined) ?? ledgerSources.value.length)
    : ledgerSources.value.length
})
</script>

<template>
  <!-- Sidebar open -->
  <aside v-if="state.sidebarOpen" class="sidebar sidebar--open">
    <div class="sidebar__header">
      <div class="cedar-logo">
        <div class="cedar-logo__dot"></div>
      </div>
      <div class="sidebar__title">CEDAR</div>
      <div class="sidebar__version">v0.4</div>
    </div>

    <!-- Evidence mode: no "new query" button needed -->
    <div v-if="isCopilot" style="padding: 14px 14px 6px">
      <button @click="newQuery" class="new-query-btn">
        <svg width="13" height="13" viewBox="0 0 14 14">
          <path
            d="M7 1v12M1 7h12"
            stroke="#2c4a63"
            stroke-width="1.5"
            fill="none"
            stroke-linecap="round"
          />
        </svg>
        New query
      </button>
    </div>

    <!-- Evidence mode sidebar -->
    <div
      v-if="isEvidence"
      style="flex: 1; overflow-y: auto; padding: 16px 14px; animation: cedarFade 0.25s ease both"
    >
      <!-- No country selected yet -->
      <template v-if="!countryName">
        <div class="mono-label" style="margin-bottom: 10px">Evidence mode</div>
        <div style="font-size: 12.5px; line-height: 1.55; color: #9a9f97">
          Select a country and theme to see the evidence ledger.
        </div>
      </template>

      <!-- Country loaded: show evidence ledger -->
      <template v-else>
        <!-- Query header -->
        <div class="mono-label" style="margin-bottom: 6px">Evidence Ledger</div>
        <div style="font-size: 13px; font-weight: 500; color: #1b1e23; margin-bottom: 2px">
          {{ countryName }}
        </div>
        <div
          style="
            font-size: 11px;
            color: #9a9f97;
            margin-bottom: 14px;
            font-family: 'IBM Plex Mono', monospace;
          "
        >
          {{ THEME_LABELS[theme] ?? theme }}
          <span v-if="retrievedAt" style="margin-left: 8px; color: #bfc2b9"
            >· {{ retrievedAt }}</span
          >
        </div>

        <!-- Cost pill -->
        <div style="display: flex; gap: 6px; margin-bottom: 14px; flex-wrap: wrap">
          <div class="ledger-pill ledger-pill--green">
            <span
              style="width: 5px; height: 5px; border-radius: 50%; background: #2f6b4f; flex: none"
            ></span>
            $0 LLM cost
          </div>
          <div class="ledger-pill">
            <span style="font-family: 'IBM Plex Mono', monospace; font-size: 9px; color: #2c4a63">{{
              apiCalls
            }}</span>
            API calls
          </div>
        </div>

        <!-- Source list -->
        <div class="mono-label" style="margin-bottom: 8px">
          Sources · {{ ledgerSources.length }}
        </div>
        <div style="display: flex; flex-direction: column; gap: 5px">
          <a
            v-for="s in ledgerSources"
            :key="s.code"
            :href="s.url"
            target="_blank"
            rel="noopener"
            class="ledger-source"
          >
            <div style="display: flex; align-items: center; gap: 6px">
              <span
                class="ledger-served"
                :class="'ledger-served--' + (s.served ?? 'live')"
                :title="s.served ?? 'live'"
              ></span>
              <span
                style="
                  font-family: 'IBM Plex Mono', monospace;
                  font-size: 9.5px;
                  color: #2c4a63;
                  flex: none;
                "
              >
                {{ s.code }}
              </span>
            </div>
            <div style="font-size: 11.5px; color: #33373d; line-height: 1.3; margin-top: 3px">
              {{ s.name }}
            </div>
            <div
              style="
                font-size: 10px;
                color: #bfc2b9;
                margin-top: 2px;
                display: flex;
                align-items: center;
                gap: 4px;
              "
            >
              WB WDI
              <svg width="8" height="8" viewBox="0 0 10 10" style="flex: none">
                <path
                  d="M3.5 6.5L6.5 3.5M4 3.5h2.5V6"
                  stroke="#bfc2b9"
                  stroke-width="1"
                  fill="none"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </div>
          </a>

          <!-- Unavailable indicators -->
          <div
            v-for="i in indicators.filter((x) => !x.available)"
            :key="i.code"
            class="ledger-source ledger-source--missing"
          >
            <div style="font-family: 'IBM Plex Mono', monospace; font-size: 9.5px; color: #bfc2b9">
              {{ i.code }}
            </div>
            <div style="font-size: 11.5px; color: #a7aaa2; line-height: 1.3; margin-top: 3px">
              {{ i.name }}
            </div>
            <div style="font-size: 10px; color: #d4cfc6; margin-top: 2px">No data</div>
          </div>
        </div>
      </template>
    </div>

    <!-- Copilot: History (no active data) -->
    <div v-if="isCopilot && !hasData" style="flex: 1; overflow-y: auto; padding: 8px 8px 12px">
      <div v-for="grp in historyGroups" :key="grp.label">
        <div class="history-label">{{ grp.label }}</div>
        <button
          v-for="it in grp.items"
          :key="it.key"
          @click="it.run()"
          :style="it.style"
          class="history-item-btn"
        >
          <span
            :style="{
              width: '5px',
              height: '5px',
              borderRadius: '50%',
              flex: 'none',
              background: it.dot,
            }"
          ></span>
          <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap">{{
            it.title
          }}</span>
        </button>
      </div>
    </div>

    <!-- Copilot: Active data panel info -->
    <div
      v-if="isCopilot && hasData"
      style="
        flex: 1;
        overflow-y: auto;
        padding: 17px 16px 16px;
        animation: cedarFade 0.35s ease both;
      "
    >
      <div class="mono-label" style="margin-bottom: 4px">This response</div>
      <div
        style="
          font-size: 13px;
          font-weight: 500;
          color: #33373d;
          line-height: 1.3;
          margin-bottom: 18px;
        "
      >
        {{ state.convTitle }}
      </div>

      <div class="mono-label" style="margin-bottom: 8px">Token use · AI</div>
      <div class="token-card">
        <div
          style="
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            margin-bottom: 11px;
          "
        >
          <span
            style="
              font-family: 'IBM Plex Mono', monospace;
              font-size: 23px;
              font-weight: 500;
              color: #2c4a63;
              line-height: 1;
              letter-spacing: -0.01em;
            "
            >{{ tokenInfo.totalStr }}</span
          >
          <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 2px">
            <span style="font-size: 10.5px; color: #9a9f97">total tokens</span>
            <span
              v-if="tokenInfo.costUsd !== null"
              style="font-family: 'IBM Plex Mono', monospace; font-size: 10px; color: #2f6b4f"
            >
              ${{
                tokenInfo.costUsd < 0.001
                  ? tokenInfo.costUsd.toFixed(6)
                  : tokenInfo.costUsd.toFixed(4)
              }}
            </span>
          </div>
        </div>
        <div
          style="
            display: flex;
            height: 6px;
            border-radius: 3px;
            overflow: hidden;
            background: #e7e3d8;
          "
        >
          <div :style="{ width: tokenInfo.inPct + '%', background: '#2c4a63' }"></div>
          <div style="flex: 1; background: #9db1c2"></div>
        </div>
        <div
          style="
            display: flex;
            justify-content: space-between;
            margin-top: 7px;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 10px;
            color: #7a7f77;
          "
        >
          <span style="display: flex; align-items: center; gap: 5px">
            <span style="width: 6px; height: 6px; border-radius: 1px; background: #2c4a63"></span>
            In {{ tokenInfo.inStr }}
          </span>
          <span style="display: flex; align-items: center; gap: 5px">
            Out {{ tokenInfo.outStr }}
            <span style="width: 6px; height: 6px; border-radius: 1px; background: #9db1c2"></span>
          </span>
        </div>
      </div>

      <div style="display: flex; align-items: center; gap: 7px; margin-bottom: 9px">
        <span class="mono-label">Sources cited</span>
        <span style="font-family: 'IBM Plex Mono', monospace; font-size: 10px; color: #bfc2b9">{{
          sources.length
        }}</span>
      </div>
      <div style="display: flex; flex-direction: column; gap: 7px">
        <div
          v-for="s in sources"
          :key="s.n"
          style="
            display: flex;
            align-items: center;
            gap: 8px;
            background: #fff;
            border: 1px solid #e3e1da;
            border-radius: 3px;
            padding: 8px 10px;
            font-size: 11.5px;
            color: #5a6068;
          "
        >
          <span
            style="
              font-family: 'IBM Plex Mono', monospace;
              font-size: 10px;
              color: #2c4a63;
              flex: none;
              width: 11px;
            "
            >{{ s.n }}</span
          >
          <svg width="9" height="9" viewBox="0 0 10 10" style="flex: none">
            <path
              d="M3.5 6.5L6.5 3.5M4 3.5h2.5V6"
              stroke="#9aa3ac"
              stroke-width="1"
              fill="none"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
          <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap">{{
            s.host
          }}</span>
        </div>
      </div>

      <button @click="newQuery" class="back-history-btn">
        <svg width="12" height="12" viewBox="0 0 14 14">
          <path
            d="M8.5 2L3.5 7l5 5"
            stroke="currentColor"
            stroke-width="1.4"
            fill="none"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
        Back to history
      </button>
    </div>

    <!-- API key status (copilot mode) -->
    <div
      v-if="isCopilot"
      class="key-status"
      :class="hasKey ? 'key-status--ok' : 'key-status--missing'"
    >
      <div style="display: flex; align-items: center; gap: 7px; min-width: 0">
        <svg width="11" height="11" viewBox="0 0 12 12" style="flex: none">
          <circle cx="5" cy="5" r="3.5" stroke="currentColor" stroke-width="1.1" fill="none" />
          <path
            d="M7.5 7.5l2.5 2.5"
            stroke="currentColor"
            stroke-width="1.1"
            stroke-linecap="round"
          />
        </svg>
        <span
          style="
            font-family: 'IBM Plex Mono', monospace;
            font-size: 10px;
            letter-spacing: 0.07em;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          "
        >
          {{ hasKey ? 'API key saved' : 'No API key' }}
        </span>
      </div>
      <button v-if="hasKey" @click="clearApiKey" class="key-action-btn" title="Remove key">
        ×
      </button>
      <button v-else @click="openKeyModal" class="key-action-btn key-action-btn--add">
        Add key
      </button>
    </div>

    <!-- User footer -->
    <div class="sidebar__footer">
      <div class="user-avatar">AO</div>
      <div style="min-width: 0">
        <div
          style="
            font-size: 12.5px;
            font-weight: 500;
            color: #33373d;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          "
        >
          A. Okonkwo
        </div>
        <div style="font-size: 10.5px; color: #9a9f97">Policy Analyst</div>
      </div>
    </div>
  </aside>

  <!-- Sidebar collapsed -->
  <aside v-else class="sidebar sidebar--closed">
    <div class="cedar-logo" style="margin-top: 17px">
      <div class="cedar-logo__dot"></div>
    </div>
    <button @click="newQuery" class="icon-btn" style="margin-top: 18px">
      <svg width="13" height="13" viewBox="0 0 14 14">
        <path
          d="M7 1v12M1 7h12"
          stroke="#2c4a63"
          stroke-width="1.5"
          fill="none"
          stroke-linecap="round"
        />
      </svg>
    </button>
  </aside>
</template>

<style scoped>
.sidebar {
  flex: none;
  border-right: 1px solid #e3e1da;
  background: #faf9f6;
  display: flex;
  flex-direction: column;
}
.sidebar--open {
  width: 266px;
}
.sidebar--closed {
  width: 54px;
  align-items: center;
  padding-top: 0;
  gap: 0;
}

.sidebar__header {
  height: 57px;
  flex: none;
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 0 18px;
  border-bottom: 1px solid #ece9e1;
}

.cedar-logo {
  width: 22px;
  height: 22px;
  border: 1.5px solid #2c4a63;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: none;
}
.cedar-logo__dot {
  width: 7px;
  height: 7px;
  background: #2c4a63;
}

.sidebar__title {
  font-weight: 600;
  letter-spacing: 0.14em;
  font-size: 14px;
  color: #1b1e23;
}
.sidebar__version {
  margin-left: auto;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 9.5px;
  letter-spacing: 0.06em;
  color: #a7aaa2;
}

.new-query-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 9px 12px;
  background: #fff;
  border: 1px solid #ddd9cf;
  border-radius: 3px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: #2c4a63;
  text-align: left;
}
.new-query-btn:hover {
  border-color: #2c4a63;
}

.history-label {
  margin: 10px 6px 4px;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #a7aaa2;
}
.history-item-btn:hover {
  background: #f0ede5 !important;
}

.mono-label {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #a7aaa2;
}

.token-card {
  background: #fff;
  border: 1px solid #e3e1da;
  border-radius: 4px;
  padding: 13px 14px;
  margin-bottom: 20px;
}

.back-history-btn {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-top: 20px;
  padding: 7px 2px;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 11.5px;
  color: #8a8f87;
}
.back-history-btn:hover {
  color: #2c4a63;
}

.sidebar__footer {
  flex: none;
  border-top: 1px solid #ece9e1;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 9px;
}
.user-avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #e7e3d8;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  color: #6a6f63;
  flex: none;
}

.icon-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  border: 1px solid #ddd9cf;
  border-radius: 3px;
  cursor: pointer;
}
.icon-btn:hover {
  border-color: #2c4a63;
}

.key-status {
  flex: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 9px 14px;
  border-top: 1px solid #ece9e1;
}
.key-status--ok {
  color: #2f6b4f;
  background: #f0f7f3;
}
.key-status--missing {
  color: #8a6516;
  background: #faf6ee;
}

.key-action-btn {
  flex: none;
  padding: 3px 8px;
  border: 1px solid currentColor;
  border-radius: 2px;
  background: transparent;
  cursor: pointer;
  font-size: 11px;
  color: inherit;
  opacity: 0.7;
}
.key-action-btn:hover {
  opacity: 1;
}
.key-action-btn--add {
  color: #2c4a63;
  border-color: #2c4a63;
}

/* Evidence ledger */
.ledger-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 8px;
  background: #fff;
  border: 1px solid #e3e1da;
  border-radius: 2px;
  font-size: 11px;
  color: #5a6068;
}
.ledger-pill--green {
  background: #f0f7f3;
  border-color: #cfe0d4;
  color: #2f6b4f;
  font-weight: 500;
}

.ledger-source {
  display: block;
  padding: 8px 10px;
  background: #fff;
  border: 1px solid #e3e1da;
  border-radius: 3px;
  text-decoration: none;
  transition: border-color 0.12s;
}
.ledger-source:hover {
  border-color: #2c4a63;
}
.ledger-source--missing {
  background: #faf9f6;
  opacity: 0.6;
  pointer-events: none;
}

.ledger-served {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  flex: none;
}
.ledger-served--live {
  background: #2f6b4f;
}
.ledger-served--cache {
  background: #e67e22;
}
.ledger-served--snapshot {
  background: #9a9f97;
}
</style>
