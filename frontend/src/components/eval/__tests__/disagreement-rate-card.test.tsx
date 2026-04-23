import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import type { ReactNode } from "react"
import { DisagreementRateCard } from "../../eval/disagreement-rate-card"

vi.mock("@/lib/api/eval", () => ({
  useDisagreementRate: vi.fn(),
  useDisagreements: vi.fn(),
}))

import { useDisagreementRate, useDisagreements } from "@/lib/api/eval"

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient()
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

describe("DisagreementRateCard", () => {
  beforeEach(() => vi.clearAllMocks())

  it("renders loading state", () => {
    ;(useDisagreementRate as ReturnType<typeof vi.fn>).mockReturnValue({ isLoading: true, error: null, data: null })
    ;(useDisagreements as ReturnType<typeof vi.fn>).mockReturnValue({ isLoading: true, error: null, data: null })
    render(<DisagreementRateCard />, { wrapper })
    expect(screen.getByText("Loading…")).toBeInTheDocument()
  })

  it("renders error state", () => {
    ;(useDisagreementRate as ReturnType<typeof vi.fn>).mockReturnValue({ isLoading: false, error: new Error("fail"), data: null })
    ;(useDisagreements as ReturnType<typeof vi.fn>).mockReturnValue({ isLoading: false, error: null, data: [] })
    render(<DisagreementRateCard />, { wrapper })
    expect(screen.getByText(/couldn't load/i)).toBeInTheDocument()
  })

  it("renders disagreement rate as percentage", () => {
    ;(useDisagreementRate as ReturnType<typeof vi.fn>).mockReturnValue({ isLoading: false, error: null, data: { disagreement_rate: 12.5 } })
    ;(useDisagreements as ReturnType<typeof vi.fn>).mockReturnValue({
      isLoading: false, error: null,
      data: [
        { id: "d1", feedback_item: "fi1", field_corrected: "sentiment", correction_ids: [], resolution_status: "pending", resolved_value: null, resolved_at: null, created_at: "2026-01-01T00:00:00Z" },
      ],
    })
    render(<DisagreementRateCard />, { wrapper })
    expect(screen.getByText("12.5%")).toBeInTheDocument()
    expect(screen.getByText("1 pending")).toBeInTheDocument()
  })

  it("shows zero pending when none pending", () => {
    ;(useDisagreementRate as ReturnType<typeof vi.fn>).mockReturnValue({ isLoading: false, error: null, data: { disagreement_rate: 0 } })
    ;(useDisagreements as ReturnType<typeof vi.fn>).mockReturnValue({ isLoading: false, error: null, data: [] })
    render(<DisagreementRateCard />, { wrapper })
    expect(screen.getByText("0%")).toBeInTheDocument()
    expect(screen.getByText("0 pending")).toBeInTheDocument()
  })
})