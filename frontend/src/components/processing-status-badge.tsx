import { useProcessingStatus } from "@/hooks/use-sources"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { Source } from "@/types/api"

type StatusKey = "no_data" | "ingesting" | "ingested" | "processing" | "completed" | "failed"

const STATUS_CONFIG: Record<
  StatusKey,
  { label: string; variant: "secondary" | "outline" | "default" | "destructive"; pulse: boolean }
> = {
  no_data: { label: "Awaiting upload", variant: "secondary", pulse: false },
  ingesting: { label: "Importing...", variant: "outline", pulse: true },
  ingested: { label: "Ready to analyze", variant: "outline", pulse: false },
  processing: { label: "Analyzing...", variant: "outline", pulse: true },
  completed: { label: "Done", variant: "default", pulse: false },
  failed: { label: "Error", variant: "destructive", pulse: false },
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

  if (isLoading) {
    return (
      <Badge variant="secondary" className="animate-pulse">
        ...
      </Badge>
    )
  }

  const status = deriveStatus(source, data?.overall_status)
  const config = STATUS_CONFIG[status]

  return (
    <Badge
      variant={config.variant}
      className={cn(config.pulse && "animate-pulse")}
    >
      {config.label}
    </Badge>
  )
}
