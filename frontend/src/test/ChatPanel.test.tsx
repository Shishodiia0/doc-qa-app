import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import ChatPanel from '../components/ChatPanel'
import { Document } from '../store/docStore'

const mockDoc: Document = {
  id: 'doc-1',
  filename: 'test.pdf',
  file_type: 'pdf',
  status: 'ready',
  created_at: '2024-01-01T00:00:00Z',
}

const mockAudioDoc: Document = {
  ...mockDoc,
  file_type: 'audio',
  transcript_segments: [{ start: 5.0, end: 10.0, text: 'relevant content' }],
}

const mockOnJumpTo = vi.fn()

// Mock fetch for streaming
const mockFetch = vi.fn()
;(globalThis as any).fetch = mockFetch

function makeStreamResponse(events: string[]) {
  const encoder = new TextEncoder()
  const stream = new ReadableStream({
    start(controller) {
      for (const event of events) {
        controller.enqueue(encoder.encode(event))
      }
      controller.close()
    },
  })
  return { ok: true, body: stream }
}

describe('ChatPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.setItem('auth', JSON.stringify({ state: { token: 'test-token' } }))
  })

  it('renders empty state with document name', () => {
    render(<ChatPanel document={mockDoc} onJumpTo={mockOnJumpTo} />)
    expect(screen.getByText(/test.pdf/)).toBeInTheDocument()
  })

  it('renders input and send button', () => {
    render(<ChatPanel document={mockDoc} onJumpTo={mockOnJumpTo} />)
    expect(screen.getByPlaceholderText('Ask a question…')).toBeInTheDocument()
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('send button is disabled when input is empty', () => {
    render(<ChatPanel document={mockDoc} onJumpTo={mockOnJumpTo} />)
    const btn = screen.getByRole('button')
    expect(btn).toBeDisabled()
  })

  it('send button enables when input has text', () => {
    render(<ChatPanel document={mockDoc} onJumpTo={mockOnJumpTo} />)
    fireEvent.change(screen.getByPlaceholderText('Ask a question…'), { target: { value: 'hello' } })
    expect(screen.getByRole('button')).not.toBeDisabled()
  })

  it('sends message and shows streaming response', async () => {
    mockFetch.mockResolvedValueOnce(
      makeStreamResponse([
        'data: {"token": "Hello"}\n\n',
        'data: {"token": " world"}\n\n',
        'data: {"done": true, "timestamp": null}\n\n',
      ])
    )
    render(<ChatPanel document={mockDoc} onJumpTo={mockOnJumpTo} />)
    fireEvent.change(screen.getByPlaceholderText('Ask a question…'), { target: { value: 'What is this?' } })
    fireEvent.submit(screen.getByRole('form') || document.querySelector('form')!)
    await waitFor(() => expect(screen.getByText('What is this?')).toBeInTheDocument())
    await waitFor(() => expect(screen.getByText(/Hello world/)).toBeInTheDocument())
  })

  it('shows play button when timestamp is returned', async () => {
    mockFetch.mockResolvedValueOnce(
      makeStreamResponse([
        'data: {"token": "The answer is here"}\n\n',
        'data: {"done": true, "timestamp": 5.0, "segment_end": 10.0}\n\n',
      ])
    )
    render(<ChatPanel document={mockAudioDoc} onJumpTo={mockOnJumpTo} />)
    const input = screen.getByPlaceholderText('Ask a question…')
    fireEvent.change(input, { target: { value: 'Where is it?' } })
    fireEvent.submit(document.querySelector('form')!)
    await waitFor(() => expect(screen.getByText(/Play at/)).toBeInTheDocument())
  })

  it('calls onJumpTo when play button clicked', async () => {
    mockFetch.mockResolvedValueOnce(
      makeStreamResponse([
        'data: {"token": "answer"}\n\n',
        'data: {"done": true, "timestamp": 5.0}\n\n',
      ])
    )
    render(<ChatPanel document={mockAudioDoc} onJumpTo={mockOnJumpTo} />)
    fireEvent.change(screen.getByPlaceholderText('Ask a question…'), { target: { value: 'q' } })
    fireEvent.submit(document.querySelector('form')!)
    await waitFor(() => screen.getByText(/Play at/))
    fireEvent.click(screen.getByText(/Play at/))
    expect(mockOnJumpTo).toHaveBeenCalledWith(5.0)
  })

  it('shows error message on fetch failure', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'))
    render(<ChatPanel document={mockDoc} onJumpTo={mockOnJumpTo} />)
    fireEvent.change(screen.getByPlaceholderText('Ask a question…'), { target: { value: 'test' } })
    fireEvent.submit(document.querySelector('form')!)
    await waitFor(() => expect(screen.getByText(/Error getting response/)).toBeInTheDocument())
  })

  it('resets messages when document changes', () => {
    const { rerender } = render(<ChatPanel document={mockDoc} onJumpTo={mockOnJumpTo} />)
    rerender(<ChatPanel document={{ ...mockDoc, id: 'doc-2', filename: 'other.pdf' }} onJumpTo={mockOnJumpTo} />)
    expect(screen.getByText(/other.pdf/)).toBeInTheDocument()
  })
})
