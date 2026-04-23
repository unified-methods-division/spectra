import { useRef } from "react"
import { motion } from "motion/react"
import { useSearchParams } from "react-router"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { DashboardSummaryPeriod } from "@/lib/api/trends"

const PERIOD_OPTIONS = [
  { key: "this-week", label: "This week" },
  { key: "last-week", label: "Last week" },
  { key: "custom", label: "Custom" },
] as const

function SegmentedControl({
  value,
  onChange,
}: {
  value: string
  onChange: (key: "this-week" | "last-week" | "custom") => void
}) {
  return (
    <div
      className="inline-flex rounded-lg border border-foreground/8 bg-muted/60 p-0.5"
      role="group"
      aria-label="Report period"
    >
      {PERIOD_OPTIONS.map((opt, i) => {
        const active = opt.key === "custom" ? value === "custom" : value === opt.key
        return (
          <button
            key={opt.key}
            type="button"
            onClick={() => onChange(opt.key)}
            className={cn(
              "relative rounded-md px-3 py-1.5 text-xs font-medium tracking-wide transition-colors",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
              active
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground/80",
              i === 0 && "rounded-l-md",
              i === PERIOD_OPTIONS.length - 1 && "rounded-r-md",
            )}
          >
            {opt.label}
          </button>
        )
      })}
    </div>
  )
}

function CustomRangeInputs({
  searchParams,
  onApply,
}: {
  searchParams: URLSearchParams
  onApply: (start: string, end: string) => void
}) {
  const startRef = useRef<HTMLInputElement>(null)
  const endRef = useRef<HTMLInputElement>(null)
  const key = `${searchParams.get("period_start") ?? ""}-${searchParams.get("period_end") ?? ""}`

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: "auto" }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.15 }}
      className="flex flex-wrap items-end gap-2 overflow-hidden"
    >
      <label className="grid gap-0.5">
        <span className="text-[10px] font-medium tracking-wider text-muted-foreground/60 uppercase">
          Start
        </span>
        <input
          key={`${key}-start`}
          ref={startRef}
          type="date"
          name="period_start"
          defaultValue={searchParams.get("period_start") ?? ""}
          className={cn(
            "h-8 min-w-36 rounded-md border border-foreground/10 bg-background px-2.5 font-mono text-xs tabular-nums",
            "focus:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          )}
        />
      </label>
      <label className="grid gap-0.5">
        <span className="text-[10px] font-medium tracking-wider text-muted-foreground/60 uppercase">
          End
        </span>
        <input
          key={`${key}-end`}
          ref={endRef}
          type="date"
          name="period_end"
          defaultValue={searchParams.get("period_end") ?? ""}
          className={cn(
            "h-8 min-w-36 rounded-md border border-foreground/10 bg-background px-2.5 font-mono text-xs tabular-nums",
            "focus:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          )}
        />
      </label>
      <Button
        type="button"
        size="sm"
        className="h-8 px-3 text-xs"
        onClick={() => onApply(startRef.current?.value ?? "", endRef.current?.value ?? "")}
      >
        Apply
      </Button>
    </motion.div>
  )
}

export function DashboardHeader({
  period,
  onPeriodChange,
}: {
  period: DashboardSummaryPeriod
  onPeriodChange: (p: DashboardSummaryPeriod) => void
}) {
  const [searchParams, setSearchParams] = useSearchParams()

  const handlePeriodKey = (key: "this-week" | "last-week" | "custom") => {
    if (key === "custom") {
      onPeriodChange({ kind: "custom", periodStart: "", periodEnd: "" })
      setSearchParams(
        (prev) => {
          const p = new URLSearchParams(prev)
          p.set("period", "custom")
          return p
        },
        { replace: true },
      )
    } else {
      onPeriodChange({ kind: key })
      setSearchParams(
        (prev) => {
          const p = new URLSearchParams(prev)
          p.set("period", key)
          p.delete("period_start")
          p.delete("period_end")
          return p
        },
        { replace: true },
      )
    }
  }

  const handleCustomApply = (start: string, end: string) => {
    onPeriodChange({ kind: "custom", periodStart: start, periodEnd: end })
    setSearchParams(
      (prev) => {
        const p = new URLSearchParams(prev)
        p.set("period", "custom")
        if (start) p.set("period_start", start)
        if (end) p.set("period_end", end)
        return p
      },
      { replace: true },
    )
  }

  const currentKey = period.kind

  return (
    <div className="mb-6">
      <motion.div
        initial={{ opacity: 0, y: -4 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
        className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"
      >
        <div>
          <span className="text-[11px] font-semibold tracking-[0.25em] text-muted-foreground/50 uppercase">
            Dashboard
          </span>
          <h1 className="mt-1 text-2xl font-normal tracking-tight text-foreground">
            What changed, and what needs attention
          </h1>
        </div>
        <SegmentedControl value={currentKey} onChange={handlePeriodKey} />
      </motion.div>

      {period.kind === "custom" && (
        <div className="mt-3">
          <CustomRangeInputs searchParams={searchParams} onApply={handleCustomApply} />
        </div>
      )}
    </div>
  )
}