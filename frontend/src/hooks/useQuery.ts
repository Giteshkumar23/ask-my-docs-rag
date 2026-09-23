import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import type { Query } from '@/types'

export function useQueryHistory() {
  return useQuery({
    queryKey: ['queries'],
    queryFn: async () => {
      const { data } = await api.get<{
        items: Query[]
        total: number
        skip: number
        limit: number
      }>('/query')

      return data.items
    },
  })
}

export function useQueryById(id: string) {
  return useQuery({
    queryKey: ['queries', id],
    queryFn: async () => {
      const { data } = await api.get<Query>(`/query/${id}`)
      return data
    },
    enabled: !!id,
  })
}

export function useSubmitQuery() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      question,
      collectionId,
    }: {
      question: string
      collectionId?: string
    }) => {
      const { data } = await api.post<Query>('/query', {
        question,
        collection_id: collectionId ?? null,
      })
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['queries'] })
      queryClient.invalidateQueries({ queryKey: ['analytics'] })
    },
  })
}
