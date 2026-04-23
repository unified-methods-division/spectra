import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import type { ReactNode } from "react"
import { EvalAccuracyPanel } from "../../eval/eval-accuracy-panel"
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

describe("EvalAccuracyPanel", () => {
  beforeEach(() => vi.clearAllMocks())

  it("renders loading state", () => {
    ;(useDriftDelta as ReturnType<typeof vi.fn>).mockReturnValue({ isLoading: true, error: null, data: null })
    render(<EvalAccuracyPanel />, { wrapper })
    expect(screen.getByText("Loading…")).toBeInTheDocument()
  })

  it("renders error state", () => {
    ;(useDriftDelta as ReturnType<typeof vi.fn>).mockReturnValue({ isLoading: false, error: new Error("fail"), data: null })
    render(<EvalAccuracyPanel />, { wrapper })
    expect(screen.getByText(/couldn't load/i)).toBeInTheDocument()
  })

  it("renders empty state", () => {
    ;(useDriftDelta as ReturnType<typeof vi.fn>).mockReturnValue({ isLoading: false, error: null, data: [] })
    render(<EvalAccuracyPanel />, { wrapper })
    expect(screen.getByText(/no drift data/i)).toBeInTheDocument()
  })

  it("renders drift entries with accuracy and delta", () => {
    ;(useDriftDelta as ReturnType<typeof vi.fn>).mockReturnValue({ isLoading: false, error: null, data: mockDrift })
    render(<EvalAccuracyPanel />, { wrapper })
    expect(screen.getByText("Accuracy drift")).toBeInTheDocument()
    expect(screen.getByText("87.0%")).toBeInTheDocument()
    expect(screen.getByText("90.0%")).toBeInTheDocument()
  })

  it("shows positive delta in green", () => {
    ;(useDriftDelta as ReturnType<typeof vi.fn>).mockReturnValue({ isLoading: false, error: null, data: mockDrift })
    const { container } = render(<EvalAccuracyPanel />, { wrapper })
    const deltaEls = container.querySelectorAll(".text-emerald-600")
    expect(deltaEls.length).toBeGreaterThan(0)
  })

  it("shows negative delta in red", () => {
    ;(useDriftDelta as ReturnType<typeof vi.fn>).mockReturnValue({ isLoading: false, error: null, data: mockDrift })
    const { container } = render(<EvalAccuracyPanel />, { wrapper })
    const deltaEls = container.querySelectorAll(".text-red-500")
    expect(deltaEls.length).toBeGreaterThan(0)
  })
})