import axios from 'axios'

export const API_URL = import.meta.env.PROD 
  ? `${import.meta.env.VITE_API_GATEWAY_URL}/prod`  // Production API Gateway URL
  : 'http://localhost:8000/prod'                     // Local development

export const uploadPDF = async (file, sessionId) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('session_id', sessionId)
  
  try {
    const response = await axios.post(`${API_URL}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  } catch (error) {
    throw error
  }
}

export const sendQuery = async (query, sessionId, chatHistory) => {
  try {
    const response = await axios.post(`${API_URL}/query`, {
      query: query,
      session_id: sessionId,
      chat_history: chatHistory.map(msg => ({
        role: msg.type === 'user' ? 'user' : 'assistant', 
        content: msg.content
      }))
    })
    return response.data
  } catch (error) {
    throw error
  }
}
