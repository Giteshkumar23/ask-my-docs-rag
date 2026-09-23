import {
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

interface LatencyChartProps {
  data: { retrieval: number; reranking: number; generation: number }
}

export default function LatencyChart({ data }: LatencyChartProps) {
  const chartData = [
    { stage: 'Retrieval', ms: Math.round(data.retrieval * 1000), fill: '#3b82f6' },
    { stage: 'Reranking', ms: Math.round(data.reranking * 1000), fill: '#f59e0b' },
    { stage: 'Generation', ms: Math.round(data.generation * 1000), fill: '#8b5cf6' },
  ]

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
        <XAxis
          dataKey="stage"
          tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
          axisLine={false}
          tickLine={false}
          unit="ms"
        />
        <Tooltip
          formatter={(value: number) => [`${value}ms`, 'Latency']}
          contentStyle={{
            background: 'hsl(var(--popover))',
            border: '1px solid hsl(var(--border))',
            borderRadius: '6px',
            fontSize: '12px',
            color: 'hsl(var(--foreground))',
          }}
        />
        <Bar dataKey="ms" name="Latency (ms)" radius={[4, 4, 0, 0]}>
          {chartData.map((entry, index) => (
            <Cell key={index} fill={entry.fill} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
