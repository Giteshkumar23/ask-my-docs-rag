import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import type { Analytics } from '@/types'

export function useAnalytics() {
  return useQuery({
    queryKey: ['analytics'],
    queryFn: async () => {
      const { data } = await api.get<Analytics>('/analytics')
      return data
    },
    staleTime: 1000 * 60, // 1 minute
  })
}
