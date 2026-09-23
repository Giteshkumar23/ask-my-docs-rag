import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import type { EvaluationRun } from '@/types'

export function useEvaluationRuns() {
  return useQuery({
    queryKey: ['evaluations'],
    queryFn: async () => {
      const { data } = await api.get<EvaluationRun[]>('/evaluation/runs')
      return data
    },
  })
}

export function useEvaluationRun(id: string) {
  return useQuery({
    queryKey: ['evaluations', id],
    queryFn: async () => {
      const { data } = await api.get<EvaluationRun>(`/evaluation/runs/${id}`)
      return data
    },
    enabled: !!id,
  })
}

export function useStartEvaluation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      name,
      datasetFile,
      collectionId,
      onProgress,
    }: {
      name: string
      datasetFile: File
      collectionId?: string
      onProgress?: (progress: number) => void
    }) => {
      const formData = new FormData()
      formData.append('name', name)
      formData.append('dataset', datasetFile)
      if (collectionId) formData.append('collection_id', collectionId)

      const { data } = await api.post<EvaluationRun>('/evaluation/run', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (event) => {
          if (event.total && onProgress) {
            onProgress(Math.round((event.loaded / event.total) * 100))
          }
        },
      })
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evaluations'] })
    },
  })
}
