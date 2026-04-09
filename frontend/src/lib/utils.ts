import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" })

const UNITS: [Intl.RelativeTimeFormatUnit, number][] = [
  ["day", 86_400_000],
  ["hour", 3_600_000],
  ["minute", 60_000],
  ["second", 1_000],
]

export function formatRelativeTime(dateString: string): string {
  const diff = new Date(dateString).getTime() - Date.now()
  for (const [unit, ms] of UNITS) {
    if (Math.abs(diff) >= ms || unit === "second") {
      return rtf.format(Math.round(diff / ms), unit)
    }
  }
  return "just now"
}

const SOURCE_TYPE_LABELS: Record<string, string> = {
  csv_upload: "CSV Upload",
  webhook: "Webhook",
  rss_pull: "RSS Pull",
  api_pull: "API Pull",
}

export function sourceTypeLabel(type: string): string {
  return SOURCE_TYPE_LABELS[type] ?? type
}
