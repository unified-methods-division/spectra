import { useMemo, useState } from "react"
import { useSearchParams } from "react-router"
import { motion } from "motion/react"
import {
  useAcknowledgeAlert,
  useAlerts,
  useDashboardSummary,
  type DashboardSummaryPeriod,
} from "@/lib/api/trends"
import { DashboardHeader, KpiStrip, AlertsPanel, RecommendationsPanel } from "@/components/dashboard"
import { DisagreementRateCard } from "@/components/eval/disagreement-rate-card"
import { DriftDeltaChart } from "@/components/eval/drift-delta-chart"
import { EvalAccuracyPanel } from "@/components/eval/eval-accuracy-panel"

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
  const [searchParams] = useSearchParams()
  const period = useMemo(() => readDashboardPeriod(searchParams), [searchParams])
  const summary = useDashboardSummary(period)
  const alerts = useAlerts(period)
  const ack = useAcknowledgeAlert()

  const [headerPeriod, setHeaderPeriod] = useState<DashboardSummaryPeriod>(period)

  const isCustomIncomplete =
    period.kind === "custom" && (!period.periodStart || !period.periodEnd)

  return (
    <div className="mx-auto max-w-6xl">
      <DashboardHeader period={headerPeriod} onPeriodChange={setHeaderPeriod} />

      {isCustomIncomplete ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="rounded-lg border border-dashed border-foreground/10 bg-card/60 px-6 py-12 text-center"
        >
          <p className="text-sm text-muted-foreground">
            Choose start and end dates, then{" "}
            <span className="font-medium text-foreground">Apply range</span>.
          </p>
        </motion.div>
      ) : (
        <div className="space-y-6">
          <KpiStrip summary={summary.data} isLoading={summary.isLoading} />

          <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.2, delay: 0.15 }}
              className="space-y-6"
            >
              <AlertsPanel
                alerts={alerts.data}
                isLoading={alerts.isLoading}
                error={alerts.error}
                onAcknowledge={(id) => ack.mutate(id)}
                isAckPending={ack.isPending}
              />
              <RecommendationsPanel
                recommendations={summary.data?.top_recommendations}
                isLoading={summary.isLoading}
                error={summary.error}
              />
            </motion.div>

            <motion.aside
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.25, delay: 0.2 }}
              className="space-y-4"
            >
              <DisagreementRateCard />
              <DriftDeltaChart />
              <EvalAccuracyPanel />
            </motion.aside>
          </div>
        </div>
      )}
    </div>
  )
}