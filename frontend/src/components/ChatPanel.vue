<template>
  <div class="chat-panel" :style="{ width: `${rightPaneWidth}px` }">
    <div v-if="!selectedPdf" class="chat-placeholder">
      Select a PDF to start chatting
    </div>
    <div v-else class="chat-interface">
        <div class="messages" ref="chatContainerRef">
          <div
            v-for="(message, index) in messages[selectedPdf?.id] || []"
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
            :value="modelValue"
            @input="$emit('update:modelValue', $event.target.value)"
            @keyup.enter="$emit('send-message')"
            placeholder="Ask a question about the PDF..."
            :disabled="!selectedPdf"
          />
          <button @click="$emit('send-message')" :disabled="!selectedPdf">Send</button>
        </div>
      </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  selectedPdf: Object,
  messages: Object,
  isLoading: Boolean,
  rightPaneWidth: Number,
  modelValue: String
})

defineEmits(['update:modelValue', 'send-message'])

const formatMessage = (content) => {
  if (!content) return ''
  
  // Replace ### with h3 headers
  content = content.replace(/###\s(.*)/g, '<h3>$1</h3>')

  // Replace ** ** with bold text
  content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')

  // Replace numbered lists (1., 2., etc)
  content = content.replace(
    /(\d+\.\s.*?)(?=(?:\d+\.|\n|$))/g,
    '<div class="list-item">$1</div>'
  )

  // Convert line breaks to <br>
  content = content.replace(/\n/g, '<br>')

  return content
}

const chatContainerRef = ref(null)
</script>

<style scoped>
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
    transform: scale(1);
  }
}

/* Add some spacing between messages */
.message + .message {
  margin-top: 1rem;
}
</style> 