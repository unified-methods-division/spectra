import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router"
import App from "@/App"

function renderWithRouter(initialEntry: string = "/explorer") {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <App />
    </MemoryRouter>
  )
}

const navGroups = [
  {
    label: "Ingest",
    items: [
      { label: "Sources", href: "/sources" },
    ],
  },
  {
    label: "Explore",
    items: [
      { label: "Explorer", href: "/explorer" },
    ],
  },
  {
    label: "Analyze",
    items: [
      { label: "Themes", href: "/themes" },
      { label: "Reports", href: "/reports" },
    ],
  },
  {
    label: "Act",
    items: [
      { label: "Dashboard", href: "/dashboard" },
      { label: "Eval", href: "/eval" },
    ],
  },
]

describe("App sidebar", () => {
  it("renders all section labels", () => {
    renderWithRouter("/explorer")

    for (const group of navGroups) {
      expect(screen.getByText(group.label, { selector: "span" })).toBeInTheDocument()
    }
  })

  it("renders all nav items", () => {
    renderWithRouter("/explorer")

    for (const group of navGroups) {
      for (const item of group.items) {
        expect(screen.getByText(item.label)).toBeInTheDocument()
      }
    }
  })

  it("marks the active nav item with bold styling", () => {
    renderWithRouter("/explorer")

    const explorerLink = screen.getByText("Explorer").closest("a")
    expect(explorerLink).toHaveClass("font-medium")
  })

  it("section labels are not links", () => {
    renderWithRouter("/explorer")

    for (const group of navGroups) {
      const label = screen.getByText(group.label, { selector: "span" })
      expect(label.tagName).toBe("SPAN")
    }
  })

  it("nav items are indented with pl-3", () => {
    renderWithRouter("/explorer")

    for (const group of navGroups) {
      for (const item of group.items) {
        const link = screen.getByText(item.label).closest("a")
        expect(link).toHaveClass("pl-3")
      }
    }
  })

  it("nav items have minimum 40px hit area (py-2.5)", () => {
    renderWithRouter("/explorer")

    const sourcesLink = screen.getByText("Sources").closest("a")
    expect(sourcesLink).toHaveClass("py-2.5")
  })

  it("nav items have scale on press", () => {
    renderWithRouter("/explorer")

    const sourcesLink = screen.getByText("Sources").closest("a")
    expect(sourcesLink).toHaveClass("active:scale-[0.96]")
  })

  it("nav items use specific transition properties", () => {
    renderWithRouter("/explorer")

    const sourcesLink = screen.getByText("Sources").closest("a")
    expect(sourcesLink?.className).toMatch(/transition-\[color/)
    expect(sourcesLink?.className).toMatch(/transform\]/)
  })

  it("renders the logo section", () => {
    renderWithRouter("/explorer")

    expect(screen.getByText("Spectra")).toBeInTheDocument()
  })

  it("section labels have muted-foreground/40 styling", () => {
    renderWithRouter("/explorer")

    for (const group of navGroups) {
      const label = screen.getByText(group.label, { selector: "span" })
      expect(label.className).toContain("text-muted-foreground/40")
    }
  })

  it("first group starts with mt-8", () => {
    renderWithRouter("/explorer")

    const firstGroup = screen.getByText("Ingest", { selector: "span" }).parentElement
    expect(firstGroup).toHaveClass("mt-8")
  })

  it("subsequent groups have mt-6 spacing", () => {
    renderWithRouter("/explorer")

    const secondGroup = screen.getByText("Explore", { selector: "span" }).parentElement
    expect(secondGroup).toHaveClass("mt-6")
  })
})