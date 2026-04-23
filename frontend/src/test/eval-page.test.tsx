import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { EvalPage } from "@/pages/eval-page"
import * as evalApi from "@/lib/api/eval"

type UseGoldEvalReturn = ReturnType<typeof evalApi.useGoldEval>
type UseGoldSetItemsReturn = ReturnType<typeof evalApi.useGoldSetItems>
type UseCreateGoldSetItemReturn = ReturnType<typeof evalApi.useCreateGoldSetItem>
type UseDeleteGoldSetItemReturn = ReturnType<typeof evalApi.useDeleteGoldSetItem>

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

const mockGoldItems: evalApi.GoldSetItem[] = [
  {
    id: "gs1",
    feedback_item: "abc12345-6789-def0-1111-222222222222",
    gold_sentiment: "positive",
    gold_urgency: "medium",
    gold_themes: ["pricing", "support"],
    created_at: "2026-04-20T10:00:00Z",
  },
]

const mockEvalResult: evalApi.GoldEvalResult = {
  overall_accuracy: 0.85,
  field_accuracy: { sentiment: 0.9, urgency: 0.8 },
  theme_precision: 0.75,
  theme_recall: 0.7,
  items_evaluated: 10,
}

describe("EvalPage", () => {
  it("shows loading state", () => {
    vi.spyOn(evalApi, "useGoldEval").mockReturnValue({
      isLoading: true,
      error: null,
      data: undefined,
    } as unknown as UseGoldEvalReturn)
    vi.spyOn(evalApi, "useGoldSetItems").mockReturnValue({
      isLoading: true,
      error: null,
      data: undefined,
    } as unknown as UseGoldSetItemsReturn)

    render(<EvalPage />, { wrapper })
    expect(screen.getAllByText(/loading/i).length).toBeGreaterThanOrEqual(1)
  })

  it("renders eval summary KPIs when data available", () => {
    vi.spyOn(evalApi, "useGoldEval").mockReturnValue({
      isLoading: false,
      error: null,
      data: mockEvalResult,
    } as unknown as UseGoldEvalReturn)
    vi.spyOn(evalApi, "useGoldSetItems").mockReturnValue({
      isLoading: false,
      error: null,
      data: mockGoldItems,
    } as unknown as UseGoldSetItemsReturn)
    vi.spyOn(evalApi, "useCreateGoldSetItem").mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as UseCreateGoldSetItemReturn)
    vi.spyOn(evalApi, "useDeleteGoldSetItem").mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as UseDeleteGoldSetItemReturn)

    render(<EvalPage />, { wrapper })
    expect(screen.getByText(/85\.0/)).toBeInTheDocument()
    expect(screen.getByText(/10 items/)).toBeInTheDocument()
    expect(screen.getByText(/90\.0%/)).toBeInTheDocument()
    expect(screen.getByText(/80\.0%/)).toBeInTheDocument()
  })

  it("renders gold set table with items", () => {
    vi.spyOn(evalApi, "useGoldEval").mockReturnValue({
      isLoading: false,
      error: null,
      data: mockEvalResult,
    } as unknown as UseGoldEvalReturn)
    vi.spyOn(evalApi, "useGoldSetItems").mockReturnValue({
      isLoading: false,
      error: null,
      data: mockGoldItems,
    } as unknown as UseGoldSetItemsReturn)
    vi.spyOn(evalApi, "useCreateGoldSetItem").mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as UseCreateGoldSetItemReturn)
    vi.spyOn(evalApi, "useDeleteGoldSetItem").mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as UseDeleteGoldSetItemReturn)

    render(<EvalPage />, { wrapper })
    expect(screen.getByText("abc12345…")).toBeInTheDocument()
    expect(screen.getByText("positive")).toBeInTheDocument()
    expect(screen.getByText("medium")).toBeInTheDocument()
    expect(screen.getByText("pricing, support")).toBeInTheDocument()
  })

  it("shows empty state when no gold items", () => {
    vi.spyOn(evalApi, "useGoldEval").mockReturnValue({
      isLoading: false,
      error: null,
      data: mockEvalResult,
    } as unknown as UseGoldEvalReturn)
    vi.spyOn(evalApi, "useGoldSetItems").mockReturnValue({
      isLoading: false,
      error: null,
      data: [],
    } as unknown as UseGoldSetItemsReturn)
    vi.spyOn(evalApi, "useCreateGoldSetItem").mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as UseCreateGoldSetItemReturn)
    vi.spyOn(evalApi, "useDeleteGoldSetItem").mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as UseDeleteGoldSetItemReturn)

    render(<EvalPage />, { wrapper })
    expect(screen.getByText(/no gold set items yet/i)).toBeInTheDocument()
  })

  it("has add gold item form fields", () => {
    vi.spyOn(evalApi, "useGoldEval").mockReturnValue({
      isLoading: false,
      error: null,
      data: mockEvalResult,
    } as unknown as UseGoldEvalReturn)
    vi.spyOn(evalApi, "useGoldSetItems").mockReturnValue({
      isLoading: false,
      error: null,
      data: mockGoldItems,
    } as unknown as UseGoldSetItemsReturn)
    vi.spyOn(evalApi, "useCreateGoldSetItem").mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as UseCreateGoldSetItemReturn)
    vi.spyOn(evalApi, "useDeleteGoldSetItem").mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as UseDeleteGoldSetItemReturn)

    render(<EvalPage />, { wrapper })
    expect(screen.getByLabelText(/feedback item/i)).toBeInTheDocument()
  })

  it("shows validation errors on empty submit", async () => {
    const user = userEvent.setup()
    vi.spyOn(evalApi, "useGoldEval").mockReturnValue({
      isLoading: false,
      error: null,
      data: mockEvalResult,
    } as unknown as UseGoldEvalReturn)
    vi.spyOn(evalApi, "useGoldSetItems").mockReturnValue({
      isLoading: false,
      error: null,
      data: mockGoldItems,
    } as unknown as UseGoldSetItemsReturn)
    vi.spyOn(evalApi, "useCreateGoldSetItem").mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as UseCreateGoldSetItemReturn)
    vi.spyOn(evalApi, "useDeleteGoldSetItem").mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as UseDeleteGoldSetItemReturn)

    render(<EvalPage />, { wrapper })
    await user.click(screen.getByRole("button", { name: /add to gold set/i }))
    expect(screen.getAllByText(/required/i).length).toBeGreaterThanOrEqual(1)
  })
})