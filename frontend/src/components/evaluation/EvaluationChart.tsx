import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'
import type { EvaluationRun } from '@/types'

interface EvaluationChartProps {
  runs: EvaluationRun[]
}

export default function EvaluationChart({ runs }: EvaluationChartProps) {
  if (runs.length === 0) return null

  // Use the latest run for the radar chart
  const latest = runs[runs.length - 1]

  const data = [
    { metric: 'Recall@5', value: (latest.recall_at_5 ?? 0) * 100 },
    { metric: 'MRR', value: (latest.mrr ?? 0) * 100 },
    { metric: 'Faithfulness', value: (latest.faithfulness ?? 0) * 100 },
    { metric: 'Relevance', value: (latest.answer_relevance ?? 0) * 100 },
    { metric: 'Citation Acc.', value: (latest.citation_accuracy ?? 0) * 100 },
    { metric: 'Hit Rate', value: (latest.hit_rate ?? 0) * 100 },
  ]

  return (
    <ResponsiveContainer width="100%" height={280}>
      <RadarChart data={data}>
        <PolarGrid stroke="hsl(var(--border))" />
        <PolarAngleAxis
          dataKey="metric"
          tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
        />
        <Radar
          name={latest.name}
          dataKey="value"
          stroke="hsl(var(--primary))"
          fill="hsl(var(--primary))"
          fillOpacity={0.2}
        />
        <Tooltip
          formatter={(v: number) => [`${v.toFixed(1)}%`]}
          contentStyle={{
            background: 'hsl(var(--popover))',
            border: '1px solid hsl(var(--border))',
            borderRadius: '6px',
            fontSize: '12px',
            color: 'hsl(var(--foreground))',
          }}
        />
      </RadarChart>
    </ResponsiveContainer>
  )
}
