import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { apiGet, apiPost } from "@/lib/api"
import type {
  CorrectionPayload,
  FeedbackItemsResponse,
} from "@/types/api"

export type ExplorerFilters = {
  page?: number
  sentiment?: string
  urgency?: string
  source?: string
  theme?: string
  search?: string
  date_from?: string
  date_to?: string
}

function buildQueryString(filters: ExplorerFilters): string {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== "") {
      params.set(key, String(value))
    }
  }
  const qs = params.toString()
  return qs ? `?${qs}` : ""
}

export function useFeedbackItems(filters: ExplorerFilters) {
  return useQuery({
    queryKey: ["feedback-items", filters],
    queryFn: () =>
      apiGet<FeedbackItemsResponse>(
        `/api/ingestion/feedback-items/${buildQueryString(filters)}`,
      ),
  })
}

export function useSubmitCorrection() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: CorrectionPayload) =>
      apiPost("/api/analysis/corrections/", data),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["feedback-items"] }),
  })
}
