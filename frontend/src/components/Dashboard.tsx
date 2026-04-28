import React, { useState } from 'react'
import { LogOut, FileText } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { useDocStore } from '../store/docStore'
import FileUpload from './FileUpload'
import DocumentList from './DocumentList'
import ChatPanel from './ChatPanel'
import MediaPlayer from './MediaPlayer'

export default function Dashboard() {
  const logout = useAuthStore((s) => s.logout)
  const selected = useDocStore((s) => s.selected)
  const [jumpTo, setJumpTo] = useState<number | null>(null)

  const handleJumpTo = (ts: number) => {
    setJumpTo(null)
    setTimeout(() => setJumpTo(ts), 50)
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="text-indigo-600" size={22} />
          <span className="font-bold text-gray-800">Doc Q&amp;A</span>
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-red-500 transition-colors"
        >
          <LogOut size={16} /> Sign out
        </button>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-72 bg-white border-r border-gray-200 flex flex-col overflow-hidden">
          <FileUpload />
          <div className="flex-1 overflow-y-auto">
            <DocumentList />
          </div>
        </aside>

        {/* Main */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {selected ? (
            <div className="flex flex-1 overflow-hidden">
              {/* Chat */}
              <div className="flex-1 flex flex-col overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-100 bg-white">
                  <p className="text-sm font-semibold text-gray-700 truncate">{selected.filename}</p>
                  {selected.summary && (
                    <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{selected.summary}</p>
                  )}
                </div>
                <ChatPanel document={selected} onJumpTo={handleJumpTo} />
              </div>

              {/* Media panel (audio/video only) */}
              {(selected.file_type === 'audio' || selected.file_type === 'video') && (
                <div className="w-80 border-l border-gray-200 bg-white p-4 overflow-y-auto">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Media</p>
                  <MediaPlayer
                    docId={selected.id}
                    fileType={selected.file_type}
                    segments={selected.transcript_segments}
                    jumpTo={jumpTo}
                  />
                </div>
              )}
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-400">
              <div className="text-center">
                <FileText size={48} className="mx-auto mb-3 opacity-30" />
                <p className="text-sm">Select a document to start chatting</p>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
