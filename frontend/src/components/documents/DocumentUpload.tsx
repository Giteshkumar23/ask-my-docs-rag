import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { UploadCloud, X, FileText, CheckCircle2, AlertCircle } from 'lucide-react'
import { toast } from 'sonner'
import { cn, formatBytes } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { useUploadDocument } from '@/hooks/useDocuments'

interface UploadFile {
  file: File
  progress: number
  status: 'pending' | 'uploading' | 'done' | 'error'
  error?: string
}

interface DocumentUploadProps {
  collectionId?: string
}

export default function DocumentUpload({ collectionId }: DocumentUploadProps) {
  const [queue, setQueue] = useState<UploadFile[]>([])
  const { mutateAsync: upload } = useUploadDocument()

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const newItems: UploadFile[] = acceptedFiles.map((f) => ({
        file: f,
        progress: 0,
        status: 'pending',
      }))
      setQueue((prev) => [...prev, ...newItems])

      newItems.forEach(async (item) => {
        setQueue((prev) =>
          prev.map((q) =>
            q.file === item.file ? { ...q, status: 'uploading' } : q,
          ),
        )
        try {
          await upload({
            file: item.file,
            collectionId,
            onProgress: (progress) => {
              setQueue((prev) =>
                prev.map((q) =>
                  q.file === item.file ? { ...q, progress } : q,
                ),
              )
            },
          })
          setQueue((prev) =>
            prev.map((q) =>
              q.file === item.file
                ? { ...q, status: 'done', progress: 100 }
                : q,
            ),
          )
          toast.success(`${item.file.name} uploaded successfully`)
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Upload failed'
          setQueue((prev) =>
            prev.map((q) =>
              q.file === item.file
                ? { ...q, status: 'error', error: message }
                : q,
            ),
          )
        }
      })
    },
    [upload, collectionId],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'text/csv': ['.csv'],
    },
  })

  const remove = (file: File) => {
    setQueue((prev) => prev.filter((q) => q.file !== file))
  }

  return (
    <div className="space-y-3">
      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors duration-200',
          isDragActive
            ? 'border-primary bg-primary/5'
            : 'border-border hover:border-primary/50 hover:bg-muted/30',
        )}
      >
        <input {...getInputProps()} />
        <UploadCloud className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
        {isDragActive ? (
          <p className="text-sm font-medium text-primary">Drop files here…</p>
        ) : (
          <>
            <p className="text-sm font-medium text-foreground">
              Drag & drop files, or{' '}
              <span className="text-primary">browse</span>
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              PDF, DOCX, TXT, MD, XLSX, CSV
            </p>
          </>
        )}
      </div>

      {queue.length > 0 && (
        <div className="space-y-2">
          {queue.map((item, i) => (
            <div
              key={i}
              className="flex items-center gap-3 p-3 rounded-lg border border-border bg-muted/20"
            >
              <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs font-medium truncate">{item.file.name}</p>
                  <span className="text-xs text-muted-foreground flex-shrink-0">
                    {formatBytes(item.file.size)}
                  </span>
                </div>
                {item.status === 'uploading' && (
                  <Progress value={item.progress} className="mt-1.5 h-1" />
                )}
                {item.status === 'error' && (
                  <p className="text-xs text-destructive mt-0.5">{item.error}</p>
                )}
              </div>
              {item.status === 'done' && (
                <CheckCircle2 className="h-4 w-4 text-green-500 flex-shrink-0" />
              )}
              {item.status === 'error' && (
                <AlertCircle className="h-4 w-4 text-destructive flex-shrink-0" />
              )}
              {(item.status === 'pending' || item.status === 'done') && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 flex-shrink-0"
                  onClick={() => remove(item.file)}
                >
                  <X className="h-3 w-3" />
                </Button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
