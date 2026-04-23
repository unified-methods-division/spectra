import { useMemo, useState } from "react"
import { Link, useParams } from "react-router"
import { motion } from "motion/react"
import {
  useDecideRecommendation,
  useRecommendation,
  type RecommendationStatus,
} from "@/lib/api/recommendations"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

function explorerHref(opts: {
  periodStart?: string
  periodEnd?: string
  filters?: Record<string, string>
}) {
  const params = new URLSearchParams({
    v: "1",
    ...(opts.periodStart ? { date_from: opts.periodStart } : {}),
    ...(opts.periodEnd ? { date_to: opts.periodEnd } : {}),
    ...(opts.filters ?? {}),
  })
  return `/explorer?${params.toString()}`
}

const DECISION_OPTIONS: Array<{
  value: Exclude<RecommendationStatus, "proposed">
  label: string
}> = [
  { value: "accepted", label: "Accept" },
  { value: "dismissed", label: "Dismiss" },
  { value: "needs_more_evidence", label: "Needs more evidence" },
]

export function RecommendationDetailPage() {
  const { recommendationId } = useParams<{ recommendationId: string }>()
  const { data: rec, isLoading, error } = useRecommendation(recommendationId)
  const decide = useDecideRecommendation()
  const [owner, setOwner] = useState("")

  const primaryTheme = useMemo(() => rec?.themes?.[0], [rec?.themes])

  const onDecide = (status: Exclude<RecommendationStatus, "proposed">) => {
    if (!rec) return
    decide.mutate({
      recommendationId: rec.id,
      status,
      decision_owner: owner.trim() ? owner.trim() : undefined,
    })
  }

  return (
    <div>
      <div className="relative">
        <div className="h-56">
          <img
            src="https://images.unsplash.com/photo-1519681393784-d120267933ba?q=80&w=1600&auto=format&fit=crop"
            alt=""
            className="h-full w-full object-cover"
          />
          <div className="absolute inset-0 bg-linear-to-b from-background/60 via-background/20 to-background" />
        </div>
      </div>

      <div className="relative -mt-20 mx-auto max-w-3xl px-10">
        <nav className="mb-5 text-sm">
          <Link
            to="/reports"
            className="text-foreground/60 hover:text-foreground transition-colors"
          >
            Reports
          </Link>
          <span className="text-foreground/30 mx-2">/</span>
          <span className="text-foreground/80">Recommendation</span>
        </nav>

        <div className="rounded-xl border border-foreground/8 bg-card/80 backdrop-blur-xl p-5">
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : error || !rec ? (
            <p className="text-sm text-destructive">Couldn't load recommendation.</p>
          ) : (
            <div className="grid gap-5">
              <div>
                <h1 className="text-2xl font-medium tracking-tight text-balance">
                  {rec.title}
                </h1>
                <p className="mt-2 text-sm text-muted-foreground text-pretty">
                  {rec.problem_statement}
                </p>
              </div>

              <div className="rounded-xl border border-foreground/5 bg-background/50 p-4">
                <p className="text-xs font-medium tracking-[0.15em] text-muted-foreground/60 uppercase">
                  Proposed action
                </p>
                <p className="mt-2 text-sm text-pretty">{rec.proposed_action}</p>
              </div>

              <div className="grid gap-3">
                <p className="text-xs font-medium tracking-[0.15em] text-muted-foreground/60 uppercase">
                  Decision
                </p>

                <div className="flex flex-wrap gap-2">
                  {DECISION_OPTIONS.map((opt) => (
                    <Button
                      key={opt.value}
                      variant={rec.status === opt.value ? "default" : "outline"}
                      size="sm"
                      disabled={decide.isPending}
                      onClick={() => onDecide(opt.value)}
                      className={cn("min-h-[40px]", "active:scale-[0.96]")}
                    >
                      {opt.label}
                    </Button>
                  ))}
                </div>

                <label className="grid gap-1">
                  <span className="text-xs text-muted-foreground">
                    Owner (optional)
                  </span>
                  <input
                    value={owner}
                    onChange={(e) => setOwner(e.target.value)}
                    placeholder="alex…"
                    className={cn(
                      "h-10 rounded-md border border-foreground/10 bg-background px-3 text-sm",
                      "focus:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                    )}
                    autoComplete="name"
                  />
                </label>

                {decide.isError && (
                  <p className="text-sm text-destructive">
                    Failed to save decision.
                  </p>
                )}
                {decide.isSuccess && (
                  <p className="text-sm text-muted-foreground" aria-live="polite">
                    Saved.
                  </p>
                )}
              </div>

              <div className="grid gap-2">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-medium tracking-[0.15em] text-muted-foreground/60 uppercase">
                    Evidence
                  </p>
                  <Link
                    to={explorerHref({
                      filters: primaryTheme ? { theme: primaryTheme } : {},
                    })}
                    className="text-xs text-primary underline underline-offset-2 hover:text-primary/80"
                  >
                    View in Explorer
                  </Link>
                </div>

                {rec.evidence.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No evidence linked yet.
                  </p>
                ) : (
                  <div className="grid gap-2">
                    {rec.evidence.map((e, i) => (
                      <motion.div
                        key={e.id}
                        initial={{ opacity: 0, y: 6 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.03 }}
                        className="rounded-xl border border-foreground/5 bg-background/50 p-4"
                      >
                        <p className="text-sm text-muted-foreground text-pretty">
                          {e.selection_reason ?? "Evidence item"}
                        </p>
                        <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted-foreground/70 font-mono">
                          {e.feedback_item_urgency && (
                            <span>urgency={e.feedback_item_urgency}</span>
                          )}
                          {e.feedback_item_sentiment && (
                            <span>sentiment={e.feedback_item_sentiment}</span>
                          )}
                          {e.feedback_item_themes?.slice(0, 3).map((t) => (
                            <Link
                              key={t}
                              to={explorerHref({ filters: { theme: t } })}
                              className="underline underline-offset-2 hover:text-foreground"
                            >
                              theme={t}
                            </Link>
                          ))}
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

