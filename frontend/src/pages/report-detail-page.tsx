/**
 * ReportDetailPage - view a single report with all sections.
 */

import { motion } from "motion/react"
import { useParams, Link } from "react-router"
import { useReport, useRetryReport } from "@/lib/api/reports"
import { ReportViewer, ReportStatusBadge } from "@/components/reports"
import { Button } from "@/components/ui/button"
import { HugeiconsIcon } from "@hugeicons/react"
import { Loading03Icon, Copy01Icon, RefreshIcon, AlertCircleIcon } from "@hugeicons/core-free-icons"
import { cn } from "@/lib/utils"

export function ReportDetailPage() {
  const { reportId } = useParams<{ reportId: string }>()
  const { data: report, isLoading, error } = useReport(reportId)
  const retryReport = useRetryReport()

  const handleCopyLink = () => {
    navigator.clipboard.writeText(window.location.href)
  }

  const handleRetry = () => {
    if (reportId) {
      retryReport.mutate(reportId)
    }
  }

  return (
    <div>
      {/* Masthead */}
      <div className="relative">
        <div className="h-72">
          <img
            src="https://images.unsplash.com/photo-1688494930045-328d0f95efe9?q=80&w=2235&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
            alt=""
            className="h-full w-full object-cover"
          />
          <div className="absolute inset-0 bg-linear-to-b from-background/40 via-background/10 to-background" />
        </div>
      </div>

      {/* Content */}
      <div className="relative -mt-24 mx-auto max-w-3xl px-10">
        {/* Breadcrumb + Actions */}
        <div className="flex items-center justify-between mb-5">
          <nav className="text-sm">
            <Link
              to="/reports"
              className="text-foreground/60 hover:text-foreground transition-colors"
            >
              Reports
            </Link>
            <span className="text-foreground/30 mx-2">/</span>
            <span className="text-foreground/80">
              {report
                ? formatDateRange(report.period_start, report.period_end)
                : "Loading…"}
            </span>
          </nav>
          {report?.status === "ready" && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopyLink}
              className="transition-transform duration-150 active:scale-[0.96]"
            >
              <HugeiconsIcon
                icon={Copy01Icon}
                data-icon="inline-start"
                strokeWidth={2}
              />
              Copy link
            </Button>
          )}
        </div>

        {/* Panel */}
        <div className="rounded-xl border border-foreground/8 bg-card/80 backdrop-blur-xl p-5">
          {/* Loading */}
          {isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3, duration: 0.2 }}
              className="flex flex-col items-center gap-4 py-20"
            >
              <div className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <motion.span
                    key={i}
                    className="size-1.5 rounded-full bg-primary/40"
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{ duration: 2, repeat: Infinity, delay: i * 0.3 }}
                  />
                ))}
              </div>
              <p className="text-sm text-muted-foreground">Loading report…</p>
            </motion.div>
          )}

          {/* Error */}
          {error && !isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center gap-2 py-16"
            >
              <HugeiconsIcon
                icon={AlertCircleIcon}
                className="size-8 text-destructive/50"
                strokeWidth={1.5}
              />
              <p className="text-sm text-destructive">Failed to load report</p>
              <Link to="/reports">
                <Button variant="outline" size="sm" className="mt-2">
                  Back to Reports
                </Button>
              </Link>
            </motion.div>
          )}

          {/* Generating state */}
          {report && (report.status === "pending" || report.status === "generating") && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center gap-4 py-16"
            >
              <HugeiconsIcon
                icon={Loading03Icon}
                className="size-8 text-muted-foreground/50 animate-spin"
                strokeWidth={1.5}
              />
              <ReportStatusBadge status={report.status} />
              <p className="text-sm text-muted-foreground text-center max-w-[40ch]">
                Your report is being generated. This page will update automatically.
              </p>
            </motion.div>
          )}

          {/* Failed state */}
          {report && report.status === "failed" && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center gap-2 py-16"
            >
              <HugeiconsIcon
                icon={AlertCircleIcon}
                className="size-8 text-destructive/50"
                strokeWidth={1.5}
              />
              <ReportStatusBadge status={report.status} />
              <p className="mt-2 text-sm text-destructive text-center max-w-[50ch]">
                {report.error_message || "Report generation failed"}
              </p>
              <Button
                onClick={handleRetry}
                disabled={retryReport.isPending}
                size="sm"
                variant="outline"
                className={cn(
                  "mt-4 transition-transform duration-150",
                  "active:scale-[0.96]",
                )}
              >
                {retryReport.isPending ? (
                  <HugeiconsIcon
                    icon={Loading03Icon}
                    className="animate-spin"
                    data-icon="inline-start"
                    strokeWidth={2}
                  />
                ) : (
                  <HugeiconsIcon
                    icon={RefreshIcon}
                    data-icon="inline-start"
                    strokeWidth={2}
                  />
                )}
                {retryReport.isPending ? "Retrying…" : "Retry"}
              </Button>
            </motion.div>
          )}

          {/* Ready state - show report */}
          {report && report.status === "ready" && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              <ReportViewer report={report} />
            </motion.div>
          )}
        </div>
      </div>
    </div>
  )
}

function formatDateRange(start: string, end: string): string {
  const startDate = new Date(start)
  const endDate = new Date(end)
  const options: Intl.DateTimeFormatOptions = { month: "short", day: "numeric" }
  return `${startDate.toLocaleDateString("en-US", options)} – ${endDate.toLocaleDateString("en-US", options)}`
}
