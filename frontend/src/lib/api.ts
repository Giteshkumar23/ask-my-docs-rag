import axios from 'axios'
import { toast } from 'sonner'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor: attach a request ID
api.interceptors.request.use((config) => {
  const requestId = crypto.randomUUID()
  config.headers['X-Request-ID'] = requestId
  return config
})

// Response interceptor: handle errors globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred'

    // Don't toast for 404s on query hooks (they often probe)
    if (error.response?.status !== 404) {
      toast.error(message)
    }

    return Promise.reject(error)
  },
)

export default api
