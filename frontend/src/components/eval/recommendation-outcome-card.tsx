import { motion } from "motion/react"
import { useRecommendationOutcome, type RecommendationOutcome } from "@/lib/api/eval"
import { cn } from "@/lib/utils"

function OutcomeRow({
  outcome,
  index,
}: {
  outcome: RecommendationOutcome
  index: number
}) {
  const deltaPct = (outcome.delta * 100).toFixed(1)

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04 }}
      className="rounded-xl border border-foreground/5 bg-background/50 p-4"
    >
      <p className="text-xs font-medium tracking-[0.15em] text-muted-foreground/60 uppercase">
        {outcome.metric_name}
      </p>
      <div className="mt-1 flex items-baseline gap-2">
        <span className="font-mono text-xs tabular-nums text-muted-foreground/70">
          {outcome.baseline_value.toFixed(2)}
        </span>
        <span className="text-muted-foreground/40">→</span>
        <span className="font-mono text-sm tabular-nums">
          {outcome.current_value.toFixed(2)}
        </span>
        <span
          className={cn(
            "font-mono text-xs tabular-nums",
            outcome.delta > 0
              ? "text-emerald-600"
              : outcome.delta < 0
                ? "text-red-500"
                : "text-muted-foreground",
          )}
        >
          {outcome.delta > 0 ? "+" : ""}
          {deltaPct}pp
        </span>
      </div>
      {outcome.interpretation && (
        <p className="mt-1 text-xs text-muted-foreground text-pretty">
          {outcome.interpretation}
        </p>
      )}
    </motion.div>
  )
}

export function RecommendationOutcomeCard({
  recommendationId,
}: {
  recommendationId: string | undefined
}) {
  const { data, isLoading, error } = useRecommendationOutcome(recommendationId)

  if (!recommendationId) return null

  return (
    <div className="rounded-xl border border-foreground/8 bg-card/80 backdrop-blur-xl p-5">
      <p className="mb-3 text-xs font-medium tracking-[0.15em] text-muted-foreground/50 uppercase">
        Outcome metrics
      </p>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : error ? (
        <p className="text-sm text-destructive">
          Couldn't load outcome metrics.
        </p>
      ) : !data || data.length === 0 ? (
        <p className="text-sm text-muted-foreground">No outcome data yet.</p>
      ) : (
        <div className="grid gap-2">
          {data.map((outcome, i) => (
            <OutcomeRow key={outcome.id} outcome={outcome} index={i} />
          ))}
        </div>
      )}
    </div>
  )
}