import axios from 'axios'

export const API_URL = import.meta.env.PROD 
  ? `${import.meta.env.VITE_API_GATEWAY_URL}/prod`
  : 'http://localhost:8000'

export const uploadPDF = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  
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
