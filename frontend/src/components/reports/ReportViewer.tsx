/**
 * ReportViewer - renders a complete report with all sections.
 *
 * INV-005: Sections render in fixed order matching backend.
 */

import { motion } from "motion/react"
import type { Report } from "@/lib/api/reports"
import { ReportSectionCard } from "./ReportSectionCard"

interface ReportViewerProps {
  report: Report
}

export function ReportViewer({ report }: ReportViewerProps) {
  const sortedSections = [...report.sections].sort((a, b) => a.order - b.order)

  return (
    <div className="space-y-5">
      {/* Report header */}
      <div className="pb-4 border-b border-foreground/5">
        <p className="text-xs font-medium tracking-[0.15em] text-muted-foreground/50 uppercase mb-1">
          Weekly Feedback Outlook
        </p>
        <h1 className="text-xl font-medium text-foreground">
          {formatDateRange(report.period_start, report.period_end)}
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Generated{" "}
          {report.generated_at ? formatRelativeTime(report.generated_at) : "—"}
        </p>
      </div>

      {/* Sections */}
      <div className="space-y-3">
        {sortedSections.map((section, i) => (
          <motion.div
            key={section.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05, duration: 0.2 }}
          >
            <ReportSectionCard
              section={section}
              periodStart={report.period_start}
              periodEnd={report.period_end}
            />
          </motion.div>
        ))}
      </div>
    </div>
  )
}

function formatDateRange(start: string, end: string): string {
  const startDate = new Date(start)
  const endDate = new Date(end)
  const options: Intl.DateTimeFormatOptions = { month: "short", day: "numeric" }
  return `${startDate.toLocaleDateString("en-US", options)} – ${endDate.toLocaleDateString("en-US", options)}, ${endDate.getFullYear()}`
}

function formatRelativeTime(isoString: string): string {
  const date = new Date(isoString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))

  if (diffHours < 1) return "just now"
  if (diffHours < 24) return `${diffHours}h ago`
  return date.toLocaleDateString()
}
