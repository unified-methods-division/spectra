import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

const SHORT_UNITS: [string, number][] = [
  ["d", 86_400_000],
  ["h", 3_600_000],
  ["m", 60_000],
]

export function formatRelativeTime(dateString: string): string {
  const elapsed = Date.now() - new Date(dateString).getTime()
  for (const [label, ms] of SHORT_UNITS) {
    if (elapsed >= ms) {
      return `${Math.floor(elapsed / ms)}${label} ago`
    }
  }
  return "just now"
}

type SourceTypeCopy = {
  label: string
  emptyStatus: string
  emptyTimestamp: string
}

const SOURCE_TYPE_COPY: Record<string, SourceTypeCopy> = {
  csv_upload: {
    label: "CSV Upload",
    emptyStatus: "Awaiting upload",
    emptyTimestamp: "No file uploaded",
  },
  webhook: {
    label: "Webhook",
    emptyStatus: "Awaiting events",
    emptyTimestamp: "No events received",
  },
  rss_pull: {
    label: "RSS Pull",
    emptyStatus: "Awaiting sync",
    emptyTimestamp: "No feeds pulled",
  },
  api_pull: {
    label: "API Pull",
    emptyStatus: "Awaiting connection",
    emptyTimestamp: "Not connected",
  },
}

const FALLBACK_COPY: SourceTypeCopy = {
  label: "Unknown",
  emptyStatus: "No data",
  emptyTimestamp: "No data yet",
}

export function sourceTypeCopy(type: string): SourceTypeCopy {
  return SOURCE_TYPE_COPY[type] ?? FALLBACK_COPY
}
