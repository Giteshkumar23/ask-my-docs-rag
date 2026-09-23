import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { FlaskConical, UploadCloud, Play, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { useEvaluationRuns, useStartEvaluation } from '@/hooks/useEvaluation'
import { useCollections } from '@/hooks/useCollections'
import type { EvaluationRun } from '@/types'
import EvaluationRunCard from '@/components/evaluation/EvaluationRunCard'
import MetricsTable from '@/components/evaluation/MetricsTable'
import EvaluationChart from '@/components/evaluation/EvaluationChart'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

export default function EvaluationPage() {
  const { data: runs, isLoading } = useEvaluationRuns()
  const { data: collections } = useCollections()
  const { mutateAsync: startEval, isPending } = useStartEvaluation()

  const [runName, setRunName] = useState('')
  const [datasetFile, setDatasetFile] = useState<File | null>(null)
  const [collectionId, setCollectionId] = useState<string | undefined>()
  const [uploadProgress, setUploadProgress] = useState(0)
  const [selectedRun, setSelectedRun] = useState<EvaluationRun | null>(null)

  const onDrop = useCallback((files: File[]) => {
    if (files[0]) setDatasetFile(files[0])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/json': ['.json'] },
    maxFiles: 1,
  })

  const handleStart = async () => {
    if (!datasetFile || !runName.trim()) return

    try {
      await startEval({
        name: runName,
        datasetFile,
        collectionId,
        onProgress: setUploadProgress,
      })
      toast.success('Evaluation started')
      setRunName('')
      setDatasetFile(null)
      setUploadProgress(0)
    } catch {
      // error toasted by interceptor
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Evaluation</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Benchmark your RAG pipeline with custom datasets
        </p>
      </div>

      {/* Run evaluation card */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-semibold">Run Evaluation</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label>Run Name</Label>
              <Input
                value={runName}
                onChange={(e) => setRunName(e.target.value)}
                placeholder="e.g. baseline-v1"
              />
            </div>
            <div className="space-y-1.5">
              <Label>Collection (optional)</Label>
              <Select
                value={collectionId ?? 'all'}
                onValueChange={(v) => setCollectionId(v === 'all' ? undefined : v)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All documents" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All documents</SelectItem>
                  {collections?.map((c) => (
                    <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div
            {...getRootProps()}
            className={cn(
              'border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors',
              isDragActive ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50',
              datasetFile && 'border-green-400 bg-green-50 dark:bg-green-900/10',
            )}
          >
            <input {...getInputProps()} />
            <UploadCloud className="h-7 w-7 text-muted-foreground mx-auto mb-2" />
            {datasetFile ? (
              <p className="text-sm font-medium text-green-600 dark:text-green-400">
                {datasetFile.name} selected
              </p>
            ) : (
              <p className="text-sm text-muted-foreground">
                Drop evaluation dataset (JSON) here or click to browse
              </p>
            )}
          </div>

          {isPending && uploadProgress > 0 && (
            <Progress value={uploadProgress} className="h-1.5" />
          )}

          <Button
            onClick={handleStart}
            disabled={!datasetFile || !runName.trim() || isPending}
            className="w-full sm:w-auto"
          >
            {isPending ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Play className="h-4 w-4 mr-2" />
            )}
            Start Evaluation
          </Button>
        </CardContent>
      </Card>

      {/* Results */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-48 rounded-lg" />
          ))}
        </div>
      ) : runs && runs.length > 0 ? (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {runs.map((run) => (
              <EvaluationRunCard
                key={run.id}
                run={run}
                onClick={() => setSelectedRun(run)}
              />
            ))}
          </div>

          {/* Chart of latest run */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">
                Latest Run — Metrics Radar
              </CardTitle>
            </CardHeader>
            <CardContent>
              <EvaluationChart runs={runs} />
            </CardContent>
          </Card>
        </>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <FlaskConical className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-sm font-medium">No evaluation runs yet</p>
            <p className="text-sm text-muted-foreground mt-1">
              Upload a dataset and run your first evaluation above
            </p>
          </CardContent>
        </Card>
      )}

      {/* Detail dialog */}
      <Dialog open={!!selectedRun} onOpenChange={(o) => !o && setSelectedRun(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{selectedRun?.name}</DialogTitle>
          </DialogHeader>
          {selectedRun && <MetricsTable run={selectedRun} />}
        </DialogContent>
      </Dialog>
    </div>
  )
}
