import { useState } from "react"
import { useSources } from "@/hooks/use-sources"
import { SourcesTable } from "@/components/sources-table"
import { CreateSourceDialog } from "@/components/create-source-dialog"
import { UploadCsvDialog } from "@/components/upload-csv-dialog"
import { Button } from "@/components/ui/button"
import { HugeiconsIcon } from "@hugeicons/react"
import { Add01Icon } from "@hugeicons/core-free-icons"

export function SourcesPage() {
  const { data: sources, isLoading, error } = useSources()
  const [createOpen, setCreateOpen] = useState(false)
  const [uploadSourceId, setUploadSourceId] = useState<string | null>(null)

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">Sources</h1>
          <p className="text-sm text-muted-foreground">
            Manage your feedback data sources.
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <HugeiconsIcon
            icon={Add01Icon}
            data-icon="inline-start"
            strokeWidth={2}
          />
          Add Source
        </Button>
      </div>

      {isLoading && (
        <p className="text-sm text-muted-foreground">Loading sources...</p>
      )}

      {error && (
        <p className="text-sm text-destructive">
          Failed to load sources. Check that the backend is running.
        </p>
      )}

      {sources && (
        <SourcesTable
          sources={sources}
          onUpload={(id) => setUploadSourceId(id)}
        />
      )}

      <CreateSourceDialog open={createOpen} onOpenChange={setCreateOpen} />

      <UploadCsvDialog
        sourceId={uploadSourceId}
        onClose={() => setUploadSourceId(null)}
      />
    </div>
  )
}
