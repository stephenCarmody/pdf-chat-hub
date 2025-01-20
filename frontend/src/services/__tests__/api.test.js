import { describe, it, expect, vi } from 'vitest'
import { sendQuery } from '@/services/api'
import axios from 'axios'

vi.mock('axios')

describe('api', () => {
  describe('sendQuery', () => {
    it('formats chat history correctly', async () => {
      // Arrange
      const mockResponse = { data: { message: 'Success' } }
      axios.post.mockResolvedValue(mockResponse)

      const query = 'test query'
      const sessionId = 'test-session'
      const docId = 'test-doc'
      const chatHistory = [
        { type: 'user', content: 'Hello' },
        { type: 'assistant', content: 'Hi there' }
      ]

      // Act
      const result = await sendQuery(query, sessionId, docId, chatHistory)

      // Assert
      expect(axios.post).toHaveBeenCalledWith(expect.any(String), {
        query,
        session_id: sessionId,
        doc_id: docId,
        chat_history: [
          { role: 'user', content: 'Hello' },
          { role: 'assistant', content: 'Hi there' }
        ]
      })
      expect(result).toEqual(mockResponse.data)
    })
  })
})
