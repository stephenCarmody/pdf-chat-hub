import { describe, it, expect, vi } from 'vitest'
import { sendQuery } from '@/services/api'
import axios from 'axios'

vi.mock('axios')

describe('api', () => {
  describe('sendQuery', () => {
    it('sends query with correct format', async () => {
      // Arrange
      const mockResponse = { data: { message: 'Success' } }
      axios.post.mockResolvedValue(mockResponse)

      const query = 'test query'
      const sessionId = 'test-session'
      const docId = 'test-doc'

      // Act
      const result = await sendQuery(query, sessionId, docId)

      // Assert
      expect(axios.post).toHaveBeenCalledWith(expect.any(String), {
        query,
        session_id: sessionId,
        doc_id: docId
      })
      expect(result).toEqual(mockResponse.data)
    })

    it('handles errors correctly', async () => {
      // Arrange
      const mockError = new Error('API Error')
      axios.post.mockRejectedValue(mockError)

      const query = 'test query'
      const sessionId = 'test-session'
      const docId = 'test-doc'

      // Act & Assert
      await expect(sendQuery(query, sessionId, docId)).rejects.toThrow('API Error')
    })
  })
})
