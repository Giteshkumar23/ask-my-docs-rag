import { formatDistanceToNow } from 'date-fns'
import { CheckCircle2, XCircle, Clock, FileQuestion } from 'lucide-react'
import type { EvaluationRun } from '@/types'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface EvaluationRunCardProps {
  run: EvaluationRun
  onClick?: () => void
}

function MetricPill({ label, value }: { label: string; value: number | null }) {
  if (value === null) return null
  return (
    <div className="text-center">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-sm font-semibold">{(value * 100).toFixed(1)}%</p>
    </div>
  )
}

export default function EvaluationRunCard({ run, onClick }: EvaluationRunCardProps) {
  return (
    <Card
      className="hover:shadow-md transition-shadow cursor-pointer"
      onClick={onClick}
    >
      <CardContent className="p-4 space-y-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="text-sm font-semibold truncate">{run.name}</p>
            <p className="text-xs text-muted-foreground">{run.dataset_name}</p>
          </div>
          {run.passed !== null ? (
            run.passed ? (
              <Badge variant="success" className="gap-1">
                <CheckCircle2 className="h-3 w-3" />
                Passed
              </Badge>
            ) : (
              <Badge variant="destructive" className="gap-1">
                <XCircle className="h-3 w-3" />
                Failed
              </Badge>
            )
          ) : (
            <Badge variant="secondary" className="gap-1">
              <Clock className="h-3 w-3" />
              Pending
            </Badge>
          )}
        </div>

        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <FileQuestion className="h-3 w-3" />
          {run.num_questions} questions
        </div>

        <div className="grid grid-cols-4 gap-3 pt-1">
          <MetricPill label="Recall@5" value={run.recall_at_5} />
          <MetricPill label="MRR" value={run.mrr} />
          <MetricPill label="Faithfulness" value={run.faithfulness} />
          <MetricPill label="Relevance" value={run.answer_relevance} />
        </div>

        <p className="text-xs text-muted-foreground">
          {formatDistanceToNow(new Date(run.created_at), { addSuffix: true })}
        </p>
      </CardContent>
    </Card>
  )
}
