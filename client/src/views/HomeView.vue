<script setup lang="ts">
import AppSidebar from '@/components/AppSidebar.vue'
import ChatView from '@/components/ChatView.vue'
import BriefView from '@/components/BriefView.vue'
import DataPanel from '@/components/DataPanel.vue'
import { useCedar } from '@/composables/useCedar'

const {
  state,
  isChat,
  panelShown,
  showBriefBtn,
  showPanelBtn,
  panelBtnStyle,
  panelBtnLabel,
  toggleSidebar,
  togglePanel,
  openBrief,
} = useCedar()
</script>

<template>
  <div class="cedar-app">
    <AppSidebar />

    <main style="flex: 1; min-width: 0; display: flex; flex-direction: column; background: #f4f3ef">
      <!-- Header -->
      <header class="app-header">
        <button @click="toggleSidebar" class="sidebar-toggle">
          <svg width="15" height="15" viewBox="0 0 16 16">
            <path
              d="M1 3h14M1 8h14M1 13h14"
              stroke="#5a6068"
              stroke-width="1.4"
              stroke-linecap="round"
            />
          </svg>
        </button>

        <div
          v-if="isChat && state.convTitle !== 'New query'"
          style="
            font-size: 13.5px;
            font-weight: 500;
            color: #33373d;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          "
        >
          {{ state.convTitle }}
        </div>
        <div
          v-if="!isChat"
          style="
            font-family: 'IBM Plex Mono', monospace;
            font-size: 11px;
            letter-spacing: 0.13em;
            text-transform: uppercase;
            color: #8a6516;
          "
        >
          Evidence Brief
        </div>

        <div style="margin-left: auto; display: flex; align-items: center; gap: 8px">
          <button v-if="showBriefBtn" @click="openBrief" class="header-btn">
            <svg width="13" height="13" viewBox="0 0 14 14">
              <rect
                x="2.5"
                y="1.5"
                width="9"
                height="11"
                rx="1"
                stroke="#6a6f63"
                stroke-width="1.2"
                fill="none"
              />
              <path
                d="M4.5 5h5M4.5 7.5h5M4.5 10h3"
                stroke="#6a6f63"
                stroke-width="1.1"
                stroke-linecap="round"
              />
            </svg>
            Generate brief
          </button>
          <button
            v-if="showPanelBtn"
            @click="togglePanel"
            :style="panelBtnStyle"
            class="panel-toggle-btn"
          >
            <svg width="13" height="13" viewBox="0 0 14 14">
              <rect
                x="1"
                y="1.5"
                width="12"
                height="11"
                rx="1"
                stroke="#2c4a63"
                stroke-width="1.2"
                fill="none"
              />
              <path d="M9 1.5v11" stroke="#2c4a63" stroke-width="1.2" />
              <rect x="9" y="1.5" width="4" height="11" fill="#dce6ee" />
            </svg>
            {{ panelBtnLabel }}
          </button>
        </div>
      </header>

      <!-- Main content -->
      <ChatView
        v-if="isChat"
        style="display: flex; flex-direction: column; flex: 1; min-height: 0"
      />
      <BriefView v-else style="display: flex; flex-direction: column; flex: 1; min-height: 0" />
    </main>

    <DataPanel v-if="panelShown" />
  </div>
</template>

<style scoped>
.cedar-app {
  display: flex;
  height: 100vh;
  width: 100%;
  font-family: 'IBM Plex Sans', system-ui, sans-serif;
  color: #1b1e23;
  background: #f4f3ef;
  overflow: hidden;
}

.app-header {
  height: 57px;
  flex: none;
  border-bottom: 1px solid #e3e1da;
  display: flex;
  align-items: center;
  gap: 13px;
  padding: 0 18px;
  background: #f7f6f3;
}

.sidebar-toggle {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 3px;
  cursor: pointer;
  flex: none;
}
.sidebar-toggle:hover {
  background: #ece9e1;
}

.header-btn {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 7px 12px;
  background: transparent;
  border: 1px solid #ddd9cf;
  border-radius: 3px;
  cursor: pointer;
  font-size: 12.5px;
  font-weight: 500;
  color: #42474e;
}
.header-btn:hover {
  border-color: #2c4a63;
  color: #2c4a63;
}

.panel-toggle-btn:hover {
  border-color: #2c4a63 !important;
}
</style>
