import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import type { Collection } from '@/types'

export function useCollections() {
  return useQuery<Collection[]>({
    queryKey: ['collections'],

    queryFn: async (): Promise<Collection[]> => {
      const { data } = await api.get<
        Collection[] | {
          collections: Collection[]
        } | {
          items: Collection[]
        }
      >('/collections')

      if (Array.isArray(data)) {
        return data
      }

      if ('collections' in data) {
        return data.collections
      }

      if ('items' in data) {
        return data.items
      }

      return []
    },
  })
}

export function useCollection(id: string) {
  return useQuery({
    queryKey: ['collections', id],
    queryFn: async () => {
      const { data } = await api.get<Collection>(`/collections/${id}`)
      return data
    },
    enabled: !!id,
  })
}

export function useCreateCollection() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: {
      name: string
      description?: string
      color?: string
    }) => {
      const { data } = await api.post<Collection>('/collections', payload)
      return data
    },

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['collections'],
      })
    },
  })
}

export function useUpdateCollection() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      id,
      ...payload
    }: {
      id: string
      name?: string
      description?: string
      color?: string
    }) => {
      const { data } = await api.patch<Collection>(
        `/collections/${id}`,
        payload,
      )
      return data
    },

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['collections'],
      })
    },
  })
}

export function useDeleteCollection() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/collections/${id}`)
      return id
    },

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['collections'],
      })

      queryClient.invalidateQueries({
        queryKey: ['documents'],
      })
    },
  })
}