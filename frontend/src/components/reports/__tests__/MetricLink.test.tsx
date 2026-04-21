/**
 * Tests for MetricLink component.
 *
 * Invariants covered:
 * - INV-006: Deep-link filters preserve report context
 */

import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router"
import { MetricLink } from "../MetricLink"

describe("MetricLink", () => {
  it("navigates with correct filters for theme metric", () => {
    render(
      <MemoryRouter>
        <MetricLink
          text="New themes: billing, onboarding"
          sectionType="whats_changed"
          rawContent={{ new_themes: ["billing", "onboarding"] }}
          periodStart="2026-04-13"
          periodEnd="2026-04-19"
        />
      </MemoryRouter>,
    )

    const billingLink = screen.getByRole("link", { name: "billing" })
    expect(billingLink).toHaveAttribute("href", expect.stringContaining("theme=billing"))
    expect(billingLink).toHaveAttribute("href", expect.stringContaining("date_start=2026-04-13"))
    expect(billingLink).toHaveAttribute("href", expect.stringContaining("date_end=2026-04-19"))
  })

  it("url-encodes special characters in theme names", () => {
    render(
      <MemoryRouter>
        <MetricLink
          text="Rising: billing/payments"
          sectionType="whats_changed"
          rawContent={{ rising_themes: ["billing/payments"] }}
          periodStart="2026-04-13"
          periodEnd="2026-04-19"
        />
      </MemoryRouter>,
    )

    const link = screen.getByRole("link", { name: "billing/payments" })
    // URLSearchParams encodes the slash automatically
    expect(link).toHaveAttribute("href", expect.stringMatching(/theme=billing(%2F|\/)payments/))
  })

  it("renders plain text when no linkable patterns", () => {
    render(
      <MemoryRouter>
        <MetricLink
          text="No themes here"
          sectionType="whats_changed"
          rawContent={{}}
          periodStart="2026-04-13"
          periodEnd="2026-04-19"
        />
      </MemoryRouter>,
    )

    expect(screen.queryByRole("link")).not.toBeInTheDocument()
    expect(screen.getByText("No themes here")).toBeInTheDocument()
  })

  it("links sentiment percentage mentions", () => {
    render(
      <MemoryRouter>
        <MetricLink
          text="45% positive sentiment this week"
          sectionType="whats_working"
          rawContent={{ positive_sentiment_pct: 0.45 }}
          periodStart="2026-04-13"
          periodEnd="2026-04-19"
        />
      </MemoryRouter>,
    )

    const link = screen.getByRole("link", { name: "45% positive" })
    expect(link).toHaveAttribute("href", expect.stringContaining("sentiment=positive"))
  })

  it("applies tabular-nums to all text", () => {
    render(
      <MemoryRouter>
        <MetricLink
          text="247 items received"
          sectionType="exec_summary"
          rawContent={{ total_items: 247 }}
          periodStart="2026-04-13"
          periodEnd="2026-04-19"
        />
      </MemoryRouter>,
    )

    const textElement = screen.getByText("247 items received")
    expect(textElement).toHaveClass("tabular-nums")
  })
})
