import type { Citation } from '@/types'
import { cn } from '@/lib/utils'
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from '@/components/ui/tooltip'

interface CitationBadgeProps {
  citation: Citation
  onClick: (citation: Citation) => void
}

export default function CitationBadge({ citation, onClick }: CitationBadgeProps) {
  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            onClick={() => onClick(citation)}
            className={cn(
              'inline-flex items-center justify-center',
              'w-5 h-5 rounded text-[10px] font-bold',
              'bg-primary/15 text-primary hover:bg-primary/25 transition-colors',
              'cursor-pointer align-middle mx-0.5',
            )}
          >
            {citation.citation_number}
          </button>
        </TooltipTrigger>
        <TooltipContent className="max-w-xs">
          <p className="font-medium text-xs">{citation.document_name}</p>
          {citation.page_number && (
            <p className="text-xs opacity-75">Page {citation.page_number}</p>
          )}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
