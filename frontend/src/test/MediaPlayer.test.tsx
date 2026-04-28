import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import MediaPlayer from '../components/MediaPlayer'

const segments = [
  { start: 0, end: 5, text: 'Introduction to the topic' },
  { start: 5, end: 10, text: 'Main content here' },
  { start: 10, end: 15, text: 'Conclusion and summary' },
]

describe('MediaPlayer', () => {
  it('renders audio player for audio type', () => {
    render(<MediaPlayer docId="d1" fileType="audio" />)
    expect(document.querySelector('audio')).toBeInTheDocument()
    expect(document.querySelector('video')).not.toBeInTheDocument()
  })

  it('renders video player for video type', () => {
    render(<MediaPlayer docId="d1" fileType="video" />)
    expect(document.querySelector('video')).toBeInTheDocument()
  })

  it('renders transcript segments', () => {
    render(<MediaPlayer docId="d1" fileType="audio" segments={segments} />)
    expect(screen.getByText('Introduction to the topic')).toBeInTheDocument()
    expect(screen.getByText('Main content here')).toBeInTheDocument()
    expect(screen.getByText('Conclusion and summary')).toBeInTheDocument()
  })

  it('shows transcript label when segments present', () => {
    render(<MediaPlayer docId="d1" fileType="audio" segments={segments} />)
    expect(screen.getByText('Transcript')).toBeInTheDocument()
  })

  it('does not show transcript when no segments', () => {
    render(<MediaPlayer docId="d1" fileType="audio" segments={[]} />)
    expect(screen.queryByText('Transcript')).not.toBeInTheDocument()
  })

  it('shows formatted timestamps in transcript', () => {
    render(<MediaPlayer docId="d1" fileType="audio" segments={segments} />)
    expect(screen.getByText('0:00')).toBeInTheDocument()
    expect(screen.getByText('0:05')).toBeInTheDocument()
  })

  it('renders play button for audio', () => {
    render(<MediaPlayer docId="d1" fileType="audio" />)
    const playBtn = document.querySelector('button')
    expect(playBtn).toBeInTheDocument()
  })

  it('uses correct src for media', () => {
    render(<MediaPlayer docId="doc-abc" fileType="audio" />)
    const audio = document.querySelector('audio')
    expect(audio?.src).toContain('/api/v1/documents/doc-abc/stream')
  })

  it('jumps to timestamp when jumpTo changes', () => {
    const { rerender } = render(<MediaPlayer docId="d1" fileType="audio" jumpTo={null} />)
    const audio = document.querySelector('audio') as HTMLAudioElement
    const playSpy = vi.spyOn(audio, 'play').mockResolvedValue(undefined)
    rerender(<MediaPlayer docId="d1" fileType="audio" jumpTo={30} />)
    expect(playSpy).toHaveBeenCalled()
  })
})
