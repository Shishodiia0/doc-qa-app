import React, { useState, useRef, useEffect } from 'react'
import { Send, Play } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import api from '../services/api'
import { Document } from '../store/docStore'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp?: number | null
  segmentEnd?: number | null
}

interface Props {
  document: Document
  onJumpTo: (ts: number) => void
}

export default function ChatPanel({ document, onJumpTo }: Props) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [streaming, setStreaming] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setMessages([])
  }, [document.id])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMsg: Message = { role: 'user', content: input }
    const history = messages.map((m) => ({ role: m.role, content: m.content }))
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)

    const assistantMsg: Message = { role: 'assistant', content: '' }
    setMessages((prev) => [...prev, assistantMsg])

    try {
      const response = await fetch('/api/v1/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('auth') ? JSON.parse(localStorage.getItem('auth')!).state.token : ''}`,
        },
        body: JSON.stringify({ document_id: document.id, message: input, history }),
      })

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      setStreaming(true)
      let fullContent = ''
      let timestamp: number | null = null
      let segmentEnd: number | null = null

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const text = decoder.decode(value)
        for (const line of text.split('\n')) {
          if (!line.startsWith('data: ')) continue
          const data = JSON.parse(line.slice(6))
          if (data.token) {
            fullContent += data.token
            setMessages((prev) => {
              const updated = [...prev]
              updated[updated.length - 1] = { ...updated[updated.length - 1], content: fullContent }
              return updated
            })
          }
          if (data.done) {
            timestamp = data.timestamp ?? null
            segmentEnd = data.segment_end ?? null
          }
        }
      }

      setMessages((prev) => {
        const updated = [...prev]
        updated[updated.length - 1] = { ...updated[updated.length - 1], timestamp, segmentEnd }
        return updated
      })
    } catch {
      setMessages((prev) => {
        const updated = [...prev]
        updated[updated.length - 1] = { ...updated[updated.length - 1], content: 'Error getting response.' }
        return updated
      })
    } finally {
      setLoading(false)
      setStreaming(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-sm text-gray-400 mt-8">
            <p>Ask anything about <strong>{document.filename}</strong></p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm ${
                msg.role === 'user'
                  ? 'bg-indigo-600 text-white rounded-br-sm'
                  : 'bg-gray-100 text-gray-800 rounded-bl-sm'
              }`}
            >
              {msg.role === 'assistant' ? (
                <ReactMarkdown>{msg.content || '▋'}</ReactMarkdown>
              ) : (
                msg.content
              )}
              {msg.role === 'assistant' && msg.timestamp != null && (
                <button
                  onClick={() => onJumpTo(msg.timestamp!)}
                  className="mt-2 flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800 font-medium"
                >
                  <Play size={12} />
                  Play at {Math.floor(msg.timestamp / 60)}:{String(Math.floor(msg.timestamp % 60)).padStart(2, '0')}
                </button>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={sendMessage} className="p-4 border-t border-gray-100 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question…"
          disabled={loading}
          className="flex-1 border border-gray-300 rounded-full px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="w-9 h-9 bg-indigo-600 text-white rounded-full flex items-center justify-center hover:bg-indigo-700 disabled:opacity-40 transition-colors"
        >
          <Send size={15} />
        </button>
      </form>
    </div>
  )
}
