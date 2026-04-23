import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import type { ReactNode } from "react"
import { DriftDeltaChart } from "../../eval/drift-delta-chart"
import type { DriftEntry } from "@/lib/api/eval"

vi.mock("@/lib/api/eval", () => ({
  useDriftDelta: vi.fn(),
}))

import { useDriftDelta } from "@/lib/api/eval"

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient()
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

const mockDrift: DriftEntry[] = [
  { week_start: "2026-04-06", week_end: "2026-04-12", accuracy: 0.87, prev_accuracy: 0.85, delta: 0.02 },
  { week_start: "2026-04-13", week_end: "2026-04-19", accuracy: 0.90, prev_accuracy: 0.87, delta: 0.03 },
  { week_start: "2026-04-20", week_end: "2026-04-26", accuracy: 0.82, prev_accuracy: 0.90, delta: -0.08 },
]

describe("DriftDeltaChart", () => {
  beforeEach(() => vi.clearAllMocks())

  it("renders loading state", () => {
    ;(useDriftDelta as ReturnType<typeof vi.fn>).mockReturnValue({ isLoading: true, error: null, data: null })
    render(<DriftDeltaChart />, { wrapper })
    expect(screen.getByText("Loading…")).toBeInTheDocument()
  })

  it("renders error state", () => {
    ;(useDriftDelta as ReturnType<typeof vi.fn>).mockReturnValue({ isLoading: false, error: new Error("fail"), data: null })
    render(<DriftDeltaChart />, { wrapper })
    expect(screen.getByText(/couldn't load/i)).toBeInTheDocument()
  })

  it("renders empty state", () => {
    ;(useDriftDelta as ReturnType<typeof vi.fn>).mockReturnValue({ isLoading: false, error: null, data: [] })
    render(<DriftDeltaChart />, { wrapper })
    expect(screen.getByText(/no drift data/i)).toBeInTheDocument()
  })

  it("renders section heading", () => {
    ;(useDriftDelta as ReturnType<typeof vi.fn>).mockReturnValue({ isLoading: false, error: null, data: mockDrift })
    render(<DriftDeltaChart />, { wrapper })
    expect(screen.getByText("Weekly accuracy trend")).toBeInTheDocument()
  })

  it("renders accuracy bars per entry", () => {
    ;(useDriftDelta as ReturnType<typeof vi.fn>).mockReturnValue({ isLoading: false, error: null, data: mockDrift })
    render(<DriftDeltaChart />, { wrapper })
    expect(screen.getByText("87.0%")).toBeInTheDocument()
    expect(screen.getByText("90.0%")).toBeInTheDocument()
    expect(screen.getByText("82.0%")).toBeInTheDocument()
  })

  it("shows delta arrows — green up for positive, red down for negative", () => {
    ;(useDriftDelta as ReturnType<typeof vi.fn>).mockReturnValue({ isLoading: false, error: null, data: mockDrift })
    const { container } = render(<DriftDeltaChart />, { wrapper })
    expect(container.querySelectorAll(".text-emerald-600").length).toBeGreaterThanOrEqual(1)
    expect(container.querySelectorAll(".text-red-500").length).toBeGreaterThanOrEqual(1)
  })

  it("shows neutral for zero delta", () => {
    const neutralDrift: DriftEntry[] = [
      { week_start: "2026-04-06", week_end: "2026-04-12", accuracy: 0.85, prev_accuracy: 0.85, delta: 0 },
    ]
    ;(useDriftDelta as ReturnType<typeof vi.fn>).mockReturnValue({ isLoading: false, error: null, data: neutralDrift })
    render(<DriftDeltaChart />, { wrapper })
    expect(screen.getByText("—")).toBeInTheDocument()
  })
})