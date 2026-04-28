import React, { useRef, useState, useEffect } from 'react'
import { Play, Pause } from 'lucide-react'
import { TranscriptSegment } from '../store/docStore'

interface Props {
  docId: string
  fileType: 'audio' | 'video'
  segments?: TranscriptSegment[]
  jumpTo?: number | null
}

export default function MediaPlayer({ docId, fileType, segments, jumpTo }: Props) {
  const mediaRef = useRef<HTMLVideoElement & HTMLAudioElement>(null)
  const [playing, setPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const src = `/api/v1/documents/${docId}/stream`

  useEffect(() => {
    if (jumpTo != null && mediaRef.current) {
      mediaRef.current.currentTime = jumpTo
      mediaRef.current.play()
      setPlaying(true)
    }
  }, [jumpTo])

  const togglePlay = () => {
    if (!mediaRef.current) return
    if (playing) {
      mediaRef.current.pause()
    } else {
      mediaRef.current.play()
    }
    setPlaying(!playing)
  }

  const jumpToSegment = (start: number) => {
    if (!mediaRef.current) return
    mediaRef.current.currentTime = start
    mediaRef.current.play()
    setPlaying(true)
  }

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60)
    const sec = Math.floor(s % 60)
    return `${m}:${sec.toString().padStart(2, '0')}`
  }

  return (
    <div className="space-y-3">
      {fileType === 'video' ? (
        <video
          ref={mediaRef}
          src={src}
          className="w-full rounded-lg max-h-48 bg-black"
          onTimeUpdate={() => setCurrentTime(mediaRef.current?.currentTime || 0)}
          onPlay={() => setPlaying(true)}
          onPause={() => setPlaying(false)}
          controls
        />
      ) : (
        <div className="bg-gray-100 rounded-lg p-4 flex items-center gap-3">
          <button
            onClick={togglePlay}
            className="w-10 h-10 bg-indigo-600 text-white rounded-full flex items-center justify-center hover:bg-indigo-700 transition-colors"
          >
            {playing ? <Pause size={16} /> : <Play size={16} />}
          </button>
          <audio
            ref={mediaRef}
            src={src}
            onTimeUpdate={() => setCurrentTime(mediaRef.current?.currentTime || 0)}
            onPlay={() => setPlaying(true)}
            onPause={() => setPlaying(false)}
          />
          <span className="text-sm text-gray-600 font-mono">{formatTime(currentTime)}</span>
        </div>
      )}

      {segments && segments.length > 0 && (
        <div className="max-h-40 overflow-y-auto space-y-1">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide px-1">Transcript</p>
          {segments.map((seg, i) => (
            <button
              key={i}
              onClick={() => jumpToSegment(seg.start)}
              className={`w-full text-left px-3 py-1.5 rounded-lg text-xs transition-colors flex gap-2 ${
                currentTime >= seg.start && currentTime < seg.end
                  ? 'bg-indigo-100 text-indigo-800'
                  : 'hover:bg-gray-100 text-gray-700'
              }`}
            >
              <span className="font-mono text-gray-400 shrink-0">{formatTime(seg.start)}</span>
              <span>{seg.text}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
