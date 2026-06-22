<script setup lang="ts">
import { useCedar } from '@/composables/useCedar'

const { brief, closeBrief, tierStyle } = useCedar()

const briefDate = new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })
</script>

<template>
  <div style="flex:1;overflow-y:auto;background:#ecebe5;">
    <div style="max-width:760px;margin:0 auto;padding:22px 28px 60px;">
      <button @click="closeBrief" class="back-btn">
        <svg width="13" height="13" viewBox="0 0 14 14">
          <path d="M8.5 2L3.5 7l5 5" stroke="#6a6f68" stroke-width="1.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Back to conversation
      </button>

      <article class="brief-article">
        <div class="brief-tag">Evidence Brief</div>
        <h1 class="brief-title">{{ brief.contextLabel }}</h1>
        <div class="brief-meta">
          <span>PREPARED BY CEDAR</span>
          <span class="sep">|</span>
          <span>{{ briefDate }}</span>
          <span class="sep">|</span>
          <span>{{ brief.kpiCount }} INDICATORS</span>
        </div>

        <table class="brief-table">
          <thead>
            <tr>
              <th class="th" style="text-align:left;padding-right:8px;">Indicator</th>
              <th class="th" style="text-align:right;padding:0 8px;">Value</th>
              <th class="th" style="text-align:right;padding:0 8px;">Year</th>
              <th class="th" style="text-align:right;padding-left:8px;">Conf.</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="k in brief.kpis" :key="k.indicator" style="border-bottom:1px solid #ece9e1;">
              <td style="padding:11px 8px 11px 0;font-size:13.5px;color:#2a2e34;">
                {{ k.indicator }}
                <div style="font-size:11px;color:#9a9f97;margin-top:2px;">{{ k.source }}</div>
              </td>
              <td style="padding:11px 8px;text-align:right;font-family:'IBM Plex Mono',monospace;font-size:14px;font-weight:500;color:#1b1e23;white-space:nowrap;">
                {{ k.value }}<span style="font-size:10px;color:#a7aaa2;margin-left:3px;">{{ k.unit }}</span>
              </td>
              <td style="padding:11px 8px;text-align:right;font-family:'IBM Plex Mono',monospace;font-size:13px;color:#6a6f68;">{{ k.year }}</td>
              <td style="padding:11px 0 11px 8px;text-align:right;">
                <span :style="tierStyle(k.confidence) + 'display:inline-block;padding:2px 7px;border-radius:2px;font-family:IBM Plex Mono,monospace;font-size:10px;letter-spacing:.04em;'">
                  {{ k.confidence }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>

        <div style="font-family:'Source Serif 4',Georgia,serif;">
          <p
            v-for="(para, i) in brief.paragraphs"
            :key="i"
            style="font-size:17px;line-height:1.7;color:#2a2e34;margin:0 0 16px;text-wrap:pretty;"
          >
            <span v-html="para.text"></span><sup v-if="para.cite" style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:#2c4a63;font-weight:500;vertical-align:super;margin-left:1px;">{{ para.cite }}</sup>
          </p>
        </div>

        <div style="margin-top:34px;border-top:1px solid #e7e4dc;padding-top:18px;">
          <div class="section-label" style="margin-bottom:12px;">Sources</div>
          <div v-for="c in brief.citations" :key="c.n" style="display:flex;gap:10px;margin-bottom:9px;">
            <span style="font-family:'IBM Plex Mono',monospace;font-size:11px;color:#2c4a63;flex:none;width:14px;">{{ c.n }}</span>
            <span style="font-size:12.5px;line-height:1.5;color:#5a6068;">{{ c.text }}</span>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>

<style scoped>
.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 18px;
  padding: 6px 2px;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 12.5px;
  color: #6a6f68;
}
.back-btn:hover { color: #2c4a63; }

.brief-article {
  background: #fff;
  border: 1px solid #e0ddd4;
  box-shadow: 0 1px 3px rgba(0,0,0,.05);
  padding: 54px 58px 56px;
}

.brief-tag {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10.5px;
  letter-spacing: .16em;
  text-transform: uppercase;
  color: #8a6516;
  margin-bottom: 18px;
}

.brief-title {
  font-family: 'Source Serif 4', Georgia, serif;
  font-weight: 500;
  font-size: 30px;
  line-height: 1.2;
  letter-spacing: -.01em;
  color: #1b1e23;
  margin: 0 0 14px;
  text-wrap: pretty;
}

.brief-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 16px;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11px;
  color: #8a8f87;
  border-bottom: 1px solid #e7e4dc;
  padding-bottom: 18px;
  margin-bottom: 26px;
}
.sep { color: #cfccc1; }

.brief-table {
  width: 100%;
  border-collapse: collapse;
  margin: 0 0 30px;
}
.th {
  padding: 0 8px 8px;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 9.5px;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: #8a8f87;
  font-weight: 500;
  border-bottom: 1.5px solid #1b1e23;
}

.section-label {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  letter-spacing: .12em;
  text-transform: uppercase;
  color: #8a8f87;
}
</style>
