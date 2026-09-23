import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import type { Document, DocumentChunk, DocumentFilters } from '@/types'

export function useDocuments(filters?: DocumentFilters) {
  return useQuery<Document[]>({
    queryKey: ['documents', filters],

    queryFn: async (): Promise<Document[]> => {
      const params = new URLSearchParams()

      if (filters?.status) {
        params.set('status', filters.status)
      }

      if (filters?.collection_id) {
        params.set('collection_id', filters.collection_id)
      }

      if (filters?.file_type) {
        params.set('file_type', filters.file_type)
      }

      if (filters?.search) {
        params.set('search', filters.search)
      }

      const { data } = await api.get<
        Document[] | {
          documents: Document[]
        } | {
          items: Document[]
        }
      >(`/documents?${params.toString()}`)

      if (Array.isArray(data)) {
        return data
      }

      if ('documents' in data) {
        return data.documents
      }

      if ('items' in data) {
        return data.items
      }

      return []
    },
  })
}

export function useDocument(id: string) {
  return useQuery({
    queryKey: ['documents', id],
    queryFn: async () => {
      const { data } = await api.get<Document>(`/documents/${id}`)
      return data
    },
    enabled: !!id,
  })
}

export function useDocumentChunks(id: string) {
  return useQuery({
    queryKey: ['documents', id, 'chunks'],
    queryFn: async () => {
      const { data } = await api.get<DocumentChunk[]>(
        `/documents/${id}/chunks`,
      )
      return data
    },
    enabled: !!id,
  })
}

export function useUploadDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      file,
      collectionId,
      onProgress,
    }: {
      file: File
      collectionId?: string
      onProgress?: (progress: number) => void
    }) => {
      const formData = new FormData()
      formData.append('file', file)

      if (collectionId) {
        formData.append('collection_id', collectionId)
      }

      const { data } = await api.post<Document>(
        '/documents',
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (event) => {
            if (event.total && onProgress) {
              onProgress(
                Math.round((event.loaded / event.total) * 100),
              )
            }
          },
        },
      )

      return data
    },

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['documents'],
      })
    },
  })
}

export function useDeleteDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/documents/${id}`)
      return id
    },

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['documents'],
      })
    },
  })
}

export function useReindexDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await api.post<Document>(
        `/documents/${id}/reindex`,
      )
      return data
    },

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['documents'],
      })
    },
  })
}