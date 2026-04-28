import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Dashboard from '../components/Dashboard'
import { useAuthStore } from '../store/authStore'
import { useDocStore } from '../store/docStore'
import api from '../services/api'

vi.mock('../services/api')

const renderDashboard = () =>
  render(<MemoryRouter><Dashboard /></MemoryRouter>)

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useDocStore.setState({ documents: [], selected: null })
    vi.mocked(api.get).mockResolvedValue({ data: [] })
  })

  it('renders header with app name', () => {
    renderDashboard()
    expect(screen.getByText('Doc Q&A')).toBeInTheDocument()
  })

  it('renders sign out button', () => {
    renderDashboard()
    expect(screen.getByText('Sign out')).toBeInTheDocument()
  })

  it('calls logout on sign out click', () => {
    const logoutSpy = vi.fn()
    useAuthStore.setState({ token: 'tok', logout: logoutSpy } as any)
    renderDashboard()
    fireEvent.click(screen.getByText('Sign out'))
    expect(logoutSpy).toHaveBeenCalled()
  })

  it('shows empty state when no document selected', () => {
    renderDashboard()
    expect(screen.getByText(/Select a document to start chatting/)).toBeInTheDocument()
  })

  it('shows chat panel when pdf document selected', () => {
    useDocStore.setState({
      documents: [],
      selected: {
        id: 'd1', filename: 'report.pdf', file_type: 'pdf',
        status: 'ready', created_at: '2024-01-01T00:00:00Z',
        summary: 'A great report about things.',
      },
    })
    renderDashboard()
    expect(screen.getByText('report.pdf')).toBeInTheDocument()
    expect(screen.getByText('A great report about things.')).toBeInTheDocument()
  })

  it('shows media panel for audio document', () => {
    useDocStore.setState({
      documents: [],
      selected: {
        id: 'd2', filename: 'lecture.mp3', file_type: 'audio',
        status: 'ready', created_at: '2024-01-01T00:00:00Z',
      },
    })
    renderDashboard()
    expect(screen.getByText('Media')).toBeInTheDocument()
  })

  it('shows media panel for video document', () => {
    useDocStore.setState({
      documents: [],
      selected: {
        id: 'd3', filename: 'demo.mp4', file_type: 'video',
        status: 'ready', created_at: '2024-01-01T00:00:00Z',
      },
    })
    renderDashboard()
    expect(screen.getByText('Media')).toBeInTheDocument()
  })

  it('does not show media panel for pdf', () => {
    useDocStore.setState({
      documents: [],
      selected: {
        id: 'd1', filename: 'doc.pdf', file_type: 'pdf',
        status: 'ready', created_at: '2024-01-01T00:00:00Z',
      },
    })
    renderDashboard()
    expect(screen.queryByText('Media')).not.toBeInTheDocument()
  })
})
