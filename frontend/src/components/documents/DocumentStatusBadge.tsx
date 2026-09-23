import type { Document } from '@/types'
import { Badge } from '@/components/ui/badge'

const statusConfig: Record<
  Document['status'],
  { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning' }
> = {
  uploading: { label: 'Uploading', variant: 'secondary' },
  processing: { label: 'Processing', variant: 'default' },
  chunking: { label: 'Chunking', variant: 'default' },
  embedding: { label: 'Embedding', variant: 'warning' },
  indexing: { label: 'Indexing', variant: 'warning' },
  completed: { label: 'Ready', variant: 'success' },
  failed: { label: 'Failed', variant: 'destructive' },
}

interface DocumentStatusBadgeProps {
  status: Document['status']
}

export default function DocumentStatusBadge({ status }: DocumentStatusBadgeProps) {
  const config = statusConfig[status] ?? { label: status, variant: 'outline' as const }
  return <Badge variant={config.variant}>{config.label}</Badge>
}
