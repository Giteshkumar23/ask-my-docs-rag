import { Link } from 'react-router-dom'
import {
  BookOpen,
  Brain,
  ShieldCheck,
  FlaskConical,
  Zap,
  ArrowRight,
  FileText,
  MessageSquare,
  BarChart3,
  CheckCircle2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

const features = [
  {
    icon: Brain,
    title: 'Hybrid Intelligence',
    description:
      'BM25 keyword search combined with dense vector retrieval for maximum recall. Configurable weighting lets you tune precision vs. coverage.',
    color: 'text-blue-500',
    bg: 'bg-blue-50 dark:bg-blue-900/20',
  },
  {
    icon: ShieldCheck,
    title: 'Evidence-Backed Answers',
    description:
      'Every answer is grounded in your documents with inline citations and confidence scores. Click any citation to inspect the exact source chunk.',
    color: 'text-green-500',
    bg: 'bg-green-50 dark:bg-green-900/20',
  },
  {
    icon: FlaskConical,
    title: 'Enterprise Evaluation',
    description:
      'Built-in evaluation suite measuring Recall@K, MRR, faithfulness, answer relevance, and citation accuracy against custom benchmark datasets.',
    color: 'text-purple-500',
    bg: 'bg-purple-50 dark:bg-purple-900/20',
  },
  {
    icon: Zap,
    title: 'Production Ready',
    description:
      'Cross-encoder reranking, async processing, real-time status polling, full analytics dashboard, and a clean REST API for integration.',
    color: 'text-amber-500',
    bg: 'bg-amber-50 dark:bg-amber-900/20',
  },
]

const steps = [
  { icon: FileText, label: 'Upload', description: 'Drag & drop PDFs, DOCX, TXT, CSV' },
  { icon: Brain, label: 'Process', description: 'Automatic chunking, embedding, indexing' },
  { icon: MessageSquare, label: 'Ask', description: 'Natural language questions with citations' },
  { icon: BarChart3, label: 'Evaluate', description: 'Measure quality with real metrics' },
]

function DashboardPreview() {
  return (
    <div className="relative w-full max-w-2xl mx-auto rounded-xl border border-border bg-card shadow-xl overflow-hidden">
      {/* Mock header bar */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-border bg-muted/30">
        <div className="w-3 h-3 rounded-full bg-red-400" />
        <div className="w-3 h-3 rounded-full bg-yellow-400" />
        <div className="w-3 h-3 rounded-full bg-green-400" />
        <div className="flex-1 mx-4">
          <div className="h-5 rounded bg-muted w-48" />
        </div>
      </div>

      {/* Mock content */}
      <div className="flex h-48">
        {/* Sidebar */}
        <div className="w-36 border-r border-border bg-muted/20 p-3 space-y-1.5">
          {['Dashboard', 'Documents', 'Ask', 'Collections', 'Analytics'].map((item, i) => (
            <div
              key={item}
              className={`h-7 rounded-md flex items-center px-2 text-xs ${
                i === 2
                  ? 'bg-primary/15 text-primary font-medium'
                  : 'text-muted-foreground'
              }`}
            >
              {item}
            </div>
          ))}
        </div>

        {/* Chat area */}
        <div className="flex-1 p-4 space-y-3">
          {/* User message */}
          <div className="flex justify-end">
            <div className="bg-primary text-primary-foreground rounded-2xl rounded-tr-sm px-3 py-2 text-xs max-w-[70%]">
              What are the key findings in Q3?
            </div>
          </div>
          {/* Assistant message */}
          <div className="flex justify-start">
            <div className="bg-muted/50 border border-border rounded-2xl rounded-tl-sm px-3 py-2 text-xs max-w-[85%] space-y-1">
              <p>The Q3 report highlights three key findings:</p>
              <div className="space-y-0.5">
                <div className="flex items-start gap-1">
                  <span className="text-primary font-bold">1.</span>
                  <span>Revenue growth of 23% YoY <span className="inline-flex items-center justify-center w-4 h-4 rounded bg-primary/15 text-primary text-[9px] font-bold">1</span></span>
                </div>
                <div className="flex items-start gap-1">
                  <span className="text-primary font-bold">2.</span>
                  <span>Customer retention at 94% <span className="inline-flex items-center justify-center w-4 h-4 rounded bg-primary/15 text-primary text-[9px] font-bold">2</span></span>
                </div>
              </div>
            </div>
          </div>
          {/* Confidence + input */}
          <div className="flex items-center gap-2 mt-1">
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
              High Confidence
            </span>
            <span className="text-[10px] text-muted-foreground">2 sources</span>
          </div>
        </div>
      </div>

      {/* Mock input bar */}
      <div className="px-4 py-2 border-t border-border bg-muted/10 flex items-center gap-2">
        <div className="flex-1 h-7 rounded-lg border border-border bg-background" />
        <div className="w-7 h-7 rounded-md bg-primary flex items-center justify-center">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
            <path d="M22 2L11 13" stroke="white" strokeWidth="2" strokeLinecap="round" />
            <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      </div>
    </div>
  )
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Nav */}
      <header className="border-b border-border bg-background/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-primary rounded-lg flex items-center justify-center">
              <BookOpen className="h-3.5 w-3.5 text-primary-foreground" />
            </div>
            <span className="font-semibold text-sm">Ask My Docs</span>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="secondary" className="text-xs">v1.0</Badge>
            <Button asChild size="sm">
              <Link to="/dashboard">Open Dashboard</Link>
            </Button>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 pt-20 pb-16 text-center">
        <Badge variant="outline" className="mb-5 text-xs">
          Enterprise RAG · Hybrid Search · Evidence-Backed
        </Badge>
        <h1 className="text-4xl sm:text-5xl font-bold text-foreground tracking-tight leading-tight max-w-3xl mx-auto">
          Ask your documents.{' '}
          <span className="text-primary">Get evidence-backed answers.</span>
        </h1>
        <p className="mt-5 text-lg text-muted-foreground max-w-xl mx-auto leading-relaxed">
          A production-grade RAG platform with hybrid BM25 + vector search, cross-encoder
          reranking, inline citations, and enterprise evaluation metrics.
        </p>
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
          <Button asChild size="lg">
            <Link to="/dashboard">
              Get Started
              <ArrowRight className="h-4 w-4 ml-2" />
            </Link>
          </Button>
          <Button asChild variant="outline" size="lg">
            <Link to="/dashboard/documents">Upload Documents</Link>
          </Button>
        </div>

        {/* Trust pills */}
        <div className="mt-10 flex flex-wrap items-center justify-center gap-4 text-sm text-muted-foreground">
          {['No hallucinations', 'Every answer cited', 'Full audit trail', 'Open source'].map(
            (item) => (
              <div key={item} className="flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                {item}
              </div>
            ),
          )}
        </div>
      </section>

      {/* Dashboard preview */}
      <section className="max-w-6xl mx-auto px-6 pb-20">
        <DashboardPreview />
      </section>

      {/* How it works */}
      <section className="border-t border-border bg-muted/20 py-16">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-2xl font-bold text-center mb-10">How it works</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {steps.map((step, i) => {
              const Icon = step.icon
              return (
                <div key={step.label} className="text-center space-y-3">
                  <div className="relative mx-auto w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                    <Icon className="h-6 w-6 text-primary" />
                    <span className="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-primary text-primary-foreground text-[10px] font-bold flex items-center justify-center">
                      {i + 1}
                    </span>
                  </div>
                  <p className="font-semibold text-foreground">{step.label}</p>
                  <p className="text-sm text-muted-foreground">{step.description}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <h2 className="text-2xl font-bold text-center mb-10">Built for Production</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {features.map((f) => {
            const Icon = f.icon
            return (
              <div
                key={f.title}
                className="rounded-xl border border-border p-6 bg-card hover:shadow-md transition-shadow"
              >
                <div className={`w-10 h-10 rounded-lg ${f.bg} flex items-center justify-center mb-4`}>
                  <Icon className={`h-5 w-5 ${f.color}`} />
                </div>
                <h3 className="font-semibold text-foreground mb-2">{f.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{f.description}</p>
              </div>
            )
          })}
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-border bg-muted/20 py-16 text-center">
        <div className="max-w-lg mx-auto px-6">
          <h2 className="text-2xl font-bold text-foreground mb-3">
            Ready to ask your documents?
          </h2>
          <p className="text-muted-foreground mb-6 text-sm">
            Upload your first document and get evidence-backed answers in seconds.
          </p>
          <Button asChild size="lg">
            <Link to="/dashboard">
              Open Dashboard
              <ArrowRight className="h-4 w-4 ml-2" />
            </Link>
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-6">
        <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-muted-foreground">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 bg-primary rounded flex items-center justify-center">
              <BookOpen className="h-2.5 w-2.5 text-primary-foreground" />
            </div>
            Ask My Docs — Enterprise RAG Platform
          </div>
          <p>Built with React, TypeScript, FastAPI, and PostgreSQL</p>
        </div>
      </footer>
    </div>
  )
}
