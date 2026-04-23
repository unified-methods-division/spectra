import { motion, AnimatePresence } from "motion/react"
import { Link } from "react-router"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { Alert } from "@/lib/api/trends"

const SEVERITY_STYLES: Record<Alert["severity"], { border: string; dot: string }> = {
  critical: { border: "border-l-destructive", dot: "bg-destructive" },
  warning: { border: "border-l-warning", dot: "bg-warning" },
  info: { border: "border-l-info", dot: "bg-info" },
}

const SEVERITY_ORDER: Record<Alert["severity"], number> = {
  critical: 0,
  warning: 1,
  info: 2,
}

function AlertRow({
  alert,
  index,
  onAcknowledge,
  isAckPending,
}: {
  alert: Alert
  index: number
  onAcknowledge: (id: string) => void
  isAckPending: boolean
}) {
  const style = SEVERITY_STYLES[alert.severity]

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 8, transition: { duration: 0.12 } }}
      transition={{ duration: 0.18, delay: index * 0.03 }}
      className={cn(
        "rounded-md border border-foreground/5 border-l-3 bg-background/40 px-4 py-3",
        style.border,
        alert.acknowledged && "opacity-50",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className={cn("inline-block size-1.5 shrink-0 rounded-full", style.dot)} />
            <p className={cn("text-sm font-medium truncate", !alert.acknowledged && "text-foreground")}>
              {alert.title}
            </p>
          </div>
          <p className="mt-1 line-clamp-2 text-xs text-muted-foreground text-pretty pl-3.5">
            {alert.description}
          </p>
          <div className="mt-2 flex items-center gap-3 pl-3.5">
            <Link
              to={explorerHref(alert)}
              className="font-mono text-[11px] text-primary underline underline-offset-2 hover:text-primary/80"
            >
              View evidence
            </Link>
            {!alert.acknowledged && (
              <Button
                size="xs"
                variant="ghost"
                disabled={isAckPending}
                onClick={() => onAcknowledge(alert.id)}
                className="h-5 px-1.5 font-mono text-[11px] text-muted-foreground hover:text-foreground"
              >
                Ack
              </Button>
            )}
          </div>
        </div>
        <span className="shrink-0 font-mono text-[10px] tabular-nums uppercase tracking-wider text-muted-foreground/40">
          {alert.severity}
        </span>
      </div>
    </motion.div>
  )
}

function explorerHref(alert: { metadata: { [k: string]: unknown } | null }) {
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

function AlertSkeleton() {
  return (
    <div className="grid gap-2">
      {Array.from({ length: 3 }).map((_, i) => (
        <div
          key={i}
          className="rounded-md border border-foreground/5 border-l-3 border-l-muted px-4 py-3"
        >
          <div className="h-4 w-3/4 animate-pulse rounded bg-muted" />
          <div className="mt-2 h-3 w-full animate-pulse rounded bg-muted" />
        </div>
      ))}
    </div>
  )
}

interface AlertsPanelProps {
  alerts: Alert[] | undefined
  isLoading: boolean
  error: unknown
  onAcknowledge: (id: string) => void
  isAckPending: boolean
}

export function AlertsPanel({ alerts, isLoading, error, onAcknowledge, isAckPending }: AlertsPanelProps) {
  return (
    <div>
      <p className="mb-3 text-[10px] font-semibold tracking-[0.2em] text-muted-foreground/50 uppercase">
        Alerts
      </p>

      {isLoading ? (
        <AlertSkeleton />
      ) : error ? (
        <p className="text-sm text-destructive">Couldn't load alerts.</p>
      ) : !alerts || alerts.length === 0 ? (
        <div className="rounded-md border border-dashed border-foreground/8 px-4 py-8 text-center">
          <p className="text-sm text-muted-foreground">No alerts this period</p>
          <p className="mt-1 text-xs text-muted-foreground/60">
            Alerts fire when weekly reports detect threshold deltas in volume, sentiment, or new themes.
          </p>
        </div>
      ) : (
        <AnimatePresence mode="popLayout">
          <div className="grid gap-2">
            {[...alerts]
              .sort((a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity])
              .slice(0, 20)
              .map((a, i) => (
                <AlertRow
                  key={a.id}
                  alert={a}
                  index={i}
                  onAcknowledge={onAcknowledge}
                  isAckPending={isAckPending}
                />
              ))}
          </div>
        </AnimatePresence>
      )}
    </div>
  )
}