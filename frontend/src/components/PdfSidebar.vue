<template>
  <div class="sidebar" :style="{ width: '250px' }">
    <div class="upload-button">
      <label
        class="upload-label"
        :class="{ 'opacity-50 cursor-not-allowed': isUploading || !isSessionInitialized }"
      >
        <FileText class="icon" />
        <span>{{ isSessionInitialized ? 'Upload PDF' : 'Initializing...' }}</span>
        <input
          type="file"
          accept=".pdf"
          class="hidden-input"
          @change="$emit('file-upload', $event)"
          :disabled="isUploading || !isSessionInitialized"
        />
      </label>
    </div>

    <div class="pdf-list">
        <div v-if="uploadedPdfs.length === 0" class="no-pdfs">
          No PDFs uploaded yet
        </div>
        <div
          v-for="pdf in uploadedPdfs"
          :key="pdf.id"
          class="pdf-item"
          @click="selectPdf(pdf)"
        >
          <FileText class="icon" />
          <span class="pdf-name text-truncate">{{ pdf.name }}</span>
        </div>
    </div>
  </div>
</template>

<script setup>
import { FileText } from 'lucide-vue-next'

defineProps({
  uploadedPdfs: Array,
  isUploading: Boolean,
  isSessionInitialized: {
    type: Boolean,
    default: false
  }
})

defineEmits(['file-upload', 'select-pdf'])
</script>

<style scoped>
.sidebar {
  background-color: #f3f4f6;
  padding: 1rem;
  flex-shrink: 0;
}

.upload-button {
  margin-bottom: 1rem;
}

.upload-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background-color: #3b82f6;
  color: white;
  border-radius: 0.375rem;
  cursor: pointer;
}

.upload-label.opacity-50 {
  opacity: 0.5;
  cursor: not-allowed;
}

.hidden-input {
  display: none;
}

.pdf-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.pdf-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px;
}

.pdf-item:hover {
  background-color: #e5e7eb;
}

.pdf-name {
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.icon {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
}
</style> 