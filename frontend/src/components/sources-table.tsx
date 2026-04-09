import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ProcessingStatusBadge } from "./processing-status-badge"
import { formatRelativeTime, sourceTypeLabel } from "@/lib/utils"
import type { Source } from "@/types/api"
import { HugeiconsIcon } from "@hugeicons/react"
import { CloudUploadIcon } from "@hugeicons/core-free-icons"

type Props = {
  sources: Source[]
  onUpload: (sourceId: string) => void
}

export function SourcesTable({ sources, onUpload }: Props) {
  if (sources.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-border py-16 text-center">
        <p className="text-sm text-muted-foreground">No sources yet.</p>
        <p className="text-xs text-muted-foreground">
          Add a source to start importing feedback.
        </p>
      </div>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Type</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Last Synced</TableHead>
          <TableHead className="text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {sources.map((source) => (
          <TableRow key={source.id}>
            <TableCell className="font-medium">{source.name}</TableCell>
            <TableCell>
              <Badge variant="outline">{sourceTypeLabel(source.source_type)}</Badge>
            </TableCell>
            <TableCell>
              <ProcessingStatusBadge source={source} />
            </TableCell>
            <TableCell className="text-muted-foreground">
              {source.last_synced_at
                ? formatRelativeTime(source.last_synced_at)
                : "Never"}
            </TableCell>
            <TableCell className="text-right">
              {source.source_type === "csv_upload" && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onUpload(source.id)}
                >
                  <HugeiconsIcon
                    icon={CloudUploadIcon}
                    data-icon="inline-start"
                    strokeWidth={2}
                  />
                  Upload
                </Button>
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
