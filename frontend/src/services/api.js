import axios from 'axios'

export const API_URL = `${import.meta.env.VITE_API_GATEWAY_URL}/prod`

export const uploadPDF = async (file, sessionId) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('session_id', sessionId)

  const response = await axios.post(`${API_URL}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  return response.data
}

export const sendQuery = async (query, sessionId, docId) => {
  const payload = {
    query: query,
    session_id: sessionId,
    doc_id: docId
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
