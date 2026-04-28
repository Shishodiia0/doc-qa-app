import React, { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, Music, Video } from 'lucide-react'
import api from '../services/api'
import { useDocStore } from '../store/docStore'

const ACCEPT = {
  'application/pdf': ['.pdf'],
  'audio/*': ['.mp3', '.wav', '.m4a'],
  'video/*': ['.mp4', '.mov', '.avi', '.mkv'],
}

export default function FileUpload() {
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState('')
  const addDocument = useDocStore((s) => s.addDocument)

  const onDrop = useCallback(async (files: File[]) => {
    if (!files.length) return
    setUploading(true)
    setProgress('')
    for (const file of files) {
      try {
        setProgress(`Uploading ${file.name}…`)
        const form = new FormData()
        form.append('file', file)
        const { data } = await api.post('/documents/upload', form)
        addDocument(data)
        setProgress(`✓ ${file.name} uploaded — processing in background`)
      } catch (err: any) {
        setProgress(`✗ ${file.name}: ${err.response?.data?.detail || 'Upload failed'}`)
      }
    }
    setUploading(false)
  }, [addDocument])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPT,
    maxFiles: 5,
    disabled: uploading,
  })

  return (
    <div className="p-4">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
          isDragActive ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300 hover:border-indigo-400 hover:bg-gray-50'
        } ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto mb-3 text-gray-400" size={32} />
        <p className="text-sm font-medium text-gray-700">
          {isDragActive ? 'Drop files here' : 'Drag & drop or click to upload'}
        </p>
        <div className="flex justify-center gap-4 mt-3 text-xs text-gray-500">
          <span className="flex items-center gap-1"><FileText size={12} /> PDF</span>
          <span className="flex items-center gap-1"><Music size={12} /> Audio</span>
          <span className="flex items-center gap-1"><Video size={12} /> Video</span>
        </div>
      </div>
      {progress && (
        <p className="mt-2 text-xs text-center text-gray-600">{progress}</p>
      )}
    </div>
  )
}
