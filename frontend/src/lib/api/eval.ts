import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { apiDelete, apiGet, apiPost } from "@/lib/api"

export interface DriftEntry {
  week_start: string
  week_end: string
  accuracy: number
  prev_accuracy: number | null
  delta: number | null
}

export interface Disagreement {
  id: string
  feedback_item: string
  field_corrected: string
  correction_ids: string[]
  resolution_status: "pending" | "resolved"
  resolved_value: unknown
  resolved_at: string | null
  created_at: string
}

export interface RecommendationOutcome {
  id: string
  recommendation: string
  measured_at: string
  metric_name: string
  baseline_value: number
  current_value: number
  delta: number
  interpretation: string | null
}

export interface GoldSetItem {
  id: string
  feedback_item: string
  gold_sentiment: string
  gold_urgency: string
  gold_themes: string[]
  created_at: string
}

export interface GoldEvalResult {
  field_accuracy: Record<string, number>
  theme_precision: number
  theme_recall: number
  overall_accuracy: number
  items_evaluated: number
}

export function useDriftDelta(weeks: number = 4) {
  return useQuery({
    queryKey: ["eval", "drift", weeks],
    queryFn: async () =>
      apiGet<DriftEntry[]>(`/api/analysis/eval/drift/?weeks=${weeks}`),
  })
}

export function useDisagreements(resolutionStatus?: string) {
  const params = resolutionStatus
    ? `?resolution_status=${resolutionStatus}`
    : ""
  return useQuery({
    queryKey: ["eval", "disagreements", resolutionStatus],
    queryFn: async () =>
      apiGet<Disagreement[]>(`/api/analysis/disagreements/${params}`),
  })
}

export function useDisagreementRate() {
  return useQuery({
    queryKey: ["eval", "disagreement-rate"],
    queryFn: async () =>
      apiGet<{ disagreement_rate: number }>(
        "/api/analysis/disagreements/rate/",
      ),
  })
}

export function useResolveDisagreement() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (args: {
      disagreementId: string
      resolvedValue: unknown
    }) =>
      apiPost<Disagreement>(
        `/api/analysis/disagreements/${args.disagreementId}/resolve/`,
        { resolved_value: args.resolvedValue },
      ),
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: ["eval", "disagreements"],
        exact: false,
      })
      qc.invalidateQueries({
        queryKey: ["eval", "disagreement-rate"],
      })
    },
  })
}

export function useRecommendationOutcome(
  recommendationId: string | undefined,
) {
  return useQuery({
    queryKey: ["eval", "recommendation-outcome", recommendationId],
    queryFn: async () =>
      apiGet<RecommendationOutcome[]>(
        `/api/analysis/recommendations/${recommendationId}/outcome/`,
      ),
    enabled: !!recommendationId,
  })
}

export function useGoldSetItems() {
  return useQuery({
    queryKey: ["eval", "gold-set"],
    queryFn: async () =>
      apiGet<GoldSetItem[]>("/api/analysis/gold-set/"),
  })
}

export function useCreateGoldSetItem() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (args: {
      feedbackItem: string
      goldSentiment: string
      goldUrgency: string
      goldThemes: string[]
    }) =>
      apiPost<GoldSetItem>("/api/analysis/gold-set/", {
        feedback_item: args.feedbackItem,
        gold_sentiment: args.goldSentiment,
        gold_urgency: args.goldUrgency,
        gold_themes: args.goldThemes,
      }),
    onSuccess: () =>
      qc.invalidateQueries({
        queryKey: ["eval", "gold-set"],
      }),
  })
}

export function useDeleteGoldSetItem() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) =>
      apiDelete<void>(`/api/analysis/gold-set/${id}/`),
    onSuccess: () =>
      qc.invalidateQueries({
        queryKey: ["eval", "gold-set"],
      }),
  })
}

export function useGoldEval(promptVersionId?: string) {
  const params = promptVersionId
    ? `?prompt_version_id=${promptVersionId}`
    : ""
  return useQuery({
    queryKey: ["eval", "gold", promptVersionId],
    queryFn: async () =>
      apiGet<GoldEvalResult>(`/api/analysis/eval/gold/${params}`),
  })
}