import { useMemo, useRef } from "react"
import { Link, useSearchParams } from "react-router"
import { motion } from "motion/react"
import {
  useAcknowledgeAlert,
  useAlerts,
  useDashboardSummary,
  type DashboardSummaryPeriod,
} from "@/lib/api/trends"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

function explorerHrefFromAlert(alert: { metadata: { [k: string]: unknown } | null }) {
  const meta = alert.metadata ?? {}

  const filters =
    typeof meta.explorer_filters === "object" && meta.explorer_filters
      ? (meta.explorer_filters as Record<string, string>)
      : {}

  const periodStart = typeof meta.period_start === "string" ? meta.period_start : undefined
  const periodEnd = typeof meta.period_end === "string" ? meta.period_end : undefined

  const params = new URLSearchParams({
    v: "1",
    ...(periodStart ? { date_from: periodStart } : {}),
    ...(periodEnd ? { date_to: periodEnd } : {}),
    ...Object.fromEntries(Object.entries(filters).map(([k, v]) => [k, String(v)])),
  })

  return `/explorer?${params.toString()}`
}

function readDashboardPeriod(searchParams: URLSearchParams): DashboardSummaryPeriod {
  const raw = searchParams.get("period") ?? "this-week"
  if (raw === "last-week") return { kind: "last-week" }
  if (raw === "custom") {
    const periodStart = searchParams.get("period_start") ?? ""
    const periodEnd = searchParams.get("period_end") ?? ""
    return { kind: "custom", periodStart, periodEnd }
  }
  return { kind: "this-week" }
}

export function DashboardPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const period = useMemo(() => readDashboardPeriod(searchParams), [searchParams])
  const summary = useDashboardSummary(period)
  const alerts = useAlerts(period)
  const ack = useAcknowledgeAlert()

  const startRef = useRef<HTMLInputElement>(null)
  const endRef = useRef<HTMLInputElement>(null)
  const customInputKey = `${searchParams.get("period")}-${searchParams.get("period_start") ?? ""}-${searchParams.get("period_end") ?? ""}`

  const setPresetPeriod = (kind: "this-week" | "last-week") => {
    setSearchParams(
      (prev) => {
        const p = new URLSearchParams(prev)
        p.set("period", kind)
        p.delete("period_start")
        p.delete("period_end")
        return p
      },
      { replace: true },
    )
  }

  const showCustomPanel = () => {
    setSearchParams(
      (prev) => {
        const p = new URLSearchParams(prev)
        p.set("period", "custom")
        return p
      },
      { replace: true },
    )
  }

  const applyCustomRange = () => {
    const start = startRef.current?.value ?? ""
    const end = endRef.current?.value ?? ""
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

  return (
    <div>
      {/* Masthead */}
      <div className="relative">
        <div className="h-72">
          <img
            src="https://images.unsplash.com/photo-1663275162414-64dba99065a2?q=80&w=1600&auto=format&fit=crop"
            alt=""
            className="h-full w-full object-cover"
          />
          <div className="absolute inset-0 bg-linear-to-b from-background/60 via-background/20 to-background" />
        </div>
      </div>

      <div className="relative -mt-24 mx-auto max-w-3xl px-10">
        <div className="mb-8">
          <span className="text-xs font-medium tracking-[0.2em] text-foreground/80 uppercase">
            Dashboard
          </span>
          <h1 className="text-3xl font-normal tracking-tight text-foreground">
            What changed, and what needs attention
          </h1>
        </div>

        <div
          className="mb-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end"
          role="group"
          aria-label="Report period"
        >
          <div className="flex flex-wrap gap-2">
            {(
              [
                ["this-week", "This week"],
                ["last-week", "Last week"],
                ["custom", "Custom"],
              ] as const
            ).map(([key, label]) => {
              const active =
                key === "custom"
                  ? period.kind === "custom"
                  : period.kind === key
              return (
                <Button
                  key={key}
                  type="button"
                  size="sm"
                  variant={active ? "default" : "outline"}
                  className={cn("min-h-10", "active:scale-[0.98]")}
                  onClick={() => {
                    if (key === "custom") showCustomPanel()
                    else setPresetPeriod(key)
                  }}
                >
                  {label}
                </Button>
              )
            })}
          </div>
          {period.kind === "custom" && (
            <div className="flex flex-wrap items-end gap-2">
              <label className="grid gap-1">
                <span className="text-xs text-muted-foreground">Start</span>
                <input
                  key={`${customInputKey}-start`}
                  ref={startRef}
                  type="date"
                  name="period_start"
                  defaultValue={searchParams.get("period_start") ?? ""}
                  className={cn(
                    "h-10 min-w-40 rounded-md border border-foreground/10 bg-background px-3 text-base sm:text-sm",
                    "focus:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                  )}
                />
              </label>
              <label className="grid gap-1">
                <span className="text-xs text-muted-foreground">End</span>
                <input
                  key={`${customInputKey}-end`}
                  ref={endRef}
                  type="date"
                  name="period_end"
                  defaultValue={searchParams.get("period_end") ?? ""}
                  className={cn(
                    "h-10 min-w-40 rounded-md border border-foreground/10 bg-background px-3 text-base sm:text-sm",
                    "focus:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                  )}
                />
              </label>
              <Button
                type="button"
                size="sm"
                className="min-h-10"
                onClick={applyCustomRange}
              >
                Apply range
              </Button>
            </div>
          )}
        </div>

        <div className="grid gap-4">
          <div className="rounded-xl border border-foreground/8 bg-card/80 backdrop-blur-xl p-5">
            {period.kind === "custom" &&
            (!period.periodStart || !period.periodEnd) ? (
              <p className="text-sm text-muted-foreground">
                Choose start and end dates, then{" "}
                <span className="font-medium text-foreground">Apply range</span>.
              </p>
            ) : summary.isLoading ? (
              <p className="text-sm text-muted-foreground">Loading…</p>
            ) : summary.error ? (
              <p className="text-sm text-destructive">Couldn't load dashboard summary.</p>
            ) : summary.data ? (
              <>
                <p className="mb-3 text-xs text-muted-foreground font-mono tabular-nums">
                  {summary.data.period_start} → {summary.data.period_end}
                  {summary.data.source === "report" && summary.data.report_id ? (
                    <span className="ml-2 text-muted-foreground/70">
                      (cached report{" "}
                      <Link
                        to={`/reports/${summary.data.report_id}`}
                        className="text-primary underline underline-offset-2"
                      >
                        open
                      </Link>
                      )
                    </span>
                  ) : null}
                </p>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs font-medium tracking-[0.15em] text-muted-foreground/60 uppercase">
                      Items
                    </p>
                    <p className="mt-1 font-mono text-xl tabular-nums">
                      {summary.data.total_items.toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs font-medium tracking-[0.15em] text-muted-foreground/60 uppercase">
                      Alerts
                    </p>
                    <p className="mt-1 font-mono text-xl tabular-nums">
                      {summary.data.alerts_count.toLocaleString()}
                    </p>
                  </div>
                </div>
              </>
            ) : null}
          </div>

          <div className="rounded-xl border border-foreground/8 bg-card/80 backdrop-blur-xl p-5">
            <p className="mb-3 text-xs font-medium tracking-[0.15em] text-muted-foreground/50 uppercase">
              Top recommendations
            </p>
            {period.kind === "custom" &&
            (!period.periodStart || !period.periodEnd) ? (
              <p className="text-sm text-muted-foreground">
                Select a custom range to load recommendations.
              </p>
            ) : summary.isLoading ? (
              <p className="text-sm text-muted-foreground">Loading…</p>
            ) : summary.error || !summary.data ? (
              <p className="text-sm text-muted-foreground">—</p>
            ) : summary.data.top_recommendations.length === 0 ? (
              <p className="text-sm text-muted-foreground text-pretty">
                No recommendations for this period: none with status proposed/accepted
                that have evidence (feedback <code className="font-mono text-xs">received_at</code>{" "}
                in this range), and none created in-range without evidence. Use{" "}
                <code className="font-mono text-xs">seed_demo_recommendations</code>{" "}
                (with feedback in the same dates) for demo data.
              </p>
            ) : (
              <ul className="grid gap-2">
                {summary.data.top_recommendations.map((rec) => (
                  <li
                    key={rec.id}
                    className="rounded-xl border border-foreground/5 bg-background/50 p-4"
                  >
                    <Link
                      to={`/recommendations/${rec.id}`}
                      className="font-medium text-primary underline underline-offset-2 hover:text-primary/80"
                    >
                      {rec.title}
                    </Link>
                    <p className="mt-1 text-sm text-muted-foreground text-pretty line-clamp-2">
                      {rec.proposed_action}
                    </p>
                    <p className="mt-2 font-mono text-xs tabular-nums text-muted-foreground/80">
                      score {rec.priority_score} · {rec.status}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="rounded-xl border border-foreground/8 bg-card/80 backdrop-blur-xl p-5">
            <p className="mb-3 text-xs font-medium tracking-[0.15em] text-muted-foreground/50 uppercase">
              Alerts
            </p>

            {period.kind === "custom" &&
            (!period.periodStart || !period.periodEnd) ? (
              <p className="text-sm text-muted-foreground">
                Select a custom range to load alerts for that period.
              </p>
            ) : alerts.isLoading ? (
              <p className="text-sm text-muted-foreground">Loading…</p>
            ) : alerts.error ? (
              <p className="text-sm text-destructive">Couldn't load alerts.</p>
            ) : alerts.data && alerts.data.length === 0 ? (
              <p className="text-sm text-muted-foreground text-pretty">
                No alerts for this period. They are created when a{" "}
                <strong>weekly report</strong> is generated and week-over-week
                deltas hit thresholds (volume spike, negative sentiment rise, new
                themes). If there is no prior week of data,{" "}
                <code className="font-mono text-xs">delta</code> is empty → no
                alert rows.
              </p>
            ) : (
              <div className="grid gap-2">
                {alerts.data?.slice(0, 20).map((a) => (
                  <motion.div
                    key={a.id}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={cn(
                      "rounded-xl border border-foreground/5 bg-background/50 p-4",
                      a.acknowledged && "opacity-70",
                    )}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="font-medium truncate">{a.title}</p>
                        <p className="mt-1 text-sm text-muted-foreground text-pretty">
                          {a.description}
                        </p>
                        <div className="mt-2 flex items-center gap-3">
                          <Link
                            to={explorerHrefFromAlert(a)}
                            className="text-xs text-primary underline underline-offset-2 hover:text-primary/80"
                          >
                            View evidence
                          </Link>
                          {!a.acknowledged && (
                            <Button
                              size="sm"
                              variant="outline"
                              disabled={ack.isPending}
                              onClick={() => ack.mutate(a.id)}
                              className="h-8 px-2 text-xs"
                            >
                              Acknowledge
                            </Button>
                          )}
                        </div>
                      </div>
                      <span className="text-[10px] font-mono uppercase text-muted-foreground/60">
                        {a.severity}
                      </span>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

