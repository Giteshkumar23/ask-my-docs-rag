import { useState, useRef, useEffect } from 'react'
import { MessageSquare, Settings2 } from 'lucide-react'
import { useQueryHistory, useSubmitQuery } from '@/hooks/useQuery'
import { useCollections } from '@/hooks/useCollections'
import type { Citation, Query } from '@/types'
import ChatMessage from '@/components/chat/ChatMessage'
import ChatInput from '@/components/chat/ChatInput'
import SourcePanel from '@/components/chat/SourcePanel'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'

const SUGGESTED_QUESTIONS = [
  'What are the main topics covered in the documents?',
  'Summarize the key findings',
  'What are the conclusions or recommendations?',
  'List the most important data points',
]

export default function AskPage() {
  const [messages, setMessages] = useState<Query[]>([])
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null)
  const [sourcePanelOpen, setSourcePanelOpen] = useState(false)
  const [showRetrievalDetails, setShowRetrievalDetails] = useState(false)
  const [selectedCollectionId, setSelectedCollectionId] = useState<string | undefined>()
  const [allCitations, setAllCitations] = useState<Citation[]>([])
  const bottomRef = useRef<HTMLDivElement>(null)

  const { data: history } = useQueryHistory()
  const { mutateAsync: submitQuery, isPending } = useSubmitQuery()
  const { data: collections } = useCollections()

  // Load query history on mount
  useEffect(() => {
    if (history) {
      setMessages(history)
    }
  }, [history])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = async (question: string, collectionId?: string) => {
    // Optimistically add a processing entry
    const tempId = `temp-${Date.now()}`
    const tempQuery: Query = {
      id: tempId,
      question,
      answer: null,
      confidence: null,
      status: 'processing',
      citations: [],
      retrieval_time: null,
      reranking_time: null,
      generation_time: null,
      total_time: null,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, tempQuery])

    try {
      const result = await submitQuery({ question, collectionId })
      setMessages((prev) =>
        prev.map((m) => (m.id === tempId ? result : m)),
      )
      if (result.citations.length > 0) {
        setAllCitations(result.citations)
        setSourcePanelOpen(true)
      }
    } catch {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === tempId ? { ...m, status: 'failed' as const } : m,
        ),
      )
    }
  }

  const handleCitationClick = (citation: Citation) => {
    setSelectedCitation(citation)
    setAllCitations(
      messages.flatMap((m) => m.citations).filter((c) => c.document_name === citation.document_name || true),
    )
    setSourcePanelOpen(true)
  }

  return (
    <div className="flex h-full overflow-hidden">
      {/* Main chat area */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Toolbar */}
        <div className="flex items-center justify-between px-6 py-2 border-b border-border bg-background">
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-semibold">Ask</h1>
            <span className="text-xs text-muted-foreground">
              {messages.length} message{messages.length !== 1 ? 's' : ''}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <Switch
                id="retrieval-details"
                checked={showRetrievalDetails}
                onCheckedChange={setShowRetrievalDetails}
              />
              <Label htmlFor="retrieval-details" className="text-xs text-muted-foreground cursor-pointer">
                Show retrieval details
              </Label>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="text-xs"
              onClick={() => setSourcePanelOpen((v) => !v)}
            >
              <Settings2 className="h-3.5 w-3.5 mr-1.5" />
              Sources
            </Button>
          </div>
        </div>

        {/* Messages */}
        <ScrollArea className="flex-1">
          <div className="max-w-4xl mx-auto px-6 py-6 space-y-6">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <MessageSquare className="h-14 w-14 text-muted-foreground mb-5" />
                <h2 className="text-lg font-semibold text-foreground">Ask your documents</h2>
                <p className="text-sm text-muted-foreground mt-2 max-w-sm">
                  Get evidence-backed answers from your knowledge base. Every answer cites its sources.
                </p>
                <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg">
                  {SUGGESTED_QUESTIONS.map((q) => (
                    <button
                      key={q}
                      onClick={() => handleSubmit(q, selectedCollectionId)}
                      className="text-left rounded-lg border border-border p-3 text-xs text-muted-foreground hover:text-foreground hover:border-primary/40 hover:bg-muted/30 transition-all"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((query) => (
                <ChatMessage
                  key={query.id}
                  query={query}
                  onCitationClick={handleCitationClick}
                  showRetrievalDetails={showRetrievalDetails}
                />
              ))
            )}
            <div ref={bottomRef} />
          </div>
        </ScrollArea>

        {/* Input */}
        <ChatInput
          onSubmit={handleSubmit}
          isLoading={isPending}
          collections={collections ?? []}
          selectedCollectionId={selectedCollectionId}
          onCollectionChange={setSelectedCollectionId}
        />
      </div>

      {/* Source panel */}
      {sourcePanelOpen && (
        <SourcePanel
          citation={selectedCitation}
          allCitations={allCitations}
          onClose={() => setSourcePanelOpen(false)}
          onSelectCitation={setSelectedCitation}
        />
      )}
    </div>
  )
}
