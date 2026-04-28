import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import AuthPage from '../components/AuthPage'
import api from '../services/api'

vi.mock('../services/api')
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

const renderAuth = () => render(<MemoryRouter><AuthPage /></MemoryRouter>)

describe('AuthPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders login form by default', () => {
    renderAuth()
    expect(screen.getByPlaceholderText('Username')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Password')).toBeInTheDocument()
    expect(screen.getByText('Sign In')).toBeInTheDocument()
  })

  it('switches to register mode', () => {
    renderAuth()
    fireEvent.click(screen.getByText('Register'))
    expect(screen.getByText('Create Account')).toBeInTheDocument()
  })

  it('shows error on failed login', async () => {
    vi.mocked(api.post).mockRejectedValueOnce({
      response: { data: { detail: 'Invalid credentials' } },
    })
    renderAuth()
    fireEvent.change(screen.getByPlaceholderText('Username'), { target: { value: 'user' } })
    fireEvent.change(screen.getByPlaceholderText('Password'), { target: { value: 'wrong' } })
    fireEvent.click(screen.getByText('Sign In'))
    await waitFor(() => expect(screen.getByText('Invalid credentials')).toBeInTheDocument())
  })

  it('navigates on successful login', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ data: { access_token: 'tok123', token_type: 'bearer' } })
    renderAuth()
    fireEvent.change(screen.getByPlaceholderText('Username'), { target: { value: 'alice' } })
    fireEvent.change(screen.getByPlaceholderText('Password'), { target: { value: 'secret' } })
    fireEvent.click(screen.getByText('Sign In'))
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/'))
  })

  it('shows success message after registration', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ data: { id: 'u1', username: 'alice' } })
    renderAuth()
    fireEvent.click(screen.getByText('Register'))
    fireEvent.change(screen.getByPlaceholderText('Username'), { target: { value: 'alice' } })
    fireEvent.change(screen.getByPlaceholderText('Password'), { target: { value: 'secret' } })
    fireEvent.click(screen.getByText('Create Account'))
    await waitFor(() => expect(screen.getByText(/Registered/)).toBeInTheDocument())
  })

  it('shows generic error when no detail', async () => {
    vi.mocked(api.post).mockRejectedValueOnce(new Error('Network error'))
    renderAuth()
    fireEvent.change(screen.getByPlaceholderText('Username'), { target: { value: 'u' } })
    fireEvent.change(screen.getByPlaceholderText('Password'), { target: { value: 'p' } })
    fireEvent.click(screen.getByText('Sign In'))
    await waitFor(() => expect(screen.getByText('Something went wrong')).toBeInTheDocument())
  })
})
