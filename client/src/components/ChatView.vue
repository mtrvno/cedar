<script setup lang="ts">
import { useCedar } from '@/composables/useCedar'

const { state, scrollRef, enrichedMessages, examples, togglePanel, ask, onInput, onKey } =
  useCedar()
</script>

<template>
  <div ref="scrollRef" style="flex: 1; overflow-y: auto">
    <!-- Empty state -->
    <div
      v-if="enrichedMessages.length === 0"
      style="max-width: 600px; margin: 0 auto; padding: 13vh 28px 40px"
    >
      <div class="overline" style="margin-bottom: 18px">Verified development intelligence</div>
      <h1 class="hero-title">Ask in plain language. Every figure traces back to its source.</h1>
      <p
        style="
          font-size: 14.5px;
          line-height: 1.6;
          color: #6a6f68;
          margin: 0 0 34px;
          max-width: 480px;
        "
      >
        CEDAR answers questions about countries and development indicators, returning evidence where
        each number carries a confidence tier and a verified source API.
      </p>

      <div class="mono-label" style="margin-bottom: 11px">Try asking</div>
      <div style="display: flex; flex-direction: column; border-top: 1px solid #e7e4dc">
        <button v-for="ex in examples" :key="ex.label" @click="ex.run()" class="example-btn">
          <span style="font-family: 'IBM Plex Mono', monospace; color: #bfc2b9; font-size: 13px"
            >→</span
          >
          {{ ex.label }}
        </button>
      </div>
    </div>

    <!-- Messages -->
    <div
      v-if="enrichedMessages.length > 0"
      style="max-width: 716px; margin: 0 auto; padding: 30px 28px 26px"
    >
      <template v-for="msg in enrichedMessages" :key="msg.role + msg.text">
        <!-- User message -->
        <div v-if="msg.isUser" style="margin: 0 0 24px">
          <div class="overline" style="margin-bottom: 7px">Query</div>
          <div style="font-size: 18px; font-weight: 500; line-height: 1.45; color: #1b1e23">
            {{ msg.text }}
          </div>
        </div>

        <!-- Assistant message -->
        <div v-if="msg.isAssistant" style="margin: 0 0 36px; animation: cedarFade 0.4s ease both">
          <div style="display: flex; align-items: center; gap: 9px; margin-bottom: 13px">
            <span style="width: 6px; height: 6px; background: #2c4a63; flex: none"></span>
            <span
              style="
                font-family: 'IBM Plex Mono', monospace;
                font-size: 10px;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                color: #2c4a63;
                font-weight: 500;
              "
              >CEDAR</span
            >
            <span
              v-if="msg.contextLabel"
              style="
                font-size: 11px;
                color: #9a9f97;
                border-left: 1px solid #ddd9cf;
                padding-left: 9px;
              "
              >{{ msg.contextLabel }}</span
            >
          </div>

          <div style="font-family: 'Source Serif 4', Georgia, serif">
            <p
              v-for="(para, pi) in msg.paragraphs"
              :key="pi"
              style="
                font-size: 18px;
                line-height: 1.66;
                color: #2a2e34;
                margin: 0 0 15px;
                text-wrap: pretty;
              "
            >
              <span v-html="para.text"></span
              ><sup
                v-if="para.cite"
                style="
                  font-family: 'IBM Plex Mono', monospace;
                  font-size: 10px;
                  color: #2c4a63;
                  font-weight: 500;
                  vertical-align: super;
                  margin-left: 1px;
                "
                >{{ para.cite }}</sup
              >
            </p>
          </div>

          <button v-if="msg.hasData" @click="togglePanel" class="view-data-btn">
            <span style="width: 5px; height: 5px; border-radius: 50%; background: #2f6b4f"></span>
            <template v-if="msg.kpiCount">{{ msg.kpiCount }} VERIFIED INDICATORS · </template>VIEW DATA
          </button>

          <!-- Chain of action -->
          <div
            v-if="msg.steps && msg.steps.length"
            style="
              margin-top: 18px;
              border: 1px solid #e7e4dc;
              border-radius: 6px;
              background: #faf9f6;
              padding: 15px 17px 4px;
            "
          >
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 15px">
              <svg width="13" height="13" viewBox="0 0 14 14" style="flex: none">
                <circle cx="3" cy="3" r="2" stroke="#2c4a63" stroke-width="1.1" fill="none" />
                <circle cx="3" cy="11" r="2" stroke="#2c4a63" stroke-width="1.1" fill="none" />
                <circle cx="11" cy="11" r="2" fill="#2c4a63" />
                <path
                  d="M3 5v3.5M3 9.5h5a1 1 0 001-1V13"
                  stroke="#2c4a63"
                  stroke-width="1.1"
                  fill="none"
                />
              </svg>
              <span
                style="
                  font-family: 'IBM Plex Mono', monospace;
                  font-size: 10.5px;
                  letter-spacing: 0.1em;
                  text-transform: uppercase;
                  color: #33373d;
                  font-weight: 500;
                "
                >Chain of action</span
              >
              <span style="font-family: 'IBM Plex Mono', monospace; font-size: 10px; color: #bfc2b9"
                >{{ msg.stepCount }} STEPS</span
              >
            </div>
            <div v-for="step in msg.steps" :key="step.idx" style="display: flex; gap: 13px">
              <div style="display: flex; flex-direction: column; align-items: center; flex: none">
                <div
                  style="
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    border: 1px solid #c4cdd6;
                    background: #fff;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex: none;
                  "
                >
                  <span
                    style="
                      font-family: 'IBM Plex Mono', monospace;
                      font-size: 10px;
                      color: #2c4a63;
                      font-weight: 500;
                    "
                    >{{ step.idx }}</span
                  >
                </div>
                <div
                  v-if="step.notLast"
                  style="width: 1px; flex: 1; min-height: 13px; background: #ddd9cf; margin: 2px 0"
                ></div>
              </div>
              <div style="padding-bottom: 13px; min-width: 0">
                <div style="font-size: 12.5px; font-weight: 500; color: #33373d">
                  {{ step.label }}
                </div>
                <div
                  style="
                    font-family: 'IBM Plex Mono', monospace;
                    font-size: 10.5px;
                    color: #9a9f97;
                    margin-top: 2px;
                    line-height: 1.4;
                  "
                >
                  {{ step.detail }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- Thinking indicator -->
      <div
        v-if="state.thinking"
        style="display: flex; align-items: center; gap: 11px; margin: 2px 0 30px"
      >
        <span
          style="
            width: 6px;
            height: 6px;
            background: #2c4a63;
            flex: none;
            animation: cedarPulse 1.1s ease-in-out infinite;
          "
        ></span>
        <span
          style="
            font-family: 'IBM Plex Mono', monospace;
            font-size: 11px;
            letter-spacing: 0.05em;
            color: #8a8f87;
          "
          >Consulting verified sources…</span
        >
      </div>
    </div>
  </div>

  <!-- Input area -->
  <div
    style="flex: none; border-top: 1px solid #e3e1da; background: #f7f6f3; padding: 14px 20px 17px"
  >
    <div class="input-wrap">
      <textarea
        rows="1"
        :value="state.input"
        @input="onInput"
        @keydown="onKey"
        placeholder="Ask about a country and an indicator…"
        class="query-textarea"
      ></textarea>
      <button @click="() => ask(state.input)" class="send-btn">
        <svg width="15" height="15" viewBox="0 0 16 16">
          <path
            d="M8 13V3M8 3L3.5 7.5M8 3l4.5 4.5"
            stroke="#fff"
            stroke-width="1.5"
            fill="none"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </button>
    </div>
    <div
      style="
        max-width: 716px;
        margin: 7px auto 0;
        font-size: 10.5px;
        color: #a7aaa2;
        text-align: center;
      "
    >
      CEDAR returns only figures it can trace to a verified source. Data shown is illustrative.
    </div>
  </div>
</template>

<style scoped>
.overline {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #a7aaa2;
}
.mono-label {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10.5px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #a7aaa2;
}
.hero-title {
  font-family: 'Source Serif 4', Georgia, serif;
  font-weight: 400;
  font-size: 33px;
  line-height: 1.25;
  letter-spacing: -0.01em;
  color: #1b1e23;
  margin: 0 0 14px;
}

.example-btn {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 13px 4px;
  background: transparent;
  border: none;
  border-bottom: 1px solid #e7e4dc;
  cursor: pointer;
  font-size: 14.5px;
  color: #34383f;
  text-align: left;
  transition:
    color 0.15s,
    padding-left 0.15s;
}
.example-btn:hover {
  color: #2c4a63;
  padding-left: 9px;
}

.view-data-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
  padding: 7px 12px;
  background: #eef2f5;
  border: 1px solid #dce6ee;
  border-radius: 3px;
  cursor: pointer;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11px;
  letter-spacing: 0.03em;
  color: #2c4a63;
}
.view-data-btn:hover {
  background: #e4ecf2;
}

.input-wrap {
  max-width: 716px;
  margin: 0 auto;
  display: flex;
  align-items: flex-end;
  gap: 10px;
  background: #fff;
  border: 1px solid #ddd9cf;
  border-radius: 4px;
  padding: 8px 8px 8px 14px;
}
.input-wrap:focus-within {
  border-color: #2c4a63;
}

.query-textarea {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  background: transparent;
  font-size: 14.5px;
  line-height: 1.5;
  color: #1b1e23;
  padding: 6px 0;
  max-height: 120px;
}

.send-btn {
  width: 34px;
  height: 34px;
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #2c4a63;
  border: none;
  border-radius: 3px;
  cursor: pointer;
}
.send-btn:hover {
  background: #22405a;
}
</style>
