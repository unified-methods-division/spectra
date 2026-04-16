export type SourceType = "csv_upload" | "webhook" | "rss_pull" | "api_pull"

export type Source = {
  id: string
  name: string
  source_type: SourceType
  config: Record<string, unknown> | null
  last_synced_at: string | null
  created_at: string
}

export type UploadResponse = {
  task_id: string
  source_id: string
  status: string
  message: string
}

export type TaskStatus = {
  task_id: string
  status: "pending" | "started" | "success" | "failure" | "retry"
  result?: Record<string, unknown>
  error?: string
}

export type Sentiment = "positive" | "negative" | "neutral" | "mixed"

export type Urgency = "low" | "medium" | "high" | "critical"

export type FeedbackItem = {
  id: string
  source: string
  source_name: string
  content: string
  author: string | null
  sentiment: Sentiment | null
  sentiment_confidence: number | null
  urgency: Urgency | null
  themes: string[] | null
  ai_summary: string | null
  received_at: string
  processed_at: string | null
}

export type FeedbackItemsResponse = {
  count: number
  next: string | null
  previous: string | null
  results: FeedbackItem[]
}

export type CorrectionPayload = {
  feedback_item: string
  field_corrected: "sentiment" | "themes" | "urgency"
  ai_value: unknown
  human_value: unknown
}

export type Theme = {
  id: string
  slug: string
  name: string
  description: string | null
  source: "manual" | "discovered"
  item_count: number
  first_seen_at: string | null
  created_at: string
}

export type ProcessingStatus = {
  source_id: string
  classification: {
    status: string | null
    counts: Record<string, number> | null
    error: string | null
  }
  embedding: {
    status: string | null
    counts: Record<string, number> | null
    error: string | null
  }
  overall_status: "pending" | "processing" | "completed" | "failed"
}
