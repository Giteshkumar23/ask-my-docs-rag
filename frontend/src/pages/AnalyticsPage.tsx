import { FileText, Hash, MessageSquare, BarChart3, CheckSquare } from 'lucide-react'
import { useAnalytics } from '@/hooks/useAnalytics'
import MetricCard from '@/components/analytics/MetricCard'
import QueriesChart from '@/components/analytics/QueriesChart'
import LatencyChart from '@/components/analytics/LatencyChart'
import SystemStatus from '@/components/analytics/SystemStatus'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

export default function AnalyticsPage() {
  const { data: analytics, isLoading, isError } = useAnalytics()

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-lg" />
          ))}
        </div>

        <Skeleton className="h-52 rounded-lg" />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Skeleton className="h-56 rounded-lg" />
          <Skeleton className="h-56 rounded-lg" />
        </div>
      </div>
    )
  }

  if (isError || !analytics) {
    return (
      <div className="flex items-center justify-center h-full p-6">
        <div className="text-center">
          <BarChart3 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-sm text-muted-foreground">
            Failed to load analytics data
          </p>
        </div>
      </div>
    )
  }

  const positiveRate = analytics.feedback_summary.positive_rate ?? 0
  const avgTotalLatency = analytics.latency_stats.avg_total ?? 0
  const avgRetrievalLatency = analytics.latency_stats.avg_retrieval ?? 0
  const avgRerankingLatency = analytics.latency_stats.avg_reranking ?? 0
  const avgGenerationLatency = analytics.latency_stats.avg_generation ?? 0

  const totalFailures = Object.values(
    analytics.top_failure_categories
  ).reduce((sum, count) => sum + count, 0)

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Analytics</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Performance and usage metrics for your RAG pipeline
        </p>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <MetricCard
          title="Documents"
          value={analytics.total_documents.toLocaleString()}
          icon={FileText}
        />

        <MetricCard
          title="Chunks"
          value={analytics.total_chunks.toLocaleString()}
          icon={Hash}
        />

        <MetricCard
          title="Queries"
          value={analytics.total_queries.toLocaleString()}
          icon={MessageSquare}
        />

        <MetricCard
          title="Positive Feedback"
          value={`${(positiveRate * 100).toFixed(1)}%`}
          icon={CheckSquare}
          trend="up"
          trendValue={`${(positiveRate * 100).toFixed(0)}%`}
        />

        <MetricCard
          title="Avg Latency"
          value={`${avgTotalLatency.toFixed(0)} ms`}
          icon={BarChart3}
        />

        <MetricCard
          title="Failures"
          value={totalFailures.toLocaleString()}
          icon={BarChart3}
          trend={totalFailures === 0 ? 'up' : 'down'}
          trendValue={totalFailures === 0 ? 'None' : 'Review'}
        />
      </div>

      {/* System health */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-semibold">
            System Health
          </CardTitle>
        </CardHeader>

        <CardContent>
          <SystemStatus
            services={{
              database: 'healthy',
              vector_store: 'healthy',
              llm: 'healthy',
              reranker: 'healthy',
            }}
          />
        </CardContent>
      </Card>

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">
              Queries Over Time
            </CardTitle>
          </CardHeader>

          <CardContent>
            {analytics.daily_queries.length > 0 ? (
              <QueriesChart data={analytics.daily_queries} />
            ) : (
              <div className="h-48 flex items-center justify-center text-sm text-muted-foreground">
                No query data yet
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">
              Pipeline Latency Breakdown
            </CardTitle>
          </CardHeader>

          <CardContent>
            <LatencyChart
              data={{
                retrieval: avgRetrievalLatency,
                reranking: avgRerankingLatency,
                generation: avgGenerationLatency,
              }}
            />
          </CardContent>
        </Card>
      </div>

      {/* Confidence breakdown */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold">
            Answer Confidence
          </CardTitle>
        </CardHeader>

        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="rounded-lg border p-4">
              <p className="text-xs text-muted-foreground">High</p>
              <p className="text-2xl font-semibold mt-1">
                {analytics.confidence_breakdown.high}
              </p>
            </div>

            <div className="rounded-lg border p-4">
              <p className="text-xs text-muted-foreground">Moderate</p>
              <p className="text-2xl font-semibold mt-1">
                {analytics.confidence_breakdown.moderate}
              </p>
            </div>

            <div className="rounded-lg border p-4">
              <p className="text-xs text-muted-foreground">Low</p>
              <p className="text-2xl font-semibold mt-1">
                {analytics.confidence_breakdown.low}
              </p>
            </div>

            <div className="rounded-lg border p-4">
              <p className="text-xs text-muted-foreground">Insufficient</p>
              <p className="text-2xl font-semibold mt-1">
                {analytics.confidence_breakdown.insufficient}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Failure categories */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold">
            Failure Categories
          </CardTitle>
        </CardHeader>

        <CardContent>
          {Object.keys(analytics.top_failure_categories).length === 0 ? (
            <p className="text-sm text-muted-foreground py-4 text-center">
              No failures recorded yet
            </p>
          ) : (
            <div className="space-y-3">
              {Object.entries(analytics.top_failure_categories).map(
                ([category, count]) => (
                  <div
                    key={category}
                    className="flex items-center gap-3"
                  >
                    <span className="text-sm flex-1">
                      {category}
                    </span>

                    <span className="text-xs text-muted-foreground">
                      {count}
                    </span>
                  </div>
                )
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}