import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import DocumentList from '../components/DocumentList'
import { useDocStore } from '../store/docStore'
import api from '../services/api'

vi.mock('../services/api')

const mockDocs = [
  { id: 'd1', filename: 'report.pdf', file_type: 'pdf', status: 'ready', created_at: '2024-01-01T00:00:00Z' },
  { id: 'd2', filename: 'lecture.mp3', file_type: 'audio', status: 'processing', created_at: '2024-01-02T00:00:00Z' },
  { id: 'd3', filename: 'demo.mp4', file_type: 'video', status: 'error', created_at: '2024-01-03T00:00:00Z' },
]

describe('DocumentList', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useDocStore.setState({ documents: [], selected: null })
    vi.mocked(api.get).mockResolvedValue({ data: mockDocs })
  })

  it('shows empty state when no documents', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] })
    render(<DocumentList />)
    await waitFor(() => expect(screen.getByText(/No documents yet/)).toBeInTheDocument())
  })

  it('renders documents after fetch', async () => {
    render(<DocumentList />)
    await waitFor(() => expect(screen.getByText('report.pdf')).toBeInTheDocument())
    expect(screen.getByText('lecture.mp3')).toBeInTheDocument()
    expect(screen.getByText('demo.mp4')).toBeInTheDocument()
  })

  it('selects a ready document on click', async () => {
    render(<DocumentList />)
    await waitFor(() => screen.getByText('report.pdf'))
    fireEvent.click(screen.getByText('report.pdf'))
    expect(useDocStore.getState().selected?.id).toBe('d1')
  })

  it('does not select a processing document', async () => {
    render(<DocumentList />)
    await waitFor(() => screen.getByText('lecture.mp3'))
    fireEvent.click(screen.getByText('lecture.mp3'))
    expect(useDocStore.getState().selected).toBeNull()
  })

  it('deletes a document on trash click', async () => {
    vi.mocked(api.delete).mockResolvedValue({})
    useDocStore.setState({ documents: mockDocs as any })
    render(<DocumentList />)
    await waitFor(() => screen.getByText('report.pdf'))
    const deleteButtons = screen.getAllByRole('button')
    fireEvent.click(deleteButtons[0])
    await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/documents/d1'))
  })

  it('deselects already selected document on second click', async () => {
    useDocStore.setState({ documents: mockDocs as any, selected: mockDocs[0] as any })
    render(<DocumentList />)
    await waitFor(() => screen.getByText('report.pdf'))
    fireEvent.click(screen.getByText('report.pdf'))
    expect(useDocStore.getState().selected).toBeNull()
  })
})
