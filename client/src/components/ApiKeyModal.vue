<script setup lang="ts">
import { ref } from 'vue'
import { useMode } from '@/composables/useMode'

const { state, saveApiKey, closeKeyModal } = useMode()

const inputKey = ref(state.apiKey === '__env__' ? '' : state.apiKey)

function submit() {
  if (!inputKey.value.trim()) return
  saveApiKey(inputKey.value)
}

function onBackdrop(e: MouseEvent) {
  if (e.target === e.currentTarget) closeKeyModal()
}
</script>

<template>
  <Teleport to="body">
    <div v-if="state.keyModalOpen" class="modal-backdrop" @click="onBackdrop">
      <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <div class="modal-header">
          <div style="display:flex;align-items:center;gap:9px;">
            <svg width="14" height="14" viewBox="0 0 16 16" style="flex:none;">
              <path
                d="M6.5 10.5a4 4 0 100-8 4 4 0 000 8zM10 9.5l4 4"
                stroke="#2c4a63"
                stroke-width="1.4"
                fill="none"
                stroke-linecap="round"
              />
            </svg>
            <span id="modal-title" class="modal-title">OpenAI API Key</span>
          </div>
          <button @click="closeKeyModal" class="close-btn" aria-label="Close">
            <svg width="13" height="13" viewBox="0 0 14 14">
              <path d="M3 3l8 8M11 3l-8 8" stroke="#8a8f87" stroke-width="1.4" stroke-linecap="round" />
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <p class="modal-desc">
            Copilot mode requires an OpenAI key. It is passed per request and never stored on the
            server — only in your browser's local storage.
          </p>

          <label class="field-label" for="api-key-input">Your key</label>
          <div class="input-wrap">
            <input
              id="api-key-input"
              v-model="inputKey"
              type="password"
              placeholder="sk-…"
              class="key-input"
              @keydown.enter="submit"
              autocomplete="off"
            />
          </div>

          <div class="modal-actions">
            <button @click="closeKeyModal" class="btn-cancel">Cancel</button>
            <button @click="submit" class="btn-save" :disabled="!inputKey.trim()">
              Save & enable Copilot
            </button>
          </div>

          <p class="modal-hint">
            Key is stored in <code>localStorage</code> and sent via
            <code>X-OpenAI-Key</code> header only when using Copilot endpoints.
          </p>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(27, 30, 35, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  backdrop-filter: blur(1px);
}

.modal {
  width: 440px;
  max-width: calc(100vw - 40px);
  background: #fff;
  border: 1px solid #ddd9cf;
  border-radius: 6px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #ece9e1;
}

.modal-title {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11.5px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  font-weight: 500;
  color: #2c4a63;
}

.close-btn {
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
  background: #f0ede5;
}

.modal-body {
  padding: 20px 20px 22px;
}

.modal-desc {
  font-size: 13.5px;
  line-height: 1.6;
  color: #4a4f57;
  margin: 0 0 18px;
}

.field-label {
  display: block;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #8a8f87;
  margin-bottom: 7px;
}

.input-wrap {
  margin-bottom: 18px;
}

.key-input {
  width: 100%;
  box-sizing: border-box;
  padding: 9px 12px;
  border: 1px solid #ddd9cf;
  border-radius: 3px;
  font-size: 13.5px;
  font-family: 'IBM Plex Mono', monospace;
  color: #1b1e23;
  background: #faf9f6;
  outline: none;
}
.key-input:focus {
  border-color: #2c4a63;
  background: #fff;
}

.modal-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.btn-cancel {
  padding: 8px 14px;
  background: transparent;
  border: 1px solid #ddd9cf;
  border-radius: 3px;
  cursor: pointer;
  font-size: 13px;
  color: #6a6f68;
}
.btn-cancel:hover {
  border-color: #9a9f97;
}

.btn-save {
  padding: 8px 16px;
  background: #2c4a63;
  border: none;
  border-radius: 3px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: #fff;
}
.btn-save:hover:not(:disabled) {
  background: #22405a;
}
.btn-save:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.modal-hint {
  margin: 14px 0 0;
  font-size: 11px;
  line-height: 1.55;
  color: #a7aaa2;
}
.modal-hint code {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10.5px;
  background: #f0ede5;
  padding: 1px 4px;
  border-radius: 2px;
  color: #5a6068;
}
</style>
