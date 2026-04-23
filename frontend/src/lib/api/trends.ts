import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { apiGet, apiPost } from "@/lib/api"

export interface DashboardRecommendation {
  id: string
  title: string
  problem_statement: string
  proposed_action: string
  priority_score: number
  status: string
}

export interface DashboardSummary {
  period_start: string
  period_end: string
  total_items: number
  volume_change: number | null
  accuracy: number
  accuracy_change: number | null
  alerts_count: number
  top_recommendations: DashboardRecommendation[]
  source?: "report" | "live"
  report_id?: string | null
}

export interface Alert {
  id: string
  alert_type: string
  severity: "info" | "warning" | "critical"
  title: string
  description: string
  metadata: {
    period_start?: string
    period_end?: string
    explorer_filters?: Record<string, string>
    [k: string]: unknown
  } | null
  acknowledged: boolean
  created_at: string
}

export type DashboardSummaryPeriod =
  | { kind: "this-week" }
  | { kind: "last-week" }
  | { kind: "custom"; periodStart: string; periodEnd: string }

export function trendsPeriodQueryString(p: DashboardSummaryPeriod): string {
  const params = new URLSearchParams()
  if (p.kind === "custom") {
    params.set("period", "custom")
    params.set("period_start", p.periodStart)
    params.set("period_end", p.periodEnd)
  } else {
    params.set("period", p.kind)
  }
  return params.toString()
}

export function useDashboardSummary(period: DashboardSummaryPeriod) {
  const enabled =
    period.kind !== "custom" ||
    (Boolean(period.periodStart) && Boolean(period.periodEnd))

  return useQuery({
    queryKey: ["trends", "dashboard-summary", period],
    queryFn: async () =>
      apiGet<DashboardSummary>(
        `/api/trends/dashboard/summary/?${trendsPeriodQueryString(period)}`,
      ),
    enabled,
  })
}

export function useAlerts(period: DashboardSummaryPeriod) {
  const enabled =
    period.kind !== "custom" ||
    (Boolean(period.periodStart) && Boolean(period.periodEnd))

  return useQuery({
    queryKey: ["trends", "alerts", period],
    queryFn: async () =>
      apiGet<Alert[]>(`/api/trends/alerts/?${trendsPeriodQueryString(period)}`),
    enabled,
  })
}

export function useAcknowledgeAlert() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (alertId: string) =>
      apiPost<Alert>(`/api/trends/alerts/${alertId}/ack/`),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["trends", "alerts"], exact: false }),
  })
}

