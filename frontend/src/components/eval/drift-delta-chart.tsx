import { motion } from "motion/react"
import { useDriftDelta, type DriftEntry } from "@/lib/api/eval"
import { cn } from "@/lib/utils"

function deltaColor(delta: number | null) {
  if (delta == null) return "text-muted-foreground"
  if (delta > 0) return "text-emerald-600"
  if (delta < 0) return "text-red-500"
  return "text-muted-foreground"
}

function deltaArrow(delta: number | null) {
  if (delta == null || delta === 0) return "—"
  if (delta > 0) return `↑ +${(delta * 100).toFixed(1)}pp`
  return `↓ -${Math.abs(delta * 100).toFixed(1)}pp`
}

function BarRow({ entry, index }: { entry: DriftEntry; index: number }) {
  const widthPct = Math.max(Math.round(entry.accuracy * 100), 2)

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04 }}
      className="grid gap-1"
    >
      <div className="flex items-center justify-between">
        <span className="font-mono text-xs tabular-nums text-muted-foreground/70">
          {entry.week_start} → {entry.week_end}
        </span>
        <span
          className={cn(
            "font-mono text-xs tabular-nums",
            deltaColor(entry.delta),
          )}
        >
          {deltaArrow(entry.delta)}
        </span>
      </div>
      <div className="flex items-center gap-3">
        <div className="h-2 min-w-2 rounded-full bg-foreground/8">
          <div
            className="h-2 rounded-full bg-primary/70 transition-all"
            style={{ width: `${widthPct}%` }}
          />
        </div>
        <span className="font-mono text-sm tabular-nums">
          {(entry.accuracy * 100).toFixed(1)}%
        </span>
      </div>
    </motion.div>
  )
}

export function DriftDeltaChart() {
  const { data, isLoading, error } = useDriftDelta(4)

  return (
    <div className="rounded-lg border border-foreground/6 bg-card/80 backdrop-blur-sm px-4 py-3">
      <p className="mb-3 text-[10px] font-semibold tracking-[0.2em] text-muted-foreground/50 uppercase">
        Weekly accuracy trend
      </p>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : error ? (
        <p className="text-sm text-destructive">Couldn't load drift data.</p>
      ) : !data || data.length === 0 ? (
        <p className="text-sm text-muted-foreground">No drift data yet.</p>
      ) : (
        <div className="grid gap-3">
          {data.map((entry, i) => (
            <BarRow key={entry.week_start} entry={entry} index={i} />
          ))}
        </div>
      )}
    </div>
  )
}