/**
 * ReportSectionCard - collapsible section card with polish from make-interfaces-feel-better.
 *
 * Applies:
 * - Layered shadows instead of borders
 * - Concentric border radius
 * - text-wrap: balance on headings
 * - active:scale-[0.96] on buttons
 * - 40×40px minimum hit area
 * - Subtle exit animations
 * - tabular-nums on metrics
 * - No transition: all
 */

import { useState } from "react"
import { ArrowDown01Icon } from "@hugeicons/core-free-icons"
import { HugeiconsIcon } from "@hugeicons/react"
import type { ReportSection } from "@/lib/api/reports"
import { MetricLink } from "./MetricLink"
import { cn } from "@/lib/utils"

interface ReportSectionCardProps {
  section: ReportSection
  periodStart: string
  periodEnd: string
}

const SECTION_TITLES: Record<string, string> = {
  exec_summary: "Executive Summary",
  whats_changed: "What's Changed",
  whats_working: "What's Working",
  needs_attention: "Needs Attention",
  recommendations: "Top Recommendations",
  decisions_made: "Decisions This Week",
}

export function ReportSectionCard({
  section,
  periodStart,
  periodEnd,
}: ReportSectionCardProps) {
  const [isExpanded, setIsExpanded] = useState(true)

  const polished = section.polished_content
  const title =
    polished?.title ||
    SECTION_TITLES[section.section_type] ||
    section.section_type

  return (
    <div
      className={cn(
        "rounded-2xl bg-card",
        "shadow-[0_1px_2px_rgba(0,0,0,0.05),0_4px_8px_rgba(0,0,0,0.05)]",
        "dark:shadow-[0_1px_2px_rgba(0,0,0,0.15),0_4px_8px_rgba(0,0,0,0.15)]",
      )}
    >
      <button
        className={cn(
          "flex w-full items-center justify-between p-4 text-left",
          "min-h-[48px]",
          "rounded-2xl",
          "transition-colors duration-150",
          "hover:bg-muted/50",
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          "active:scale-[0.99]",
        )}
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
        aria-controls={`section-${section.id}`}
      >
        <h2 className="text-lg font-medium text-balance">{title}</h2>
        <span
          className={cn(
            "transition-transform duration-200",
            isExpanded && "rotate-180",
          )}
        >
          <HugeiconsIcon
            icon={ArrowDown01Icon}
            className="h-5 w-5 text-muted-foreground"
          />
        </span>
      </button>

      <div
        id={`section-${section.id}`}
        className={cn(
          "grid transition-all duration-200 ease-out",
          isExpanded
            ? "grid-rows-[1fr] opacity-100"
            : "grid-rows-[0fr] opacity-0",
        )}
      >
        <div className="overflow-hidden">
          <div className="px-4 pb-4">
            {polished ? (
              <>
                <p className="mb-3 text-muted-foreground text-pretty">
                  {polished.body}
                </p>
                {polished.key_points.length > 0 && (
                  <ul className="space-y-2">
                    {polished.key_points.map((point, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-muted-foreground">•</span>
                        <MetricLink
                          text={point}
                          sectionType={section.section_type}
                          rawContent={section.raw_content}
                          periodStart={periodStart}
                          periodEnd={periodEnd}
                        />
                      </li>
                    ))}
                  </ul>
                )}
              </>
            ) : (
              <p className="text-muted-foreground">No content available.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
