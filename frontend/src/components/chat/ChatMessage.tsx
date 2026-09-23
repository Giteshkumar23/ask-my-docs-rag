import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import type { Query, Citation } from '@/types'
import { cn } from '@/lib/utils'
import CitationBadge from './CitationBadge'
import ConfidenceBadge from './ConfidenceBadge'
import RetrievalDetails from './RetrievalDetails'
import { Skeleton } from '@/components/ui/skeleton'

interface ChatMessageProps {
  query: Query
  onCitationClick: (citation: Citation) => void
  showRetrievalDetails?: boolean
}

function renderAnswerWithCitations(
  answer: string,
  citations: Citation[],
  onCitationClick: (citation: Citation) => void,
) {
  // Split on citation markers like [1], [2], etc.
  const parts = answer.split(/(\[\d+\])/g)
  return parts.map((part, i) => {
    const match = part.match(/^\[(\d+)\]$/)
    if (match) {
      const num = parseInt(match[1], 10)
      const citation = citations.find((c) => c.citation_number === num)
      if (citation) {
        return <CitationBadge key={i} citation={citation} onClick={onCitationClick} />
      }
    }
    return (
      <ReactMarkdown
        key={i}
        remarkPlugins={[remarkGfm]}
        components={{
          code({ className, children, ...props }) {
            const match = /language-(\w+)/.exec(className ?? '')
            const isInline = !match
            return isInline ? (
              <code className="bg-muted px-1.5 py-0.5 rounded text-xs font-mono" {...props}>
                {children}
              </code>
            ) : (
              <SyntaxHighlighter
                style={oneDark}
                language={match[1]}
                PreTag="div"
                className="rounded-md text-xs my-2"
              >
                {String(children).replace(/\n$/, '')}
              </SyntaxHighlighter>
            )
          },
          p({ children }) {
            return <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>
          },
          ul({ children }) {
            return <ul className="list-disc pl-5 mb-2 space-y-1">{children}</ul>
          },
          ol({ children }) {
            return <ol className="list-decimal pl-5 mb-2 space-y-1">{children}</ol>
          },
        }}
      >
        {part}
      </ReactMarkdown>
    )
  })
}

export default function ChatMessage({
  query,
  onCitationClick,
  showRetrievalDetails = false,
}: ChatMessageProps) {
  return (
    <div className="space-y-4">
      {/* User question */}
      <div className="flex justify-end">
        <div
          className={cn(
            'max-w-[70%] rounded-2xl rounded-tr-sm px-4 py-2.5',
            'bg-primary text-primary-foreground text-sm',
          )}
        >
          {query.question}
        </div>
      </div>

      {/* Assistant answer */}
      <div className="flex justify-start">
        <div className="max-w-[85%] space-y-2">
          <div
            className={cn(
              'rounded-2xl rounded-tl-sm px-4 py-3',
              'bg-muted/50 border border-border text-sm text-foreground',
            )}
          >
            {query.status === 'processing' || query.status === 'pending' ? (
              <div className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-4/5" />
                <Skeleton className="h-4 w-3/5" />
              </div>
            ) : query.status === 'failed' ? (
              <p className="text-destructive text-sm">
                Failed to generate an answer. Please try again.
              </p>
            ) : query.answer ? (
              <div className="prose prose-sm dark:prose-invert max-w-none">
                {renderAnswerWithCitations(query.answer, query.citations, onCitationClick)}
              </div>
            ) : null}
          </div>

          {query.status === 'completed' && (
            <div className="flex items-center gap-2 px-1">
              <ConfidenceBadge confidence={query.confidence} />
              {query.citations.length > 0 && (
                <span className="text-xs text-muted-foreground">
                  {query.citations.length} source{query.citations.length !== 1 ? 's' : ''}
                </span>
              )}
            </div>
          )}

          {showRetrievalDetails && query.status === 'completed' && (
            <RetrievalDetails query={query} />
          )}
        </div>
      </div>
    </div>
  )
}
