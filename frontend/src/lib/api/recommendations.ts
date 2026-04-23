import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { apiGet, apiPost } from "@/lib/api"

export type RecommendationStatus =
  | "proposed"
  | "accepted"
  | "dismissed"
  | "needs_more_evidence"

export interface RecommendationEvidence {
  id: string
  feedback_item_id: string
  feedback_item_themes: string[]
  feedback_item_urgency: string | null
  feedback_item_sentiment: string | null
  evidence_weight: number
  selection_reason: string | null
  created_at: string
}

export interface Recommendation {
  id: string
  title: string
  problem_statement: string
  proposed_action: string
  impact_score: number
  effort_score: number
  confidence: number
  priority_score: number
  decision_owner: string | null
  status: RecommendationStatus
  decided_at: string | null
  created_at: string
  themes: string[]
  evidence: RecommendationEvidence[]
}

export function useRecommendation(recommendationId: string | undefined) {
  return useQuery({
    queryKey: ["recommendations", recommendationId],
    queryFn: async () =>
      apiGet<Recommendation>(`/api/analysis/recommendations/${recommendationId}/`),
    enabled: !!recommendationId,
  })
}

export function useDecideRecommendation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (args: {
      recommendationId: string
      status: Exclude<RecommendationStatus, "proposed">
      decision_owner?: string
    }) =>
      apiPost<Recommendation>(
        `/api/analysis/recommendations/${args.recommendationId}/decide/`,
        { status: args.status, decision_owner: args.decision_owner },
      ),
    onSuccess: (rec) =>
      qc.invalidateQueries({ queryKey: ["recommendations", rec.id] }),
  })
}

