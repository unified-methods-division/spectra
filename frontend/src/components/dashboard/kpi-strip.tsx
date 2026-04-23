import { motion } from "motion/react"
import { Link } from "react-router"
import type { DashboardSummary } from "@/lib/api/trends"
import { cn } from "@/lib/utils"

interface KpiCardProps {
  label: string
  value: string
  delta: string | null
  deltaPositive: boolean | null
  delay: number
  className?: string
}

function KpiCard({ label, value, delta, deltaPositive, delay, className }: KpiCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.25, delay }}
      className={cn(
        "rounded-lg border border-foreground/6 bg-card/80 backdrop-blur-sm px-4 py-3",
        className,
      )}
    >
      <p className="text-[10px] font-semibold tracking-[0.2em] text-muted-foreground/50 uppercase">
        {label}
      </p>
      <div className="mt-1 flex items-baseline justify-between gap-2">
        <span className="font-mono text-2xl tabular-nums tracking-tight">{value}</span>
        {delta != null && (
          <span
            className={cn(
              "font-mono text-xs tabular-nums",
              deltaPositive === true && "text-emerald-600",
              deltaPositive === false && "text-red-500",
              deltaPositive === null && "text-muted-foreground",
            )}
          >
            {delta}
          </span>
        )}
      </div>
    </motion.div>
  )
}

interface KpiStripProps {
  summary: DashboardSummary | undefined
  isLoading: boolean
}

function KpiSkeleton() {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div
          key={i}
          className="rounded-lg border border-foreground/6 bg-card/80 px-4 py-3"
        >
          <div className="h-3 w-16 animate-pulse rounded bg-muted" />
          <div className="mt-2 h-7 w-20 animate-pulse rounded bg-muted" />
        </div>
      ))}
    </div>
  )
}

export function KpiStrip({ summary, isLoading }: KpiStripProps) {
  if (isLoading) return <KpiSkeleton />
  if (!summary) return null

  const fmtPct = (v: number) => `${(v * 100).toFixed(1)}%`
  const fmtDelta = (v: number | null, suffix: string = "pp") => {
    if (v == null) return null
    const pct = Math.abs(v * 100).toFixed(1)
    if (v > 0) return `+${pct}${suffix}`
    if (v < 0) return `−${pct}${suffix}`
    return `${pct}${suffix}`
  }
  const deltaPositive = (v: number | null): boolean | null => {
    if (v == null) return null
    return v > 0
  }

  const items: KpiCardProps[] = [
    {
      label: "Items",
      value: summary.total_items.toLocaleString(),
      delta: fmtDelta(summary.volume_change, "%"),
      deltaPositive: deltaPositive(summary.volume_change),
      delay: 0,
    },
    {
      label: "Volume delta",
      value: fmtDelta(summary.volume_change, "%") ?? "—",
      delta: null,
      deltaPositive: deltaPositive(summary.volume_change),
      delay: 0.04,
    },
    {
      label: "Accuracy",
      value: fmtPct(summary.accuracy),
      delta: fmtDelta(summary.accuracy_change),
      deltaPositive: deltaPositive(summary.accuracy_change),
      delay: 0.08,
    },
    {
      label: "Alerts",
      value: summary.alerts_count.toLocaleString(),
      delta: null,
      deltaPositive: null,
      delay: 0.12,
    },
  ]

  return (
    <div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {items.map((item) => (
          <KpiCard key={item.label} {...item} />
        ))}
      </div>
      <p className="mt-2 font-mono text-[11px] tabular-nums text-muted-foreground/50">
        {summary.period_start} → {summary.period_end}
        {summary.source === "report" && summary.report_id && (
          <span className="ml-2">
            (cached{" "}
            <Link
              to={`/reports/${summary.report_id}`}
              className="text-primary underline underline-offset-2 hover:text-primary/80"
            >
              report
            </Link>
            )
          </span>
        )}
      </p>
    </div>
  )
}