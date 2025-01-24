<template>
  <div class="app-container">
    <!-- Left Sidebar -->
    <PdfSidebar
      :uploaded-pdfs="uploadedPdfs"
      :is-uploading="isUploading"
      :is-session-initialized="!!sessionId"
      @file-upload="handleFileUpload"
      @select-pdf="selectPdf"
    />

    <!-- Middle PDF Viewer -->
    <PdfViewer
      :selected-pdf="selectedPdf"
      :is-uploading="isUploading"
      :right-pane-width="rightPaneWidth"
    />

    <!-- Resizer -->
    <div class="resizer" @mousedown="startResize" @dblclick="resetWidth"></div>

    <!-- Right Chat Panel -->
    <ChatPanel
      :selected-pdf="selectedPdf"
      :messages="messages"
      :is-loading="isLoading"
      :right-pane-width="rightPaneWidth"
      v-model="newMessage"
      @send-message="sendMessage"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { uploadPDF, sendQuery } from '@/services/api'
import axios from 'axios'
import { API_URL } from '@/services/api'
import PdfSidebar from '@/components/PdfSidebar.vue'
import ChatPanel from '@/components/ChatPanel.vue'
import PdfViewer from '@/components/PdfViewer.vue'

const uploadedPdfs = ref([])
const selectedPdf = ref(null)
const rightPaneWidth = ref(300) // Default width
const isResizing = ref(false)
const startX = ref(0)
const startWidth = ref(0)
const messages = ref({}) // {docId: [...messages]}
const newMessage = ref('')
const isLoading = ref(false)
const sessionId = ref(null)
const isUploading = ref(false)

const getSessionId = async () => {
  try {
    const response = await axios.get(`${API_URL}/session`)
    sessionId.value = response.data.session
    console.log('Session ID:', sessionId.value)
  } catch (error) {
    console.error('Failed to get session ID:', error)
    messages.value.push({
      type: 'error',
      content: 'Failed to initialize session. Please refresh and try again.'
    })
  }
}

const wakeUpBackend = async () => {
  try {
    await axios.get(`${API_URL}/wake-up`)
    console.log('Backend warmed up successfully')
  } catch (error) {
    console.error('Failed to wake up backend:', error)
  }
}

onMounted(async () => {
  await wakeUpBackend()
  await getSessionId()
})

const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (file && file.type === 'application/pdf') {
    isUploading.value = true
    try {
      const response = await uploadPDF(file, sessionId.value)
      const newPdf = {
        id: response.doc_id,
        name: file.name,
        file: file,
        url: URL.createObjectURL(file)
      }
      uploadedPdfs.value.push(newPdf)
      messages.value[newPdf.id] = [] // Initialize empty chat history
      selectPdf(newPdf)
    } catch (error) {
      console.error('Upload failed:', error)
    } finally {
      isUploading.value = false
    }
  }
}

const selectPdf = (pdf) => {
  selectedPdf.value = pdf
  if (!messages.value[pdf.id]) {
    messages.value[pdf.id] = []
  }
}

// Resizing functionality
const startResize = (event) => {
  isResizing.value = true
  startX.value = event.clientX
  startWidth.value = rightPaneWidth.value
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', stopResize)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

const handleMouseMove = (event) => {
  if (!isResizing.value) return

  const diff = startX.value - event.clientX
  const newWidth = Math.min(Math.max(startWidth.value + diff, 200), 600)
  rightPaneWidth.value = newWidth
}

const stopResize = () => {
  isResizing.value = false
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', stopResize)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

const resetWidth = () => {
  rightPaneWidth.value = 300 // Reset to default width
}

const sendMessage = async () => {
  if (!newMessage.value.trim() || !selectedPdf.value) return

  const userMessage = {
    type: 'user',
    content: newMessage.value
  }

  const currentDocId = selectedPdf.value.id
  messages.value[currentDocId].push(userMessage)
  newMessage.value = ''
  isLoading.value = true

  try {
    const response = await sendQuery(
      userMessage.content,
      sessionId.value,
      currentDocId
    )

    messages.value[currentDocId].push({
      type: 'assistant',
      content: response.message
    })
  } catch (error) {
    console.error('Error in chat:', error)
    messages.value[currentDocId].push({
      type: 'error',
      content: `Error: ${error.message || 'Failed to get response. Please try again.'}`
    })
  } finally {
    isLoading.value = false
  }
}

onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', stopResize)
})
</script>

<style>
/* Global styles */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body {
  height: 100%;
  width: 100%;
  overflow: hidden;
}

.app-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* Resizer styles */
.resizer {
  width: 4px;
  cursor: col-resize;
  background-color: #e5e7eb;
  transition: background-color 0.2s;
  margin: 0 -2px;
  z-index: 10;
}

.resizer:hover {
  background-color: #3b82f6;
}

/* PDF viewer styles */
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

/* Loading spinner styles */
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

.chat-panel {
  background-color: #f3f4f6;
  padding: 1rem;
  height: 100%;
  min-width: 300px;
  max-width: 600px;
  overflow: hidden;
}

.chat-placeholder {
  height: 100%;
  border: 2px dashed #ccc;
  border-radius: 0.375rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
}

.chat-interface {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.message {
  padding: 0.75rem;
  border-radius: 0.5rem;
  max-width: 80%;
}

.message.user {
  background-color: #3b82f6;
  color: white;
  align-self: flex-end;
}

.message.assistant {
  background-color: #e5e7eb;
  align-self: flex-start;
}

.message.error {
  background-color: #ef4444;
  color: white;
  align-self: center;
}

.input-area {
  padding: 1rem;
  border-top: 1px solid #e5e7eb;
  display: flex;
  gap: 0.5rem;
  min-height: 74px;
}

.input-area input {
  flex: 1;
  min-width: 150px;
  padding: 0.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
}

.input-area button {
  padding: 0.5rem 1rem;
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  white-space: nowrap;
  min-width: 70px;
  flex-shrink: 0;
}

.input-area button:disabled {
  background-color: #9ca3af;
  cursor: not-allowed;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 8px;
  align-items: center;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background-color: #3b82f6;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%,
  80%,
  100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.message + .message {
  margin-top: 1rem;
}
</style>
