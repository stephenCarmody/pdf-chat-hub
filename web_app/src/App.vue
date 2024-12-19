<template>
  <div class="app-container">
    <!-- Left Sidebar -->
    <div class="sidebar" :style="{ width: '250px' }">
      <div class="upload-button">
        <label class="upload-label" :class="{ 'opacity-50 cursor-not-allowed': isUploading }">
          <FileText class="icon" />
          <span>Upload PDF</span>
          <input 
            type="file" 
            accept=".pdf" 
            class="hidden-input" 
            @change="handleFileUpload"
            :disabled="isUploading"
          >
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
          <span class="pdf-name">{{ pdf.name }}</span>
        </div>
      </div>
    </div>

    <!-- Middle PDF Viewer -->
    <div 
      class="pdf-viewer" 
      ref="pdfContainerRef"
      :style="{ width: `calc(100% - 550px + ${rightPaneWidth}px)` }"
    >
      <div v-if="isUploading" class="upload-loading">
        <svg class="animate-spin spinner" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
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

    <!-- Resizer -->
    <div 
      class="resizer"
      @mousedown="startResize"
      @dblclick="resetWidth"
    ></div>

    <!-- Right Chat Panel -->
    <div class="chat-panel" :style="{ width: `${rightPaneWidth}px` }">
      <div v-if="!selectedPdf" class="chat-placeholder">
        Select a PDF to start chatting
      </div>
      <div v-else class="chat-interface">
        <div class="messages" ref="chatContainerRef">
          <div 
            v-for="(message, index) in messages" 
            :key="index"
            :class="['message', message.type]"
          >
            <div 
              class="message-content"
              v-html="formatMessage(message.content)"
            ></div>
          </div>
          <div v-if="isLoading" class="message assistant loading">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
        <div class="input-area">
          <input
            v-model="newMessage"
            @keyup.enter="sendMessage"
            placeholder="Ask a question about the PDF..."
            :disabled="!selectedPdf"
          />
          <button @click="sendMessage" :disabled="!selectedPdf">Send</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { FileText } from 'lucide-vue-next'
import VuePdfEmbed from 'vue-pdf-embed'
import { uploadPDF, sendQuery } from '@/services/api'
import axios from 'axios'
import { API_URL } from '@/services/api'

const uploadedPdfs = ref([])
const selectedPdf = ref(null)
const rightPaneWidth = ref(300) // Default width
const isResizing = ref(false)
const startX = ref(0)
const startWidth = ref(0)
const pdfContainerRef = ref(null)
const messages = ref([])
const newMessage = ref('')
const chatContainerRef = ref(null)
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

onMounted(async () => {
  await getSessionId()
})

const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (file && file.type === 'application/pdf') {
    if (!sessionId.value) {
      console.error('Session ID is not available.')
      messages.value.push({
        type: 'error',
        content: 'Session ID is not available. Please try again later.'
      })
      return
    }
    isUploading.value = true // Start loading
    try {
      console.log('Uploading PDF with session ID:', sessionId.value)
      const response = await uploadPDF(file, sessionId.value) // Pass sessionId.value
      const newPdf = {
        id: Date.now(),
        name: file.name,
        file: file,
        url: URL.createObjectURL(file)
      }
      uploadedPdfs.value.push(newPdf)
      selectPdf(newPdf)
      console.log('Upload successful:', response.message)
    } catch (error) {
      console.error('Upload failed:', error)
    } finally {
      isUploading.value = false // Stop loading
    }
  }
}

const selectPdf = (pdf) => {
  selectedPdf.value = pdf
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

const formatChatHistory = (messages) => {
  return messages
    .filter(msg => msg.type === 'user' || msg.type === 'assistant')
    .map((msg, index, array) => {
      if (msg.type === 'user') {
        return {
          content: msg.content,
          response: array[index + 1]?.content || ''
        }
      }
      return null
    })
    .filter(Boolean)
}

const sendMessage = async () => {
  if (!newMessage.value.trim() || !selectedPdf.value) return
  
  const userMessage = {
    type: 'user',
    content: newMessage.value
  }
  messages.value.push(userMessage)
  newMessage.value = ''
  isLoading.value = true
  
  try {
    const chatHistory = formatChatHistory(messages.value)
    const response = await sendQuery(userMessage.content, sessionId.value, chatHistory)
    
    messages.value.push({
      type: 'assistant',
      content: response.message
    })
  } catch (error) {
    console.error('Query failed:', error)
    messages.value.push({
      type: 'error',
      content: 'Failed to get response. Please try again.'
    })
  } finally {
    isLoading.value = false
  }
}

// Add this function to format messages
const formatMessage = (content) => {
  // Replace ### with h3 headers
  content = content.replace(/###\s(.*)/g, '<h3>$1</h3>')
  
  // Replace ** ** with bold text
  content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  
  // Replace numbered lists (1., 2., etc)
  content = content.replace(/(\d+\.\s.*?)(?=(?:\d+\.|\n|$))/g, '<div class="list-item">$1</div>')
  
  // Convert line breaks to <br>
  content = content.replace(/\n/g, '<br>')
  
  return content
}

onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', stopResize)
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  width: 100%;
  overflow: hidden;
}

.app-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
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

.upload-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.spinner {
  width: 40px; /* You might want to make it larger in this context */
  height: 40px;
}

.pdf-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.pdf-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  border-radius: 0.375rem;
  cursor: pointer;
}

.pdf-item:hover {
  background-color: #e5e7eb;
}

.pdf-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pdf-viewer {
  flex: 1;
  background-color: #ffffff;
  padding: 1rem;
  position: relative;
  overflow: auto;
}

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

.pdf-placeholder {
  height: 100%;
  border: 2px dashed #ccc;
  border-radius: 0.375rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon {
  width: 20px;
  height: 20px;
}

.pdf-view {
  width: 100%;
  height: 100%;
  overflow: auto;
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
  0%, 80%, 100% { 
    transform: scale(0);
  } 
  40% { 
    transform: scale(1.0);
  }
}

/* Spinner Styles */
.animate-spin {
  animation: spin 1s linear infinite;
}

.spinner {
  width: 16px; /* Smaller size */
  height: 16px;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* Add some spacing between messages */
.message + .message {
  margin-top: 1rem;
}
</style>
