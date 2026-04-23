import { useState } from "react"
import type { UseQueryResult } from "@tanstack/react-query"
import { cn } from "@/lib/utils"
import { AnimatePresence, motion } from "motion/react"
import { Button } from "@/components/ui/button"
import { ProcessingStatusBadge } from "./processing-status-badge"
import { UploadPanel, type UploadPanelStep } from "./upload-panel"
import { formatRelativeTime, sourceTypeCopy } from "@/lib/utils"
import type { Source } from "@/types/api"
import { HugeiconsIcon } from "@hugeicons/react"
import { CloudUploadIcon, WebhookIcon, RssIcon, ApiIcon } from "@hugeicons/core-free-icons"
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip"
import type { RoutingConfig } from "@/lib/api/routing-config"
import {
  useRoutingConfigsForSourceIds,
  useUpdateRoutingConfig,
} from "@/lib/api/routing-config"

type Props = {
  sources: Source[]
  uploadingSourceId: string | null
  onUpload: (sourceId: string | null) => void
}

const SOURCE_ACTION_ICONS = {
  csv_upload: { icon: CloudUploadIcon, label: "Upload file" },
  webhook: { icon: WebhookIcon, label: "Webhook URL" },
  rss_pull: { icon: RssIcon, label: "Feed URL" },
  api_pull: { icon: ApiIcon, label: "Configure connection" },
} as const

function SourceAction({
  source,
  isUploading,
  itemCount,
  onUpload,
}: {
  source: Source
  isUploading: boolean
  itemCount: number
  onUpload: () => void
}) {
  const config = SOURCE_ACTION_ICONS[source.source_type as keyof typeof SOURCE_ACTION_ICONS]
  if (!config) return null

  const hasAction = source.source_type === "csv_upload"
  const tooltipLabel = hasAction ? config.label : `${config.label} — coming soon`

  return (
    <Tooltip>
      <TooltipTrigger
        render={
          <Button
            variant="ghost"
            size="icon-sm"
            className={cn(
              "transition-all duration-150",
              !hasAction
                ? "cursor-default text-muted-foreground/30"
                : isUploading ? "invisible" : itemCount === 0 ? "text-muted-foreground hover:text-foreground" : "opacity-0 group-hover:opacity-100",
            )}
            onClick={hasAction ? onUpload : undefined}
            tabIndex={isUploading || !hasAction ? -1 : 0}
            aria-label={tooltipLabel}
          >
            <HugeiconsIcon icon={config.icon} strokeWidth={1.5} />
          </Button>
        }
      />
      <TooltipContent side="left">{tooltipLabel}</TooltipContent>
    </Tooltip>
  )
}

function SourceRow({
  source,
  isUploading,
  onUpload,
  onCloseUpload,
  routing,
  updateRouting,
}: {
  source: Source
  isUploading: boolean
  onUpload: () => void
  onCloseUpload: () => void
  routing: UseQueryResult<RoutingConfig, Error>
  updateRouting: ReturnType<typeof useUpdateRoutingConfig>
}) {
  const counts = (source.config?.ingestion_counts ?? {}) as Record<string, number>
  const itemCount = counts.created ?? 0
  const [uploadPanelStep, setUploadPanelStep] = useState<UploadPanelStep>("select")
  const [showConfidence, setShowConfidence] = useState(false)
  const [localThreshold, setLocalThreshold] = useState<number | null>(null)

  const displayThreshold = localThreshold ?? routing.data?.confidence_threshold ?? 0.85
  const saveErrorForRow =
    updateRouting.isError && updateRouting.variables?.sourceId === source.id
  const savePendingForRow =
    updateRouting.isPending && updateRouting.variables?.sourceId === source.id

  const showImportProgressSubtitle =
    isUploading && (uploadPanelStep === "uploading" || uploadPanelStep === "tracking")

  return (
    <div className="group relative">
      {/* Hover accent — left edge glow */}
      <span className="absolute left-0 top-2 bottom-2 w-0.5 rounded-full bg-primary opacity-0 transition-opacity duration-150 group-hover:opacity-100" />

      <div className="flex items-center gap-4 py-3.5 pl-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2.5">
            <span className="text-[14px] font-medium text-foreground truncate">
              {source.name}
            </span>
            {itemCount > 0 && (
              <span className="bg-foreground/8 px-1 py-px font-mono text-[10px] tabular-nums text-muted-foreground">
                {itemCount.toLocaleString()} items
              </span>
            )}
          </div>
          <div className="mt-0.5 flex items-center gap-2 text-[11px] text-muted-foreground/70 tracking-wide">
            <span>{sourceTypeCopy(source.source_type).label}</span>
            <span aria-hidden>&middot;</span>
            <span>
              {showImportProgressSubtitle
                ? "Import in progress…"
                : source.last_synced_at
                  ? formatRelativeTime(source.last_synced_at)
                  : itemCount > 0
                    ? "Imported"
                    : sourceTypeCopy(source.source_type).emptyTimestamp}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          {!isUploading && <ProcessingStatusBadge source={source} />}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowConfidence((v) => !v)}
            className={cn(
              "h-8 px-2 text-xs",
              "opacity-0 group-hover:opacity-100 transition-opacity duration-150",
              showConfidence && "opacity-100",
            )}
          >
            Confidence
          </Button>
          <SourceAction
            source={source}
            isUploading={isUploading}
            itemCount={itemCount}
            onUpload={onUpload}
          />
        </div>
      </div>

      <AnimatePresence>
        {showConfidence && !isUploading && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2, ease: [0.25, 0.46, 0.45, 0.94] }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4">
              <div className="rounded-xl border border-foreground/5 bg-background/50 p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xs font-medium tracking-[0.15em] text-muted-foreground/60 uppercase">
                      Confidence threshold
                    </p>
                    <p className="mt-1 text-sm text-muted-foreground text-pretty">
                      Items with sentiment confidence below this value are flagged for review.
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-mono text-sm tabular-nums">
                      {routing.data
                        ? `${Math.round(displayThreshold * 100)}%`
                        : "—"}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground/70 font-mono tabular-nums">
                      {routing.data ? `${routing.data.flagged_preview_count} flagged` : "…"}
                    </p>
                  </div>
                </div>

                <div className="mt-3">
                  <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.01}
                    value={displayThreshold}
                    onChange={(e) =>
                      setLocalThreshold(Number(e.currentTarget.value))
                    }
                    onPointerUp={(e) => {
                      const confidence_threshold = Number(
                        (e.currentTarget as HTMLInputElement).value,
                      )
                      updateRouting.mutate({ sourceId: source.id, confidence_threshold })
                    }}
                    onKeyUp={(e) => {
                      if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return
                      const el = e.currentTarget as HTMLInputElement
                      updateRouting.mutate({
                        sourceId: source.id,
                        confidence_threshold: Number(el.value),
                      })
                    }}
                    className="w-full"
                    disabled={!routing.data || savePendingForRow}
                    aria-label="Confidence threshold"
                  />
                  {saveErrorForRow && (
                    <p className="mt-2 text-sm text-destructive" aria-live="polite">
                      Couldn't save threshold.
                    </p>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {isUploading && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2, ease: [0.25, 0.46, 0.45, 0.94] }}
            className="overflow-hidden"
          >
            <UploadPanel
              sourceId={source.id}
              onClose={onCloseUpload}
              onStepChange={setUploadPanelStep}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export function SourcesList({ sources, uploadingSourceId, onUpload }: Props) {
  const routingQueries = useRoutingConfigsForSourceIds(
    sources.map((s) => s.id),
  )
  const updateRouting = useUpdateRoutingConfig()

  if (sources.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.15, duration: 0.3 }}
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
        <p className="text-sm text-muted-foreground">
          No sources yet
        </p>
        <p className="text-xs text-muted-foreground/70">
          Connect a feedback channel to get started.
        </p>
      </motion.div>
    )
  }

  return (
    <div className="divide-y divide-border">
      {sources.map((source, i) => (
        <motion.div
          key={source.id}
          initial={{ opacity: 0, x: -6 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{
            duration: 0.25,
            delay: i * 0.06,
            ease: [0.23, 1, 0.32, 1],
          }}
        >
          <SourceRow
            source={source}
            isUploading={uploadingSourceId === source.id}
            onUpload={() => onUpload(source.id)}
            onCloseUpload={() => onUpload(null)}
            routing={routingQueries[i]!}
            updateRouting={updateRouting}
          />
        </motion.div>
      ))}
    </div>
  )
}
