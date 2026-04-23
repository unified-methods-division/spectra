import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import type { ReactNode } from "react"
import { RecommendationOutcomeCard } from "../../eval/recommendation-outcome-card"
import type { RecommendationOutcome } from "@/lib/api/eval"

vi.mock("@/lib/api/eval", () => ({
  useRecommendationOutcome: vi.fn(),
}))

import { useRecommendationOutcome } from "@/lib/api/eval"

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient()
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

const mockOutcomes: RecommendationOutcome[] = [
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
  {
    id: "o2",
    recommendation: "rec1",
    measured_at: "2026-04-21T00:00:00Z",
    metric_name: "resolution_time_avg",
    baseline_value: 4.2,
    current_value: 3.1,
    delta: -1.1,
    interpretation: null,
  },
]

describe("RecommendationOutcomeCard", () => {
  beforeEach(() => vi.clearAllMocks())

  it("renders loading state", () => {
    ;(useRecommendationOutcome as ReturnType<typeof vi.fn>).mockReturnValue({ isLoading: true, error: null, data: null })
    render(<RecommendationOutcomeCard recommendationId="rec1" />, { wrapper })
    expect(screen.getByText("Loading…")).toBeInTheDocument()
  })

  it("renders error state", () => {
    ;(useRecommendationOutcome as ReturnType<typeof vi.fn>).mockReturnValue({ isLoading: false, error: new Error("fail"), data: null })
    render(<RecommendationOutcomeCard recommendationId="rec1" />, { wrapper })
    expect(screen.getByText(/couldn't load/i)).toBeInTheDocument()
  })

  it("renders empty state when no outcomes", () => {
    ;(useRecommendationOutcome as ReturnType<typeof vi.fn>).mockReturnValue({ isLoading: false, error: null, data: [] })
    render(<RecommendationOutcomeCard recommendationId="rec1" />, { wrapper })
    expect(screen.getByText(/no outcome/i)).toBeInTheDocument()
  })

  it("renders outcome metrics with delta", () => {
    ;(useRecommendationOutcome as ReturnType<typeof vi.fn>).mockReturnValue({ isLoading: false, error: null, data: mockOutcomes })
    render(<RecommendationOutcomeCard recommendationId="rec1" />, { wrapper })
    expect(screen.getByText("Outcome metrics")).toBeInTheDocument()
    expect(screen.getByText("negative_sentiment_pct")).toBeInTheDocument()
    expect(screen.getByText("resolution_time_avg")).toBeInTheDocument()
  })

  it("shows interpretation when present", () => {
    ;(useRecommendationOutcome as ReturnType<typeof vi.fn>).mockReturnValue({ isLoading: false, error: null, data: mockOutcomes })
    render(<RecommendationOutcomeCard recommendationId="rec1" />, { wrapper })
    expect(screen.getByText("Negative sentiment dropped 7pp after actioning.")).toBeInTheDocument()
  })

  it("does not render when recommendationId is undefined", () => {
    ;(useRecommendationOutcome as ReturnType<typeof vi.fn>).mockReturnValue({ isLoading: false, error: null, data: null })
    const { container } = render(<RecommendationOutcomeCard recommendationId={undefined} />, { wrapper })
    expect(container.innerHTML).toBe("")
  })
})