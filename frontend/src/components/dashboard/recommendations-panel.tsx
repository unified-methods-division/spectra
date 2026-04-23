import { motion } from "motion/react"
import { Link } from "react-router"
import { cn } from "@/lib/utils"
import type { DashboardRecommendation } from "@/lib/api/trends"

function ScoreBar({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  return (
    <div className="flex items-center gap-2" aria-label={`Priority score ${pct}%`}>
      <div className="h-1.5 w-16 rounded-full bg-foreground/6">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="h-1.5 rounded-full bg-primary/60"
        />
      </div>
      <span className="font-mono text-[11px] tabular-nums text-muted-foreground/60">
        {pct}
      </span>
    </div>
  )
}

function RecRow({ rec, index }: { rec: DashboardRecommendation; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -6 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.15, delay: index * 0.03 }}
      className="rounded-md border border-foreground/5 bg-background/40 px-4 py-3"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <Link
            to={`/recommendations/${rec.id}`}
            className="text-sm font-medium text-foreground underline underline-offset-2 hover:text-primary"
          >
            {rec.title}
          </Link>
          <p className="mt-1 line-clamp-2 text-xs text-muted-foreground text-pretty">
            {rec.proposed_action}
          </p>
        </div>
        <div className="shrink-0 pt-0.5">
          <ScoreBar score={rec.priority_score} />
          <p
            className={cn(
              "mt-1 text-right font-mono text-[10px] tabular-nums uppercase tracking-wider",
              rec.status === "accepted"
                ? "text-emerald-600"
                : rec.status === "proposed"
                  ? "text-primary"
                  : "text-muted-foreground/50",
            )}
          >
            {rec.status}
          </p>
        </div>
      </div>
    </motion.div>
  )
}

function RecSkeleton() {
  return (
    <div className="grid gap-2">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="rounded-md border border-foreground/5 px-4 py-3">
          <div className="h-4 w-3/5 animate-pulse rounded bg-muted" />
          <div className="mt-2 h-3 w-full animate-pulse rounded bg-muted" />
        </div>
      ))}
    </div>
  )
}

interface RecommendationsPanelProps {
  recommendations: DashboardRecommendation[] | undefined
  isLoading: boolean
  error: unknown
}

export function RecommendationsPanel({ recommendations, isLoading, error }: RecommendationsPanelProps) {
  return (
    <div>
      <p className="mb-3 text-[10px] font-semibold tracking-[0.2em] text-muted-foreground/50 uppercase">
        Top recommendations
      </p>

      {isLoading ? (
        <RecSkeleton />
      ) : error || !recommendations ? (
        <p className="text-sm text-muted-foreground">—</p>
      ) : recommendations.length === 0 ? (
        <div className="rounded-md border border-dashed border-foreground/8 px-4 py-6 text-center">
          <p className="text-sm text-muted-foreground">No recommendations this period</p>
          <p className="mt-1 text-xs text-muted-foreground/60">
            Recommendations appear when feedback evidence supports proposed actions.
          </p>
        </div>
      ) : (
        <div className="grid gap-2">
          {recommendations.map((rec, i) => (
            <RecRow key={rec.id} rec={rec} index={i} />
          ))}
        </div>
      )}
    </div>
  )
}