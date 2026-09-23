import type { Query } from '@/types'
import { Badge } from '@/components/ui/badge'

interface ConfidenceBadgeProps {
  confidence: Query['confidence']
}

const config: Record<
  NonNullable<Query['confidence']>,
  { label: string; variant: 'success' | 'warning' | 'secondary' | 'destructive' }
> = {
  high: { label: 'High Confidence', variant: 'success' },
  moderate: { label: 'Moderate', variant: 'warning' },
  low: { label: 'Low Confidence', variant: 'secondary' },
  insufficient: { label: 'Insufficient Evidence', variant: 'destructive' },
}

export default function ConfidenceBadge({ confidence }: ConfidenceBadgeProps) {
  if (!confidence) return null
  const c = config[confidence]
  return <Badge variant={c.variant} className="text-xs">{c.label}</Badge>
}
