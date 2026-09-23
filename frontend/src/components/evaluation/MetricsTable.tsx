import { CheckCircle2, XCircle } from 'lucide-react'
import type { EvaluationRun } from '@/types'

interface MetricsTableProps {
  run: EvaluationRun
}

interface MetricRow {
  label: string
  value: number | null
  threshold?: number
  format?: 'percent' | 'ms' | 'raw'
}

function MetricValue({
  value,
  threshold,
  format = 'percent',
}: {
  value: number | null
  threshold?: number
  format?: MetricRow['format']
}) {
  if (value === null) {
    return <span className="text-muted-foreground">—</span>
  }

  const display =
    format === 'percent'
      ? `${(value * 100).toFixed(1)}%`
      : format === 'ms'
        ? `${Math.round(value * 1000)}ms`
        : value.toFixed(3)

  const passed = threshold !== undefined ? value >= threshold : null

  return (
    <div className="flex items-center gap-1.5">
      <span className="font-medium">{display}</span>
      {passed !== null &&
        (passed ? (
          <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
        ) : (
          <XCircle className="h-3.5 w-3.5 text-red-500" />
        ))}
    </div>
  )
}

export default function MetricsTable({ run }: MetricsTableProps) {
  const retrieval: MetricRow[] = [
    { label: 'Recall@5', value: run.recall_at_5, threshold: 0.7 },
    { label: 'Precision@5', value: run.precision_at_5, threshold: 0.6 },
    { label: 'MRR', value: run.mrr, threshold: 0.6 },
    { label: 'Hit Rate', value: run.hit_rate, threshold: 0.8 },
  ]

  const generation: MetricRow[] = [
    { label: 'Faithfulness', value: run.faithfulness, threshold: 0.8 },
    { label: 'Answer Relevance', value: run.answer_relevance, threshold: 0.7 },
    { label: 'Citation Accuracy', value: run.citation_accuracy, threshold: 0.75 },
    { label: 'Citation Coverage', value: run.citation_coverage, threshold: 0.6 },
  ]

  const latency: MetricRow[] = [
    { label: 'Avg Retrieval Latency', value: run.avg_retrieval_latency, format: 'ms' },
    { label: 'Avg Generation Latency', value: run.avg_generation_latency, format: 'ms' },
  ]

  const renderSection = (title: string, rows: MetricRow[]) => (
    <div>
      <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
        {title}
      </h4>
      <div className="rounded-lg border border-border overflow-hidden">
        <table className="w-full text-sm">
          <tbody>
            {rows.map((row) => (
              <tr key={row.label} className="border-b border-border last:border-0">
                <td className="px-4 py-2.5 text-muted-foreground">{row.label}</td>
                <td className="px-4 py-2.5 text-right">
                  <MetricValue
                    value={row.value}
                    threshold={row.threshold}
                    format={row.format}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )

  return (
    <div className="space-y-4">
      {renderSection('Retrieval Metrics', retrieval)}
      {renderSection('Generation Metrics', generation)}
      {renderSection('Latency', latency)}
    </div>
  )
}
