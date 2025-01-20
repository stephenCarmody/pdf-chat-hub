<template>
  <div
    class="pdf-viewer"
    ref="pdfContainerRef"
    :style="{ width: `calc(100% - 550px + ${rightPaneWidth}px)` }"
  >
    <div v-if="isUploading" class="upload-loading">
      <svg
        class="animate-spin spinner"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          class="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          stroke-width="4"
        ></circle>
        <path
          class="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8v8H4z"
        ></path>
      </svg>
    </div>
    <div v-else-if="!selectedPdf" class="pdf-placeholder">
      No PDF selected
    </div>
    <VuePdfEmbed
      v-else
      :source="selectedPdf.url"
      :width="pdfContainerRef?.clientWidth || 800"
      :height="pdfContainerRef?.clientHeight || 1000"
      class="pdf-view"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import VuePdfEmbed from 'vue-pdf-embed'

defineProps({
  selectedPdf: Object,
  isUploading: Boolean,
  rightPaneWidth: Number
})

const pdfContainerRef = ref(null)
</script>

<style scoped>
.pdf-viewer {
  flex: 1;
  background-color: #ffffff;
  padding: 1rem;
  position: relative;
  overflow: auto;
}

.pdf-placeholder {
  height: 100%;
  border: 2px dashed #ccc;
  border-radius: 0.375rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pdf-view {
  width: 100%;
  height: 100%;
  overflow: auto;
}

.upload-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.animate-spin {
  animation: spin 1s linear infinite;
}

.spinner {
  width: 40px;
  height: 40px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style> 