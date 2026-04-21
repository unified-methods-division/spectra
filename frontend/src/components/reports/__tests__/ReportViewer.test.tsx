/**
 * Tests for ReportViewer component.
 *
 * INV-005: Sections render in fixed order
 */

import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router"
import { ReportViewer } from "../ReportViewer"
import type { Report } from "@/lib/api/reports"

const mockReport: Report = {
  id: "test-report-id",
  report_type: "weekly_outlook",
  period_start: "2026-04-13",
  period_end: "2026-04-19",
  status: "ready",
  raw_data: null,
  polished_content: null,
  error_message: null,
  generated_at: "2026-04-21T06:00:00Z",
  created_at: "2026-04-21T05:00:00Z",
  sections: [
    {
      id: "section-3",
      section_type: "needs_attention",
      order: 3,
      raw_content: { negative_sentiment_pct: 0.32 },
      polished_content: {
        title: "Needs Attention",
        body: "Areas requiring focus.",
        key_points: [],
      },
    },
    {
      id: "section-1",
      section_type: "whats_changed",
      order: 1,
      raw_content: { volume_delta: 0.34 },
      polished_content: {
        title: "What's Changed",
        body: "Changes this week.",
        key_points: [],
      },
    },
    {
      id: "section-0",
      section_type: "exec_summary",
      order: 0,
      raw_content: { total_items: 247 },
      polished_content: {
        title: "Executive Summary",
        body: "Overview of this week.",
        key_points: ["247 items received"],
      },
    },
    {
      id: "section-2",
      section_type: "whats_working",
      order: 2,
      raw_content: { positive_sentiment_pct: 0.45 },
      polished_content: {
        title: "What's Working",
        body: "Positive trends.",
        key_points: [],
      },
    },
  ],
}

describe("ReportViewer", () => {
  it("renders all sections in order", () => {
    render(
      <MemoryRouter>
        <ReportViewer report={mockReport} />
      </MemoryRouter>,
    )

    const sectionHeadings = screen.getAllByRole("heading", { level: 2 })

    expect(sectionHeadings[0]).toHaveTextContent("Executive Summary")
    expect(sectionHeadings[1]).toHaveTextContent("What's Changed")
    expect(sectionHeadings[2]).toHaveTextContent("What's Working")
    expect(sectionHeadings[3]).toHaveTextContent("Needs Attention")
  })

  it("renders report header with date range", () => {
    render(
      <MemoryRouter>
        <ReportViewer report={mockReport} />
      </MemoryRouter>,
    )

    // "Weekly Feedback Outlook" is now in a small caps label
    expect(screen.getByText("Weekly Feedback Outlook")).toBeInTheDocument()
    // h1 contains the date range now
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(/2026/)
  })

  it("renders section key points", () => {
    render(
      <MemoryRouter>
        <ReportViewer report={mockReport} />
      </MemoryRouter>,
    )

    expect(screen.getByText("247 items received")).toBeInTheDocument()
  })
})
