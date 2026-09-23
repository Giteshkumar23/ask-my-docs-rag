import { useState, useEffect } from 'react'
import { FileText, Search, Filter } from 'lucide-react'
import { toast } from 'sonner'
import {
  useDocuments,
  useDeleteDocument,
  useReindexDocument,
} from '@/hooks/useDocuments'
import { useCollections } from '@/hooks/useCollections'
import type { Document, DocumentFilters } from '@/types'
import DocumentCard from '@/components/documents/DocumentCard'
import DocumentUpload from '@/components/documents/DocumentUpload'
import ChunksViewer from '@/components/documents/ChunksViewer'
import { Input } from '@/components/ui/input'
// import { Button } from '@/components/ui/button'
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
import { Card, CardContent } from '@/components/ui/card'

const IN_PROGRESS_STATUSES: Document['status'][] = [
  'uploading',
  'processing',
  'chunking',
  'embedding',
  'indexing',
]

export default function DocumentsPage() {
  const [filters, setFilters] = useState<DocumentFilters>({})
  const [chunkDocId, setChunkDocId] = useState<string | null>(null)
  
  const { data: documents, isLoading, refetch } = useDocuments(filters)
  const { data: collections } = useCollections()
  const { mutate: deleteDoc } = useDeleteDocument()
  const { mutate: reindexDoc } = useReindexDocument()

  // Poll while any doc is in-progress
  const hasInProgress = documents?.some((d) =>
    IN_PROGRESS_STATUSES.includes(d.status),
  )

  useEffect(() => {
    if (!hasInProgress) return
    const interval = setInterval(() => {
      refetch()
    }, 3000)
    return () => clearInterval(interval)
  }, [hasInProgress, refetch])

  const handleDelete = (id: string) => {
    if (!window.confirm('Delete this document?')) return
    deleteDoc(id, {
      onSuccess: () => toast.success('Document deleted'),
    })
  }

  const handleReindex = (id: string) => {
    reindexDoc(id, {
      onSuccess: () => toast.success('Reindexing started'),
    })
  }

  return (
    <div className="p-6 space-y-5">
      <div>
        <h1 className="text-xl font-semibold">Documents</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Upload and manage your knowledge base documents
        </p>
      </div>

      {/* Upload zone */}
      <DocumentUpload />

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search documents…"
            className="pl-9"
            value={filters.search ?? ''}
            onChange={(e) =>
              setFilters((f) => ({ ...f, search: e.target.value || undefined }))
            }
          />
        </div>

        <Select
          value={filters.status ?? 'all'}
          onValueChange={(v) =>
            setFilters((f) => ({
              ...f,
              status: v === 'all' ? undefined : (v as Document['status']),
            }))
          }
        >
          <SelectTrigger className="w-40">
            <Filter className="h-3.5 w-3.5 mr-2 text-muted-foreground" />
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="completed">Ready</SelectItem>
            <SelectItem value="processing">Processing</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={filters.collection_id ?? 'all'}
          onValueChange={(v) =>
            setFilters((f) => ({
              ...f,
              collection_id: v === 'all' ? undefined : v,
            }))
          }
        >
          <SelectTrigger className="w-44">
            <SelectValue placeholder="Collection" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Collections</SelectItem>
            {collections?.map((c) => (
              <SelectItem key={c.id} value={c.id}>
                {c.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Document grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-40 rounded-lg" />
          ))}
        </div>
      ) : documents && documents.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {documents.map((doc) => (
            <DocumentCard
              key={doc.id}
              document={doc}
              onDelete={handleDelete}
              onReindex={handleReindex}
              onViewChunks={(id) => setChunkDocId(id)}
            />
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <FileText className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-sm font-medium text-foreground">No documents found</p>
            <p className="text-sm text-muted-foreground mt-1">
              Upload documents above to get started
            </p>
          </CardContent>
        </Card>
      )}

      {/* Chunks dialog */}
      <Dialog open={!!chunkDocId} onOpenChange={(o) => !o && setChunkDocId(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Document Chunks</DialogTitle>
          </DialogHeader>
          {chunkDocId && <ChunksViewer documentId={chunkDocId} />}
        </DialogContent>
      </Dialog>
    </div>
  )
}
