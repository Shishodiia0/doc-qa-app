import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import FileUpload from '../components/FileUpload'
import { useDocStore } from '../store/docStore'
import api from '../services/api'

vi.mock('../services/api')

describe('FileUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useDocStore.setState({ documents: [] })
  })

  it('renders upload area', () => {
    render(<FileUpload />)
    expect(screen.getByText(/Drag & drop or click to upload/)).toBeInTheDocument()
    expect(screen.getByText('PDF')).toBeInTheDocument()
    expect(screen.getByText('Audio')).toBeInTheDocument()
    expect(screen.getByText('Video')).toBeInTheDocument()
  })

  it('shows upload progress on success', async () => {
    const mockDoc = { id: 'd1', filename: 'test.pdf', file_type: 'pdf', status: 'pending', created_at: '2024-01-01' }
    vi.mocked(api.post).mockResolvedValueOnce({ data: mockDoc })

    render(<FileUpload />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })
    Object.defineProperty(input, 'files', { value: [file] })
    fireEvent.change(input)

    await waitFor(() => expect(screen.getByText(/test.pdf uploaded/)).toBeInTheDocument())
    expect(useDocStore.getState().documents).toHaveLength(1)
  })

  it('shows error on upload failure', async () => {
    vi.mocked(api.post).mockRejectedValueOnce({ response: { data: { detail: 'File too large' } } })

    render(<FileUpload />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File(['x'], 'big.pdf', { type: 'application/pdf' })
    Object.defineProperty(input, 'files', { value: [file] })
    fireEvent.change(input)

    await waitFor(() => expect(screen.getByText(/File too large/)).toBeInTheDocument())
  })
})
