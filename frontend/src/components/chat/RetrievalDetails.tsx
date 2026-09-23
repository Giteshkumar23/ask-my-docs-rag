import { useState } from 'react'
import { ChevronDown, ChevronUp, Clock, Zap } from 'lucide-react'
import type { Query } from '@/types'
import { formatDuration } from '@/lib/utils'
import { Button } from '@/components/ui/button'

interface RetrievalDetailsProps {
  query: Query
}

export default function RetrievalDetails({ query }: RetrievalDetailsProps) {
  const [open, setOpen] = useState(false)

  if (!query.total_time) return null

  return (
    <div className="mt-2">
      <Button
        variant="ghost"
        size="sm"
        className="h-6 text-xs text-muted-foreground px-2 gap-1"
        onClick={() => setOpen((v) => !v)}
      >
        {open ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
        Retrieval details
      </Button>

      {open && (
        <div className="mt-2 rounded-lg border border-border bg-muted/20 p-3 text-xs space-y-2">
          <div className="flex items-center gap-2">
            <Clock className="h-3 w-3 text-muted-foreground" />
            <span className="text-muted-foreground">Total time:</span>
            <span className="font-medium">{formatDuration(query.total_time * 1000)}</span>
          </div>
          {query.retrieval_time !== null && (
            <div className="grid grid-cols-3 gap-2 pl-5">
              <div>
                <p className="text-muted-foreground">Retrieval</p>
                <p className="font-medium">{formatDuration(query.retrieval_time * 1000)}</p>
              </div>
              {query.reranking_time !== null && (
                <div>
                  <p className="text-muted-foreground">Reranking</p>
                  <p className="font-medium">{formatDuration(query.reranking_time * 1000)}</p>
                </div>
              )}
              {query.generation_time !== null && (
                <div>
                  <p className="text-muted-foreground">Generation</p>
                  <p className="font-medium">{formatDuration(query.generation_time * 1000)}</p>
                </div>
              )}
            </div>
          )}
          {query.citations.length > 0 && (
            <div className="flex items-center gap-2">
              <Zap className="h-3 w-3 text-muted-foreground" />
              <span className="text-muted-foreground">Sources used:</span>
              <span className="font-medium">{query.citations.length}</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
