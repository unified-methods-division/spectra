import { AnimatePresence, motion } from "motion/react"
import { useProcessingStatus } from "@/hooks/use-sources"
import { cn, sourceTypeCopy } from "@/lib/utils"
import type { Source } from "@/types/api"

type StatusKey = "no_data" | "ingesting" | "ingested" | "processing" | "completed" | "failed"

const STATUS_CONFIG: Record<
  StatusKey,
  { label: string; dot: string; glow: string; text: string; alive: boolean }
> = {
  no_data: {
    label: "",
    dot: "bg-muted-foreground/30",
    glow: "",
    text: "text-muted-foreground/60",
    alive: false,
  },
  ingesting: {
    label: "Importing",
    dot: "bg-info",
    glow: "text-info animate-[glow-pulse_2s_ease-in-out_infinite]",
    text: "text-info",
    alive: true,
  },
  ingested: {
    label: "Imported",
    dot: "bg-success",
    glow: "text-success shadow-[0_0_4px_1px_currentColor]",
    text: "text-success",
    alive: false,
  },
  processing: {
    label: "Analyzing",
    dot: "bg-info",
    glow: "text-info animate-[glow-pulse_2s_ease-in-out_infinite]",
    text: "text-info",
    alive: true,
  },
  completed: {
    label: "Done",
    dot: "bg-success",
    glow: "text-success shadow-[0_0_4px_1px_currentColor]",
    text: "text-success",
    alive: false,
  },
  failed: {
    label: "Error",
    dot: "bg-destructive",
    glow: "text-destructive shadow-[0_0_4px_1px_currentColor]",
    text: "text-destructive",
    alive: false,
  },
}

function deriveStatus(source: Source, analysisStatus?: string | null): StatusKey {
  const config = source.config ?? {}
  const ingestionStatus = config.ingestion_status as string | undefined

  if (ingestionStatus === "failed") return "failed"
  if (ingestionStatus === "processing" || ingestionStatus === "pending") return "ingesting"

  if (analysisStatus === "failed") return "failed"
  if (analysisStatus === "processing") return "processing"
  if (analysisStatus === "completed") return "completed"

  if (ingestionStatus === "completed") return "ingested"

  return "no_data"
}


export function ProcessingStatusBadge({ source }: { source: Source }) {
  const { data, isLoading } = useProcessingStatus(source.id)

  const status = isLoading ? null : deriveStatus(source, data?.overall_status)
  const config = status ? STATUS_CONFIG[status] : null

  return (
    <AnimatePresence mode="wait">
      {!config ? (
        <motion.span
          key="loading"
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.4 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          className="flex items-center gap-1.5 text-xs text-muted-foreground"
        >
          <span className="size-1.5 rounded-full bg-muted-foreground/20" />
        </motion.span>
      ) : (
        <motion.span
          key={status}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          className={cn("flex items-center gap-2 text-xs", config.text)}
        >
          <span
            className={cn(
              "size-1.5 shrink-0 rounded-full",
              config.dot,
              config.glow,
            )}
          />
          {config.label || sourceTypeCopy(source.source_type).emptyStatus}
        </motion.span>
      )}
    </AnimatePresence>
  )
}
