import { motion } from "motion/react"
import { useDriftDelta, type DriftEntry } from "@/lib/api/eval"
import { cn } from "@/lib/utils"

function deltaColor(delta: number | null) {
  if (delta == null) return "text-muted-foreground"
  if (delta > 0) return "text-emerald-600"
  if (delta < 0) return "text-red-500"
  return "text-muted-foreground"
}

function deltaLabel(delta: number | null) {
  if (delta == null) return "—"
  if (delta === 0) return "—"
  const pct = `${Math.abs(delta * 100).toFixed(1)}pp`
  if (delta > 0) return `↑ +${pct}`
  return `↓ -${pct}`
}

function DriftRow({ entry, index }: { entry: DriftEntry; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04 }}
      className="rounded-xl border border-foreground/5 bg-background/50 p-4"
    >
      <div className="flex items-center justify-between">
        <span className="font-mono text-xs tabular-nums text-muted-foreground/70">
          {entry.week_start} → {entry.week_end}
        </span>
        <span className={cn("font-mono text-xs tabular-nums", deltaColor(entry.delta))}>
          {deltaLabel(entry.delta)}
        </span>
      </div>
      <div className="mt-2 flex items-baseline justify-between">
        <span className="font-mono text-xl tabular-nums">
          {(entry.accuracy * 100).toFixed(1)}%
        </span>
        {entry.prev_accuracy != null && (
          <span className="font-mono text-xs tabular-nums text-muted-foreground/60">
            prev {(entry.prev_accuracy * 100).toFixed(1)}%
          </span>
        )}
      </div>
    </motion.div>
  )
}

export function EvalAccuracyPanel() {
  const { data, isLoading, error } = useDriftDelta(4)

  return (
    <div className="rounded-lg border border-foreground/6 bg-card/80 backdrop-blur-sm px-4 py-3">
      <p className="mb-3 text-[10px] font-semibold tracking-[0.2em] text-muted-foreground/50 uppercase">
        Accuracy drift
      </p>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : error ? (
        <p className="text-sm text-destructive">Couldn't load drift data.</p>
      ) : !data || data.length === 0 ? (
        <p className="text-sm text-muted-foreground">No drift data yet.</p>
      ) : (
        <div className="grid gap-2">
          {data.map((entry, i) => (
            <DriftRow key={entry.week_start} entry={entry} index={i} />
          ))}
        </div>
      )}
    </div>
  )
}