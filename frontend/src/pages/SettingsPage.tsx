import { useState } from 'react'
import { Info } from 'lucide-react'
import { useThemeStore } from '@/stores/theme-store'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'

interface SliderProps {
  label: string
  value: number
  min?: number
  max?: number
  step?: number
  onChange: (v: number) => void
  format?: (v: number) => string
}

function SimpleSlider({ label, value, min = 0, max = 1, step = 0.05, onChange, format }: SliderProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label className="text-sm">{label}</Label>
        <span className="text-sm font-mono text-muted-foreground">
          {format ? format(value) : value.toFixed(2)}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full accent-primary"
      />
    </div>
  )
}

export default function SettingsPage() {
  const { theme, setTheme } = useThemeStore()

  // Retrieval weights (UI only — configure via env on backend)
  const [bm25Weight, setBm25Weight] = useState(0.3)
  const [vectorWeight, setVectorWeight] = useState(0.7)
  const [topK, setTopK] = useState(5)
  const [rerankerEnabled, setRerankerEnabled] = useState(true)

  return (
    <div className="p-6 space-y-6 max-w-2xl">
      <div>
        <h1 className="text-xl font-semibold">Settings</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Display preferences and pipeline configuration reference
        </p>
      </div>

      {/* Display preferences */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Display Preferences</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Dark Mode</Label>
              <p className="text-xs text-muted-foreground mt-0.5">
                Switch between light and dark themes
              </p>
            </div>
            <Switch
              checked={theme === 'dark'}
              onCheckedChange={(checked) => setTheme(checked ? 'dark' : 'light')}
            />
          </div>
        </CardContent>
      </Card>

      {/* Retrieval configuration (read-only reference) */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Retrieval Configuration</CardTitle>
          <CardDescription className="flex items-start gap-1.5">
            <Info className="h-3.5 w-3.5 mt-0.5 flex-shrink-0" />
            These values reflect your current environment variable configuration. To change them, update the backend .env file and restart.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <SimpleSlider
            label="BM25 Weight"
            value={bm25Weight}
            onChange={setBm25Weight}
          />
          <SimpleSlider
            label="Vector Weight"
            value={vectorWeight}
            onChange={setVectorWeight}
          />

          <Separator />

          <SimpleSlider
            label="Top-K Retrieval"
            value={topK}
            min={1}
            max={20}
            step={1}
            onChange={setTopK}
            format={(v) => String(Math.round(v))}
          />

          <Separator />

          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Reranker</Label>
              <p className="text-xs text-muted-foreground mt-0.5">
                Enable cross-encoder reranking
              </p>
            </div>
            <Switch
              checked={rerankerEnabled}
              onCheckedChange={setRerankerEnabled}
            />
          </div>
        </CardContent>
      </Card>

      {/* LLM provider reference */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">LLM Provider</CardTitle>
          <CardDescription>
            Configured via environment variables. No secrets are stored in the browser.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-sm">
            {[
              { key: 'OPENAI_API_KEY', label: 'OpenAI API Key' },
              { key: 'ANTHROPIC_API_KEY', label: 'Anthropic API Key' },
              { key: 'LLM_PROVIDER', label: 'Active Provider' },
              { key: 'EMBEDDING_MODEL', label: 'Embedding Model' },
            ].map((item) => (
              <div key={item.key} className="flex items-center justify-between py-1.5 border-b border-border last:border-0">
                <span className="text-muted-foreground">{item.label}</span>
                <Badge variant="secondary" className="font-mono text-xs">
                  {item.key}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
