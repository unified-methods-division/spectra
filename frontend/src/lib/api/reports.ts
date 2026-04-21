/**
 * Report API client hooks.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiGet, apiPost } from "../api"

export interface ReportSection {
  id: string
  section_type: string
  order: number
  raw_content: Record<string, unknown>
  polished_content: {
    title: string
    body: string
    key_points: string[]
  } | null
}

export interface Report {
  id: string
  report_type: string
  period_start: string
  period_end: string
  status: "pending" | "generating" | "ready" | "failed"
  raw_data: Record<string, unknown> | null
  polished_content: Record<string, unknown> | null
  error_message: string | null
  generated_at: string | null
  created_at: string
  sections: ReportSection[]
}

export interface ReportSummary {
  period_start: string
  period_end: string
  total_items: number
  volume_change: number | null
  accuracy: number
  accuracy_change: number | null
  alerts_count: number
}

export function useReports() {
  return useQuery({
    queryKey: ["reports"],
    queryFn: async () => {
      return apiGet<Report[]>("/api/reports/reports/")
    },
  })
}

export function useReport(reportId: string | undefined) {
  return useQuery({
    queryKey: ["reports", reportId],
    queryFn: async () => {
      return apiGet<Report>(`/api/reports/reports/${reportId}/`)
    },
    enabled: !!reportId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === "pending" || status === "generating") {
        return 2000
      }
      return false
    },
  })
}

export function useReportSummary(reportId: string | undefined) {
  return useQuery({
    queryKey: ["reports", reportId, "summary"],
    queryFn: async () => {
      return apiGet<ReportSummary>(`/api/reports/reports/${reportId}/summary/`)
    },
    enabled: !!reportId,
  })
}

export function useCreateReport() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: {
      report_type?: string
      period_start?: string
      period_end?: string
    }) => {
      return apiPost<Report>("/api/reports/reports/", data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reports"] })
    },
  })
}

export function useRetryReport() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (reportId: string) => {
      return apiPost<Report>(`/api/reports/reports/${reportId}/retry/`)
    },
    onSuccess: (_, reportId) => {
      queryClient.invalidateQueries({ queryKey: ["reports", reportId] })
    },
  })
}
