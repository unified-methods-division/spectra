/**
 * ReportStatusBadge - visual indicator for report generation status.
 */

import { cn } from "@/lib/utils"
import type { Report } from "@/lib/api/reports"

interface ReportStatusBadgeProps {
  status: Report["status"]
}

const STATUS_CONFIG = {
  pending: {
    label: "Pending",
    className: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
  },
  generating: {
    label: "Generating…",
    className: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  },
  ready: {
    label: "Ready",
    className: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  },
  failed: {
    label: "Failed",
    className: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  },
}

export function ReportStatusBadge({ status }: ReportStatusBadgeProps) {
  const config = STATUS_CONFIG[status]

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        config.className,
      )}
    >
      {config.label}
    </span>
  )
}
