export interface Document {
  id: string
  name: string
  original_filename: string
  file_type: string
  file_size: number
  num_pages: number | null
  num_chunks: number
  status:
    | 'uploading'
    | 'processing'
    | 'chunking'
    | 'embedding'
    | 'indexing'
    | 'completed'
    | 'failed'
  error_message: string | null
  processing_time: number | null
  collection_id: string | null
  created_at: string
  updated_at: string
}

export interface DocumentChunk {
  id: string
  document_id: string
  chunk_index: number
  text: string
  page_number: number | null
  token_count: number | null
  metadata: Record<string, unknown>
}

export interface Collection {
  id: string
  name: string
  description: string | null
  color: string
  document_count: number
  created_at: string
}

export interface Query {
  id: string
  question: string
  answer: string | null
  confidence: 'high' | 'moderate' | 'low' | 'insufficient' | null
  retrieval_time: number | null
  reranking_time: number | null
  generation_time: number | null
  total_time: number | null
  status: 'pending' | 'processing' | 'completed' | 'failed'
  citations: Citation[]
  created_at: string
}

export interface Citation {
  id: string
  citation_number: number
  chunk_id: string
  document_name: string
  page_number: number | null
  text: string
  bm25_score: number | null
  vector_score: number | null
  reranker_score: number | null
}

export interface Analytics {
  total_documents: number
  total_chunks: number
  total_queries: number

  daily_queries: Array<{
    date: string
    count: number
  }>

  confidence_breakdown: {
    high: number
    moderate: number
    low: number
    insufficient: number
  }

  latency_stats: {
    avg_retrieval: number | null
    avg_reranking: number | null
    avg_generation: number | null
    avg_total: number | null
    p95_total: number | null
  }

  feedback_summary: {
    positive: number
    negative: number
    total: number
    positive_rate: number | null
  }

  top_failure_categories: Record<string, number>
}

export interface EvaluationRun {
  id: string
  name: string
  dataset_name: string
  recall_at_5: number | null
  precision_at_5: number | null
  mrr: number | null
  hit_rate: number | null
  faithfulness: number | null
  answer_relevance: number | null
  citation_accuracy: number | null
  citation_coverage: number | null
  avg_retrieval_latency: number | null
  avg_generation_latency: number | null
  num_questions: number
  passed: boolean | null
  created_at: string
}

export interface EvaluationDataset {
  questions: Array<{
    question: string
    expected_answer?: string
    relevant_doc_ids?: string[]
  }>
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy'
  services: {
    database: string
    vector_store: string
    llm: string
    reranker: string
  }
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface DocumentFilters {
  status?: Document['status']
  collection_id?: string
  file_type?: string
  search?: string
}
