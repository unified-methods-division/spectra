/**
 * ReportsPage - list of all reports with ability to generate new ones.
 */

import { motion } from "motion/react"
import { Link } from "react-router"
import { useReports, useCreateReport } from "@/lib/api/reports"
import { ReportStatusBadge } from "@/components/reports"
import { Button } from "@/components/ui/button"
import { HugeiconsIcon } from "@hugeicons/react"
import { FileValidationIcon, Loading03Icon, Add01Icon } from "@hugeicons/core-free-icons"
import { cn } from "@/lib/utils"

export function ReportsPage() {
  const { data: reports, isLoading, error } = useReports()
  const createReport = useCreateReport()

  const handleGenerateReport = () => {
    createReport.mutate({})
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
        {/* Header */}
        <div className="flex items-end justify-between mb-5">
          <div>
            <span className="text-xs font-medium tracking-[0.2em] text-foreground/80 uppercase">
              Weekly Outlook
            </span>
            <h1 className="text-3xl font-normal tracking-tight text-foreground">
              Feedback insights and recommendations
            </h1>
          </div>
          <Button
            onClick={handleGenerateReport}
            disabled={createReport.isPending}
            size="sm"
            variant="outline"
          >
            {createReport.isPending ? (
              <HugeiconsIcon
                icon={Loading03Icon}
                className="animate-spin"
                data-icon="inline-start"
                strokeWidth={2}
              />
            ) : (
              <HugeiconsIcon
                icon={Add01Icon}
                data-icon="inline-start"
                strokeWidth={2}
              />
            )}
            {createReport.isPending ? "Generating…" : "Generate report"}
          </Button>
        </div>

        {/* Panel */}
        <div className="rounded-xl border border-foreground/8 bg-card/80 backdrop-blur-xl p-5">
          {/* Loading */}
          {isLoading && (
            <div className="grid gap-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div
                  key={i}
                  className="rounded-xl border border-foreground/5 bg-muted/30 p-4 animate-pulse"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="h-4 w-32 rounded bg-muted" />
                      <div className="mt-2 h-3 w-24 rounded bg-muted/70" />
                    </div>
                    <div className="h-5 w-16 rounded-full bg-muted/50" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Error */}
          {error && (
            <p className="py-8 text-center text-sm text-destructive">
              Couldn't load reports. Check that the backend is running.
            </p>
          )}

          {/* Empty */}
          {reports && reports.length === 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.15, duration: 0.3 }}
              className="flex flex-col items-center gap-2 py-16"
            >
              <HugeiconsIcon
                icon={FileValidationIcon}
                className="size-8 text-muted-foreground/30"
                strokeWidth={1.5}
              />
              <p className="text-sm text-muted-foreground">No reports yet</p>
              <p className="text-xs text-muted-foreground/60 max-w-[40ch] text-center">
                Generate your first weekly report to see AI-powered insights
                and recommendations based on your feedback data.
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={handleGenerateReport}
                disabled={createReport.isPending}
                className="mt-2"
              >
                Generate your first report
              </Button>
            </motion.div>
          )}

          {/* Report list */}
          {reports && reports.length > 0 && (
            <>
              <p className="mb-3 text-xs font-medium tracking-[0.15em] text-muted-foreground/50 uppercase">
                {reports.length} report{reports.length !== 1 ? "s" : ""}
              </p>
              <div className="grid gap-3">
                {reports.map((report, i) => (
                  <motion.div
                    key={report.id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05, duration: 0.2 }}
                  >
                    <Link
                      to={`/reports/${report.id}`}
                      className={cn(
                        "block rounded-xl p-4",
                        "border border-foreground/5",
                        "bg-background/50",
                        "transition-colors duration-150",
                        "hover:bg-background/80 hover:border-foreground/10",
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium">
                            {formatDateRange(report.period_start, report.period_end)}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            Created {formatRelativeTime(report.created_at)}
                          </p>
                        </div>
                        <ReportStatusBadge status={report.status} />
                      </div>
                    </Link>
                  </motion.div>
                ))}
              </div>
            </>
          )}
        </div>

        {/* Generation status toast */}
        {createReport.isSuccess && (
          <motion.p
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-3 text-center text-xs text-success"
          >
            Report generation started.
          </motion.p>
        )}
      </div>
    </div>
  )
}

function formatDateRange(start: string, end: string): string {
  const startDate = new Date(start)
  const endDate = new Date(end)
  const options: Intl.DateTimeFormatOptions = { month: "short", day: "numeric" }
  return `${startDate.toLocaleDateString("en-US", options)} – ${endDate.toLocaleDateString("en-US", options)}, ${endDate.getFullYear()}`
}

function formatRelativeTime(isoString: string): string {
  const date = new Date(isoString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))

  if (diffHours < 1) return "just now"
  if (diffHours < 24) return `${diffHours}h ago`
  return date.toLocaleDateString()
}
