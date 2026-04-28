import { create } from 'zustand'

export interface TranscriptSegment {
  start: number
  end: number
  text: string
}

export interface Document {
  id: string
  filename: string
  file_type: 'pdf' | 'audio' | 'video'
  status: 'pending' | 'processing' | 'ready' | 'error'
  summary?: string
  transcript_segments?: TranscriptSegment[]
  created_at: string
}

interface DocState {
  documents: Document[]
  selected: Document | null
  setDocuments: (docs: Document[]) => void
  addDocument: (doc: Document) => void
  updateDocument: (id: string, updates: Partial<Document>) => void
  removeDocument: (id: string) => void
  selectDocument: (doc: Document | null) => void
}

export const useDocStore = create<DocState>((set) => ({
  documents: [],
  selected: null,
  setDocuments: (documents) => set({ documents }),
  addDocument: (doc) => set((s) => ({ documents: [doc, ...s.documents] })),
  updateDocument: (id, updates) =>
    set((s) => ({
      documents: s.documents.map((d) => (d.id === id ? { ...d, ...updates } : d)),
      selected: s.selected?.id === id ? { ...s.selected, ...updates } : s.selected,
    })),
  removeDocument: (id) =>
    set((s) => ({
      documents: s.documents.filter((d) => d.id !== id),
      selected: s.selected?.id === id ? null : s.selected,
    })),
  selectDocument: (selected) => set({ selected }),
}))
