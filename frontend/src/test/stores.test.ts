import { describe, it, expect, beforeEach } from 'vitest'
import { useAuthStore } from '../store/authStore'
import { useDocStore } from '../store/docStore'

describe('authStore', () => {
  beforeEach(() => useAuthStore.setState({ token: null, userId: null }))

  it('starts with no token', () => {
    expect(useAuthStore.getState().token).toBeNull()
  })

  it('sets token on login', () => {
    useAuthStore.getState().login('my-token')
    expect(useAuthStore.getState().token).toBe('my-token')
  })

  it('clears token on logout', () => {
    useAuthStore.getState().login('my-token')
    useAuthStore.getState().logout()
    expect(useAuthStore.getState().token).toBeNull()
  })
})

describe('docStore', () => {
  const doc = { id: 'd1', filename: 'a.pdf', file_type: 'pdf' as const, status: 'ready' as const, created_at: '2024-01-01' }

  beforeEach(() => useDocStore.setState({ documents: [], selected: null }))

  it('adds a document', () => {
    useDocStore.getState().addDocument(doc)
    expect(useDocStore.getState().documents).toHaveLength(1)
  })

  it('prepends new document', () => {
    const doc2 = { ...doc, id: 'd2', filename: 'b.pdf' }
    useDocStore.getState().addDocument(doc)
    useDocStore.getState().addDocument(doc2)
    expect(useDocStore.getState().documents[0].id).toBe('d2')
  })

  it('removes a document', () => {
    useDocStore.getState().addDocument(doc)
    useDocStore.getState().removeDocument('d1')
    expect(useDocStore.getState().documents).toHaveLength(0)
  })

  it('updates a document', () => {
    useDocStore.getState().addDocument(doc)
    useDocStore.getState().updateDocument('d1', { status: 'processing' })
    expect(useDocStore.getState().documents[0].status).toBe('processing')
  })

  it('updates selected document when it matches', () => {
    useDocStore.setState({ documents: [doc], selected: doc })
    useDocStore.getState().updateDocument('d1', { summary: 'new summary' })
    expect(useDocStore.getState().selected?.summary).toBe('new summary')
  })

  it('selects a document', () => {
    useDocStore.getState().selectDocument(doc)
    expect(useDocStore.getState().selected?.id).toBe('d1')
  })

  it('deselects when null passed', () => {
    useDocStore.getState().selectDocument(doc)
    useDocStore.getState().selectDocument(null)
    expect(useDocStore.getState().selected).toBeNull()
  })

  it('sets documents list', () => {
    useDocStore.getState().setDocuments([doc, { ...doc, id: 'd2' }])
    expect(useDocStore.getState().documents).toHaveLength(2)
  })

  it('clears selected when removed doc was selected', () => {
    useDocStore.setState({ documents: [doc], selected: doc })
    useDocStore.getState().removeDocument('d1')
    expect(useDocStore.getState().selected).toBeNull()
  })
})
