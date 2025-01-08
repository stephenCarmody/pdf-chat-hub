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

export const sendQuery = async (query, sessionId, docId, chatHistory = []) => {
  const payload = {
    query: query,
    session_id: sessionId,
    doc_id: docId,
    chat_history: (chatHistory || []).map(msg => ({
      role: msg.type || 'user',
      content: msg.content
    })).filter(msg => msg.content && msg.role)
  }

  console.log('Sending payload:', JSON.stringify(payload, null, 2))

  try {
    const response = await axios.post(`${API_URL}/query`, payload)
    return response.data
  } catch (error) {
    console.error('Error details:', {
      status: error.response?.status,
      data: error.response?.data,
      message: error.message,
      sentPayload: payload
    })
    throw error
  }
}
