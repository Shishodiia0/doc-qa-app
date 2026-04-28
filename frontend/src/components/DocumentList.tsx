import React, { useEffect } from 'react'
import { FileText, Music, Video, Trash2, RefreshCw, CheckCircle, Clock, AlertCircle } from 'lucide-react'
import api from '../services/api'
import { useDocStore, Document } from '../store/docStore'

const icons = { pdf: FileText, audio: Music, video: Video }

const statusIcon = {
  ready: <CheckCircle size={14} className="text-green-500" />,
  processing: <RefreshCw size={14} className="text-yellow-500 animate-spin" />,
  pending: <Clock size={14} className="text-gray-400" />,
  error: <AlertCircle size={14} className="text-red-500" />,
}

export default function DocumentList() {
  const { documents, selected, setDocuments, removeDocument, selectDocument, updateDocument } =
    useDocStore()

  useEffect(() => {
    api.get('/documents/').then(({ data }) => setDocuments(data)).catch(() => {})
  }, [])

  // Poll processing docs every 4 seconds
  useEffect(() => {
    const processing = documents.filter((d) => d.status === 'pending' || d.status === 'processing')
    if (!processing.length) return
    const timer = setInterval(async () => {
      for (const doc of processing) {
        try {
          const { data } = await api.get(`/documents/${doc.id}`)
          updateDocument(doc.id, data)
        } catch {}
      }
    }, 4000)
    return () => clearInterval(timer)
  }, [documents])

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    await api.delete(`/documents/${id}`)
    removeDocument(id)
  }

  if (!documents.length) {
    return <p className="text-center text-sm text-gray-400 py-8">No documents yet. Upload one above.</p>
  }

  return (
    <ul className="divide-y divide-gray-100">
      {documents.map((doc) => {
        const Icon = icons[doc.file_type] || FileText
        const isSelected = selected?.id === doc.id
        return (
          <li
            key={doc.id}
            onClick={() => doc.status === 'ready' && selectDocument(isSelected ? null : doc)}
            className={`flex items-center gap-3 px-4 py-3 cursor-pointer transition-colors ${
              isSelected ? 'bg-indigo-50' : 'hover:bg-gray-50'
            } ${doc.status !== 'ready' ? 'opacity-60 cursor-default' : ''}`}
          >
            <Icon size={18} className="text-indigo-500 shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-800 truncate">{doc.filename}</p>
              <p className="text-xs text-gray-400 capitalize">{doc.file_type}</p>
            </div>
            <div className="flex items-center gap-2">
              {statusIcon[doc.status]}
              <button
                onClick={(e) => handleDelete(e, doc.id)}
                className="text-gray-300 hover:text-red-500 transition-colors"
              >
                <Trash2 size={14} />
              </button>
            </div>
          </li>
        )
      })}
    </ul>
  )
}
