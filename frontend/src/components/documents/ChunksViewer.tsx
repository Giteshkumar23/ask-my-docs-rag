import { FileText } from 'lucide-react'
import type { DocumentChunk } from '@/types'
import { useDocumentChunks } from '@/hooks/useDocuments'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'

interface ChunksViewerProps {
  documentId: string
}

export default function ChunksViewer({ documentId }: ChunksViewerProps) {
  const { data: chunks, isLoading, isError } = useDocumentChunks(documentId)

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-24 w-full" />
        ))}
      </div>
    )
  }

  if (isError || !chunks) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <p className="text-sm">Failed to load chunks.</p>
      </div>
    )
  }

  if (chunks.length === 0) {
    return (
      <div className="text-center py-8">
        <FileText className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
        <p className="text-sm text-muted-foreground">No chunks found.</p>
      </div>
    )
  }

  return (
    <ScrollArea className="h-[500px]">
      <div className="space-y-3 pr-3">
        {chunks.map((chunk: DocumentChunk, index: number) => (
          <div
            key={chunk.id}
            className="rounded-lg border border-border p-3 bg-muted/20 hover:bg-muted/40 transition-colors"
          >
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="outline" className="text-xs">
                Chunk {index + 1}
              </Badge>
              {chunk.page_number && (
                <Badge variant="secondary" className="text-xs">
                  Page {chunk.page_number}
                </Badge>
              )}
              {chunk.token_count && (
                <span className="text-xs text-muted-foreground ml-auto">
                  {chunk.token_count} tokens
                </span>
              )}
            </div>
            <p className="text-sm text-foreground leading-relaxed line-clamp-4">
              {chunk.text}
            </p>
          </div>
        ))}
      </div>
    </ScrollArea>
  )
}
