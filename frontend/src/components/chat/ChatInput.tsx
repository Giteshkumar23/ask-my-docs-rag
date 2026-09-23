import { useState, useRef, KeyboardEvent } from 'react'
import { Send, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type { Collection } from '@/types'

interface ChatInputProps {
  onSubmit: (question: string, collectionId?: string) => void
  isLoading: boolean
  collections: Collection[]
  selectedCollectionId: string | undefined
  onCollectionChange: (id: string | undefined) => void
}

export default function ChatInput({
  onSubmit,
  isLoading,
  collections,
  selectedCollectionId,
  onCollectionChange,
}: ChatInputProps) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSubmit = () => {
    const trimmed = value.trim()
    if (!trimmed || isLoading) return
    onSubmit(trimmed, selectedCollectionId)
    setValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleInput = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }

  return (
    <div className="border-t border-border bg-background p-4">
      <div className="max-w-4xl mx-auto space-y-2">
        {/* Collection filter */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Collection:</span>
          <Select
            value={selectedCollectionId ?? 'all'}
            onValueChange={(v) => onCollectionChange(v === 'all' ? undefined : v)}
          >
            <SelectTrigger className="h-7 w-48 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All documents</SelectItem>
              {collections.map((c) => (
                <SelectItem key={c.id} value={c.id}>
                  {c.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Input area */}
        <div className="flex items-end gap-2 rounded-xl border border-border bg-muted/30 px-4 py-3 focus-within:border-primary/50 transition-colors">
          <Textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onInput={handleInput}
            placeholder="Ask a question about your documents… (Enter to send, Shift+Enter for newline)"
            className="flex-1 min-h-[36px] max-h-40 resize-none border-0 bg-transparent p-0 text-sm focus-visible:ring-0 shadow-none"
            rows={1}
            disabled={isLoading}
          />
          <Button
            size="icon"
            className="h-8 w-8 flex-shrink-0"
            onClick={handleSubmit}
            disabled={!value.trim() || isLoading}
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>

        <p className="text-xs text-muted-foreground text-center">
          AI-generated answers may contain errors. Always verify against source documents.
        </p>
      </div>
    </div>
  )
}
