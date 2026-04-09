import { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useCreateSource } from "@/hooks/use-sources"

type Props = {
  open: boolean
  onOpenChange: (open: boolean) => void
}

const SOURCE_TYPES = [
  { value: "csv_upload", label: "CSV Upload" },
  { value: "webhook", label: "Webhook" },
  { value: "rss_pull", label: "RSS Pull" },
  { value: "api_pull", label: "API Pull" },
]

export function CreateSourceDialog({ open, onOpenChange }: Props) {
  const [name, setName] = useState("")
  const [sourceType, setSourceType] = useState("csv_upload")
  const createSource = useCreateSource()

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    createSource.mutate(
      { name: name.trim(), source_type: sourceType },
      {
        onSuccess: () => {
          setName("")
          setSourceType("csv_upload")
          onOpenChange(false)
        },
      },
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add Source</DialogTitle>
          <DialogDescription>
            Create a new feedback data source.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="source-name">Name</Label>
            <Input
              id="source-name"
              placeholder="e.g. App Store Reviews"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label>Type</Label>
            <Select value={sourceType} onValueChange={(v) => v && setSourceType(v)}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SOURCE_TYPES.map((t) => (
                  <SelectItem key={t.value} value={t.value}>
                    {t.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button
              type="submit"
              disabled={!name.trim() || createSource.isPending}
            >
              {createSource.isPending ? "Creating..." : "Create Source"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
