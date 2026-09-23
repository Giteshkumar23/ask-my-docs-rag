import { X, FileText, ExternalLink } from 'lucide-react'
import type { Citation } from '@/types'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'

interface SourcePanelProps {
  citation: Citation | null
  allCitations: Citation[]
  onClose: () => void
  onSelectCitation: (citation: Citation) => void
}

export default function SourcePanel({
  citation,
  allCitations,
  onClose,
  onSelectCitation,
}: SourcePanelProps) {
  return (
    <div className="w-80 flex flex-col h-full border-l border-border bg-card">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <h3 className="text-sm font-semibold">Sources</h3>
        <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Citation list */}
      <div className="px-3 py-2 border-b border-border">
        <div className="flex flex-wrap gap-1.5">
          {allCitations.map((c) => (
            <button
              key={c.id}
              onClick={() => onSelectCitation(c)}
              className={cn(
                'w-7 h-7 rounded text-xs font-bold transition-colors',
                citation?.id === c.id
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground hover:bg-primary/20 hover:text-primary',
              )}
            >
              {c.citation_number}
            </button>
          ))}
        </div>
      </div>

      {/* Selected citation detail */}
      <ScrollArea className="flex-1">
        {citation ? (
          <div className="p-4 space-y-4">
            {/* Document info */}
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                <p className="text-sm font-medium leading-tight">{citation.document_name}</p>
              </div>
              {citation.page_number && (
                <Badge variant="secondary" className="text-xs">
                  Page {citation.page_number}
                </Badge>
              )}
            </div>

            <Separator />

            {/* Scores */}
            {(citation.bm25_score !== null ||
              citation.vector_score !== null ||
              citation.reranker_score !== null) && (
              <div className="space-y-2">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Relevance Scores
                </p>
                <div className="grid grid-cols-3 gap-2">
                  {citation.bm25_score !== null && (
                    <div className="text-center p-2 rounded bg-muted/30">
                      <p className="text-xs text-muted-foreground">BM25</p>
                      <p className="text-sm font-semibold">
                        {citation.bm25_score.toFixed(3)}
                      </p>
                    </div>
                  )}
                  {citation.vector_score !== null && (
                    <div className="text-center p-2 rounded bg-muted/30">
                      <p className="text-xs text-muted-foreground">Vector</p>
                      <p className="text-sm font-semibold">
                        {citation.vector_score.toFixed(3)}
                      </p>
                    </div>
                  )}
                  {citation.reranker_score !== null && (
                    <div className="text-center p-2 rounded bg-muted/30">
                      <p className="text-xs text-muted-foreground">Reranker</p>
                      <p className="text-sm font-semibold">
                        {citation.reranker_score.toFixed(3)}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            <Separator />

            {/* Text excerpt */}
            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Text Excerpt
              </p>
              <p className="text-sm leading-relaxed text-foreground bg-muted/20 rounded-lg p-3 border border-border">
                {citation.text}
              </p>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full py-16 text-center px-6">
            <ExternalLink className="h-8 w-8 text-muted-foreground mb-3" />
            <p className="text-sm text-muted-foreground">
              Click a citation number to view its source
            </p>
          </div>
        )}
      </ScrollArea>
    </div>
  )
}
