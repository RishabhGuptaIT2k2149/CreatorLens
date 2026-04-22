import { useState, useRef, useEffect } from 'react'
import client from '../api/client'

export default function ChatPanel({ channelId }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function sendMessage(e) {
    e.preventDefault()
    const question = input.trim()
    if (!question || loading) return

    const userMsg = { role: 'user', text: question }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const { data } = await client.post(`/channel/${channelId}/chat`, {
        question,
        history: [],
      })
      setMessages(prev => [
        ...prev,
        { role: 'assistant', text: data.answer, sources: data.sources },
      ])
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          text: err.response?.data?.detail || 'Something went wrong. Please try again.',
          error: true,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-[70vh]">
      {/* Message thread */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-2 mb-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-gray-600 text-sm text-center space-y-2">
            <p className="text-2xl">💬</p>
            <p>Ask anything about this channel's content.</p>
            <p className="text-xs">e.g. "What phones has Jerry reviewed?" or "Does he ever recommend screen protectors?"</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-2xl rounded-2xl px-4 py-3 text-sm ${
                msg.role === 'user'
                  ? 'bg-violet-600 text-white'
                  : msg.error
                  ? 'bg-red-950 border border-red-800 text-red-300'
                  : 'bg-gray-900 border border-gray-800 text-gray-200'
              }`}
            >
              <p className="leading-relaxed whitespace-pre-wrap">{msg.text}</p>

              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-700 flex flex-wrap gap-2">
                  {msg.sources.map((s, j) => (
                    <span
                      key={j}
                      className="text-xs text-gray-500 bg-gray-800 rounded px-2 py-0.5"
                    >
                      {s.video_id} · chunk {s.chunk_index}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-900 border border-gray-800 rounded-2xl px-4 py-3">
              <div className="flex gap-1 items-center h-4">
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:0ms]" />
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:150ms]" />
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:300ms]" />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={sendMessage} className="flex gap-3">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Ask about this channel's content…"
          className="flex-1 bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent transition text-sm"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="bg-violet-600 hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold px-5 py-3 rounded-xl transition-colors text-sm"
        >
          Send
        </button>
      </form>
    </div>
  )
}
