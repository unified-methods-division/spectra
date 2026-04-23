import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { DisagreementRateCard } from "@/components/eval/disagreement-rate-card"
import * as evalApi from "@/lib/api/eval"

function makeClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
}

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = makeClient()
  return (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  )
}

const mockDisagreements: evalApi.Disagreement[] = [
  {
    id: "d1",
    feedback_item: "abc12345-6789-def0-1111-222222222222",
    field_corrected: "sentiment",
    correction_ids: ["c1"],
    resolution_status: "pending",
    resolved_value: null,
    resolved_at: null,
    created_at: "2026-04-20T10:00:00Z",
  },
  {
    id: "d2",
    feedback_item: "xyz98765-4321-abc0-0000-111111111111",
    field_corrected: "urgency",
    correction_ids: ["c2"],
    resolution_status: "pending",
    resolved_value: null,
    resolved_at: null,
    created_at: "2026-04-21T10:00:00Z",
  },
]

describe("DisagreementRateCard", () => {
  it("shows loading state", () => {
    vi.spyOn(evalApi, "useDisagreementRate").mockReturnValue({
      isLoading: true,
      error: null,
      data: undefined,
    } as any)
    vi.spyOn(evalApi, "useDisagreements").mockReturnValue({
      isLoading: true,
      error: null,
      data: undefined,
    } as any)

    render(<DisagreementRateCard />, { wrapper })
    expect(screen.getByText("Loading…")).toBeInTheDocument()
  })

  it("shows rate and pending count", () => {
    vi.spyOn(evalApi, "useDisagreementRate").mockReturnValue({
      isLoading: false,
      error: null,
      data: { disagreement_rate: 12 },
    } as any)
    vi.spyOn(evalApi, "useDisagreements").mockReturnValue({
      isLoading: false,
      error: null,
      data: mockDisagreements,
    } as any)

    render(<DisagreementRateCard />, { wrapper })
    expect(screen.getByText("12%")).toBeInTheDocument()
    expect(screen.getByText("2 pending")).toBeInTheDocument()
  })

  it("lists pending disagreements with truncated IDs", () => {
    vi.spyOn(evalApi, "useDisagreementRate").mockReturnValue({
      isLoading: false,
      error: null,
      data: { disagreement_rate: 12 },
    } as any)
    vi.spyOn(evalApi, "useDisagreements").mockReturnValue({
      isLoading: false,
      error: null,
      data: mockDisagreements,
    } as any)

    render(<DisagreementRateCard />, { wrapper })
    expect(screen.getByText("abc12345…")).toBeInTheDocument()
    expect(screen.getByText("xyz98765…")).toBeInTheDocument()
  })

  it("shows Resolve button for each pending disagreement", () => {
    vi.spyOn(evalApi, "useDisagreementRate").mockReturnValue({
      isLoading: false,
      error: null,
      data: { disagreement_rate: 5 },
    } as any)
    vi.spyOn(evalApi, "useDisagreements").mockReturnValue({
      isLoading: false,
      error: null,
      data: mockDisagreements,
    } as any)

    render(<DisagreementRateCard />, { wrapper })
    const buttons = screen.getAllByRole("button", { name: /resolve/i })
    expect(buttons).toHaveLength(2)
  })

  it("opens resolve dialog on Resolve click", async () => {
    const user = userEvent.setup()
    vi.spyOn(evalApi, "useDisagreementRate").mockReturnValue({
      isLoading: false,
      error: null,
      data: { disagreement_rate: 5 },
    } as any)
    vi.spyOn(evalApi, "useDisagreements").mockReturnValue({
      isLoading: false,
      error: null,
      data: [mockDisagreements[0]],
    } as any)

    render(<DisagreementRateCard />, { wrapper })
    await user.click(screen.getByRole("button", { name: /resolve/i }))

    expect(screen.getByText("Resolve Disagreement")).toBeInTheDocument()
    expect(screen.getByText("Field: sentiment")).toBeInTheDocument()
  })

  it("shows +N more when more than 5 pending", () => {
    const manyDisagreements = Array.from({ length: 8 }, (_, i) => ({
      ...mockDisagreements[0],
      id: `d${i}`,
      feedback_item: `item${i}2345-6789-def0-1111-222222222222`,
    }))

    vi.spyOn(evalApi, "useDisagreementRate").mockReturnValue({
      isLoading: false,
      error: null,
      data: { disagreement_rate: 50 },
    } as any)
    vi.spyOn(evalApi, "useDisagreements").mockReturnValue({
      isLoading: false,
      error: null,
      data: manyDisagreements,
    } as any)

    render(<DisagreementRateCard />, { wrapper })
    expect(screen.getByText("+3 more")).toBeInTheDocument()
  })

  it("shows empty state when no pending disagreements", () => {
    vi.spyOn(evalApi, "useDisagreementRate").mockReturnValue({
      isLoading: false,
      error: null,
      data: { disagreement_rate: 0 },
    } as any)
    vi.spyOn(evalApi, "useDisagreements").mockReturnValue({
      isLoading: false,
      error: null,
      data: [],
    } as any)

    render(<DisagreementRateCard />, { wrapper })
    expect(screen.getByText(/no pending/i)).toBeInTheDocument()
  })
})