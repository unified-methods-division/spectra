import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { MemoryRouter, Routes, Route, useLocation } from "react-router"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { SmartRedirect } from "@/components/smart-redirect"
import * as sourcesHook from "@/hooks/use-sources"
import type { Source } from "@/types/api"

type UseSourcesReturn = ReturnType<typeof sourcesHook.useSources>

const mockSource: Source = {
  id: "1",
  name: "Test Source",
  source_type: "csv_upload",
  config: null,
  last_synced_at: null,
  created_at: "2026-01-01T00:00:00Z",
}

function makeClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
}

function LocationDisplay() {
  const location = useLocation()
  return <div data-testid="location">{location.pathname}</div>
}

function makeWrapper() {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    const qc = makeClient()
    return (
      <QueryClientProvider client={qc}>
        <MemoryRouter initialEntries={["/"]}>
          <Routes>
            <Route path="/" element={children} />
            <Route path="/sources" element={<LocationDisplay />} />
            <Route path="/dashboard" element={<LocationDisplay />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    )
  }
}

function asMock(partial: Partial<UseSourcesReturn>): UseSourcesReturn {
  return partial as UseSourcesReturn
}

describe("SmartRedirect", () => {
  it("renders nothing while sources are loading", () => {
    vi.spyOn(sourcesHook, "useSources").mockReturnValue(
      asMock({ isLoading: true, data: undefined })
    )

    const { container } = render(<SmartRedirect />, { wrapper: makeWrapper() })
    expect(container.textContent).toBe("")
  })

  it("redirects to /sources when no sources exist", () => {
    vi.spyOn(sourcesHook, "useSources").mockReturnValue(
      asMock({ isLoading: false, data: [] })
    )

    render(<SmartRedirect />, { wrapper: makeWrapper() })
    expect(screen.getByTestId("location").textContent).toBe("/sources")
  })

  it("redirects to /dashboard when sources exist", () => {
    vi.spyOn(sourcesHook, "useSources").mockReturnValue(
      asMock({ isLoading: false, data: [mockSource] })
    )

    render(<SmartRedirect />, { wrapper: makeWrapper() })
    expect(screen.getByTestId("location").textContent).toBe("/dashboard")
  })

  it("uses the useSources hook for data fetching", () => {
    const spy = vi.spyOn(sourcesHook, "useSources").mockReturnValue(
      asMock({ isLoading: true, data: undefined })
    )

    render(<SmartRedirect />, { wrapper: makeWrapper() })
    expect(spy).toHaveBeenCalled()
  })
})