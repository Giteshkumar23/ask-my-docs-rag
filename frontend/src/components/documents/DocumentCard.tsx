import { FileText, FileSpreadsheet, File, MoreVertical, Trash2, RefreshCw, Eye } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import type { Document } from '@/types'
import { formatBytes } from '@/lib/utils'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import DocumentStatusBadge from './DocumentStatusBadge'

function DocIcon({ fileType }: { fileType: string }) {
  const type = fileType.toLowerCase()
  if (type === 'pdf' || type === 'docx' || type === 'txt' || type === 'md') {
    return <FileText className="h-5 w-5 text-blue-500" />
  }
  if (type === 'xlsx' || type === 'csv') {
    return <FileSpreadsheet className="h-5 w-5 text-green-500" />
  }
  return <File className="h-5 w-5 text-muted-foreground" />
}

interface DocumentCardProps {
  document: Document
  onDelete: (id: string) => void
  onReindex: (id: string) => void
  onViewChunks: (id: string) => void
}

export default function DocumentCard({
  document: doc,
  onDelete,
  onReindex,
  onViewChunks,
}: DocumentCardProps) {
  return (
    <Card className="group hover:shadow-md transition-shadow duration-200">
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-start gap-3 min-w-0">
            <div className="mt-0.5 flex-shrink-0">
              <DocIcon fileType={doc.file_type} />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium text-foreground truncate" title={doc.name}>
                {doc.name}
              </p>
              <p className="text-xs text-muted-foreground truncate mt-0.5">
                {doc.original_filename}
              </p>
            </div>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 opacity-0 group-hover:opacity-100 flex-shrink-0"
              >
                <MoreVertical className="h-3.5 w-3.5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onViewChunks(doc.id)}>
                <Eye className="h-4 w-4 mr-2" />
                View Chunks
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onReindex(doc.id)}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Reindex
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => onDelete(doc.id)}
                className="text-destructive focus:text-destructive"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-2">
          <DocumentStatusBadge status={doc.status} />
          <span className="text-xs text-muted-foreground">{doc.file_type.toUpperCase()}</span>
          <span className="text-xs text-muted-foreground">{formatBytes(doc.file_size)}</span>
          {doc.num_pages && (
            <span className="text-xs text-muted-foreground">{doc.num_pages} pages</span>
          )}
        </div>

        {doc.status === 'completed' && (
          <p className="mt-2 text-xs text-muted-foreground">
            {doc.num_chunks} chunks indexed
          </p>
        )}

        {doc.error_message && (
          <p className="mt-2 text-xs text-destructive truncate" title={doc.error_message}>
            {doc.error_message}
          </p>
        )}

        <p className="mt-2 text-xs text-muted-foreground">
          {formatDistanceToNow(new Date(doc.created_at), { addSuffix: true })}
        </p>
      </CardContent>
    </Card>
  )
}
