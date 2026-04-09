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
