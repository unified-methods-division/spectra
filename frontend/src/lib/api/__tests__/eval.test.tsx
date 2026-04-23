import { describe, it, expect, vi, beforeEach } from "vitest"
import { renderHook, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import type { ReactNode } from "react"

vi.mock("@/lib/api", () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiDelete: vi.fn(),
}))

import { apiGet, apiPost, apiDelete } from "@/lib/api"
import {
  useDriftDelta,
  useDisagreements,
  useDisagreementRate,
  useResolveDisagreement,
  useRecommendationOutcome,
  useGoldSetItems,
  useCreateGoldSetItem,
  useDeleteGoldSetItem,
  useGoldEval,
  type DriftEntry,
  type Disagreement,
  type RecommendationOutcome,
  type GoldSetItem,
  type GoldEvalResult,
} from "@/lib/api/eval"

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

const mockDrift: DriftEntry[] = [
  { week_start: "2026-04-06", week_end: "2026-04-12", accuracy: 0.87, prev_accuracy: 0.85, delta: 0.02 },
  { week_start: "2026-04-13", week_end: "2026-04-19", accuracy: 0.90, prev_accuracy: 0.87, delta: 0.03 },
]

const mockDisagreements: Disagreement[] = [
  {
    id: "d1",
    feedback_item: "fi1",
    field_corrected: "sentiment",
    correction_ids: ["c1", "c2"],
    resolution_status: "pending",
    resolved_value: null,
    resolved_at: null,
    created_at: "2026-04-20T10:00:00Z",
  },
]

const mockOutcome: RecommendationOutcome[] = [
  {
    id: "o1",
    recommendation: "rec1",
    measured_at: "2026-04-21T00:00:00Z",
    metric_name: "negative_sentiment_pct",
    baseline_value: 0.32,
    current_value: 0.25,
    delta: -0.07,
    interpretation: "Negative sentiment dropped 7pp after actioning.",
  },
]

const mockGoldSetItem: GoldSetItem = {
  id: "gs1",
  feedback_item: "fi1",
  gold_sentiment: "positive",
  gold_urgency: "low",
  gold_themes: ["billing"],
  created_at: "2026-04-20T10:00:00Z",
}

const mockGoldEval: GoldEvalResult = {
  field_accuracy: { sentiment: 1.0, urgency: 0.8 },
  theme_precision: 0.75,
  theme_recall: 0.8,
  overall_accuracy: 0.9,
  items_evaluated: 5,
}

describe("eval API hooks", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("useDriftDelta fetches with weeks param", async () => {
    ;(apiGet as ReturnType<typeof vi.fn>).mockResolvedValue(mockDrift)
    const { result } = renderHook(() => useDriftDelta(4), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(apiGet).toHaveBeenCalledWith("/api/analysis/eval/drift/?weeks=4")
    expect(result.current.data).toEqual(mockDrift)
  })

  it("useDriftDelta defaults weeks to 4", async () => {
    ;(apiGet as ReturnType<typeof vi.fn>).mockResolvedValue(mockDrift)
    const { result } = renderHook(() => useDriftDelta(), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(apiGet).toHaveBeenCalledWith("/api/analysis/eval/drift/?weeks=4")
  })

  it("useDisagreements fetches without filter", async () => {
    ;(apiGet as ReturnType<typeof vi.fn>).mockResolvedValue(mockDisagreements)
    const { result } = renderHook(() => useDisagreements(), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(apiGet).toHaveBeenCalledWith("/api/analysis/disagreements/")
    expect(result.current.data).toEqual(mockDisagreements)
  })

  it("useDisagreements passes resolution_status filter", async () => {
    ;(apiGet as ReturnType<typeof vi.fn>).mockResolvedValue([])
    const { result } = renderHook(() => useDisagreements("pending"), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(apiGet).toHaveBeenCalledWith("/api/analysis/disagreements/?resolution_status=pending")
  })

  it("useDisagreementRate returns rate object", async () => {
    ;(apiGet as ReturnType<typeof vi.fn>).mockResolvedValue({ disagreement_rate: 12.5 })
    const { result } = renderHook(() => useDisagreementRate(), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.disagreement_rate).toBe(12.5)
  })

  it("useResolveDisagreement posts resolved_value and invalidates disagreements + rate", async () => {
    const resolved: Disagreement = { ...mockDisagreements[0], resolution_status: "resolved", resolved_value: "positive" }
    ;(apiPost as ReturnType<typeof vi.fn>).mockResolvedValue(resolved)
    const qc = new QueryClient()
    const invalidateSpy = vi.spyOn(qc, "invalidateQueries")
    const { result } = renderHook(() => useResolveDisagreement(), {
      wrapper: ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={qc}>{children}</QueryClientProvider>
      ),
    })
    result.current.mutate({ disagreementId: "d1", resolvedValue: "positive" })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(apiPost).toHaveBeenCalledWith("/api/analysis/disagreements/d1/resolve/", { resolved_value: "positive" })
    const invalidatedKeys = invalidateSpy.mock.calls.map(c => c[0]?.queryKey)
    expect(invalidatedKeys).toContainEqual(["eval", "disagreements"])
    expect(invalidatedKeys).toContainEqual(["eval", "disagreement-rate"])
  })

  it("useRecommendationOutcome skips when id undefined", () => {
    ;(apiGet as ReturnType<typeof vi.fn>).mockResolvedValue(mockOutcome)
    const { result } = renderHook(() => useRecommendationOutcome(undefined), { wrapper })
    expect(result.current.fetchStatus).toBe("idle")
    expect(apiGet).not.toHaveBeenCalled()
  })

  it("useRecommendationOutcome fetches when id provided", async () => {
    ;(apiGet as ReturnType<typeof vi.fn>).mockResolvedValue(mockOutcome)
    const { result } = renderHook(() => useRecommendationOutcome("rec1"), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(apiGet).toHaveBeenCalledWith("/api/analysis/recommendations/rec1/outcome/")
    expect(result.current.data).toEqual(mockOutcome)
  })

  it("useGoldSetItems fetches gold set items", async () => {
    ;(apiGet as ReturnType<typeof vi.fn>).mockResolvedValue([mockGoldSetItem])
    const { result } = renderHook(() => useGoldSetItems(), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(apiGet).toHaveBeenCalledWith("/api/analysis/gold-set/")
    expect(result.current.data).toEqual([mockGoldSetItem])
  })

  it("useCreateGoldSetItem posts new item and invalidates", async () => {
    ;(apiPost as ReturnType<typeof vi.fn>).mockResolvedValue(mockGoldSetItem)
    const { result } = renderHook(() => useCreateGoldSetItem(), { wrapper })
    result.current.mutate({
      feedbackItem: "fi1",
      goldSentiment: "positive",
      goldUrgency: "low",
      goldThemes: ["billing"],
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(apiPost).toHaveBeenCalledWith("/api/analysis/gold-set/", {
      feedback_item: "fi1",
      gold_sentiment: "positive",
      gold_urgency: "low",
      gold_themes: ["billing"],
    })
  })

  it("useDeleteGoldSetItem calls delete and invalidates", async () => {
    ;(apiDelete as ReturnType<typeof vi.fn>).mockResolvedValue(undefined)
    const { result } = renderHook(() => useDeleteGoldSetItem(), { wrapper })
    result.current.mutate("gs1")
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(apiDelete).toHaveBeenCalledWith("/api/analysis/gold-set/gs1/")
  })

  it("useGoldEval fetches without prompt version", async () => {
    ;(apiGet as ReturnType<typeof vi.fn>).mockResolvedValue(mockGoldEval)
    const { result } = renderHook(() => useGoldEval(), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(apiGet).toHaveBeenCalledWith("/api/analysis/eval/gold/")
    expect(result.current.data?.items_evaluated).toBe(5)
  })

  it("useGoldEval passes prompt_version_id when provided", async () => {
    ;(apiGet as ReturnType<typeof vi.fn>).mockResolvedValue(mockGoldEval)
    const { result } = renderHook(() => useGoldEval("pv1"), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(apiGet).toHaveBeenCalledWith("/api/analysis/eval/gold/?prompt_version_id=pv1")
  })
})