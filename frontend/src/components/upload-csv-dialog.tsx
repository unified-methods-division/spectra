import { useCallback, useRef, useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { useUploadFile, useTaskStatus } from "@/hooks/use-sources"
import { HugeiconsIcon } from "@hugeicons/react"
import { CloudUploadIcon, Tick02Icon, Alert02Icon } from "@hugeicons/core-free-icons"

type Props = {
  sourceId: string | null
  onClose: () => void
}

type Step = "select" | "uploading" | "tracking"

export function UploadCsvDialog({ sourceId, onClose }: Props) {
  const [step, setStep] = useState<Step>("select")
  const [file, setFile] = useState<File | null>(null)
  const [taskId, setTaskId] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const upload = useUploadFile(sourceId ?? "")
  const task = useTaskStatus(taskId)

  const reset = useCallback(() => {
    setStep("select")
    setFile(null)
    setTaskId(null)
    setDragOver(false)
  }, [])

  function handleClose() {
    reset()
    onClose()
  }

  function handleFileChange(f: File | null) {
    if (!f) return
    setFile(f)
  }

  function handleUpload() {
    if (!file || !sourceId) return
    setStep("uploading")
    upload.mutate(file, {
      onSuccess: (data) => {
        setTaskId(data.task_id)
        setStep("tracking")
      },
      onError: () => {
        setStep("select")
      },
    })
  }

  const isDone = task.data?.status === "success"
  const isFailed = task.data?.status === "failure" || upload.isError

  return (
    <Dialog open={!!sourceId} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Upload Feedback File</DialogTitle>
          <DialogDescription>
            Upload a CSV or JSONL file to import feedback items.
          </DialogDescription>
        </DialogHeader>

        {step === "select" && (
          <div className="flex flex-col gap-4">
            <div
              className={`flex cursor-pointer flex-col items-center gap-2 rounded-xl border-2 border-dashed px-4 py-10 text-center transition-colors ${
                dragOver
                  ? "border-ring bg-accent"
                  : "border-border hover:border-ring/50"
              }`}
              onClick={() => inputRef.current?.click()}
              onDragOver={(e) => {
                e.preventDefault()
                setDragOver(true)
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => {
                e.preventDefault()
                setDragOver(false)
                handleFileChange(e.dataTransfer.files[0] ?? null)
              }}
            >
              <HugeiconsIcon
                icon={CloudUploadIcon}
                strokeWidth={1.5}
                className="size-8 text-muted-foreground"
              />
              {file ? (
                <p className="text-sm">
                  {file.name}{" "}
                  <span className="text-muted-foreground">
                    ({(file.size / 1024).toFixed(1)} KB)
                  </span>
                </p>
              ) : (
                <p className="text-sm text-muted-foreground">
                  Drop a .csv or .jsonl file here, or click to browse.
                </p>
              )}
              <input
                ref={inputRef}
                type="file"
                accept=".csv,.jsonl"
                className="hidden"
                onChange={(e) =>
                  handleFileChange(e.target.files?.[0] ?? null)
                }
              />
            </div>

            {upload.isError && (
              <p className="text-sm text-destructive">
                Upload failed. Please try again.
              </p>
            )}

            <DialogFooter>
              <Button
                onClick={handleUpload}
                disabled={!file}
              >
                Upload
              </Button>
            </DialogFooter>
          </div>
        )}

        {step === "uploading" && (
          <div className="flex flex-col gap-4">
            <p className="text-sm">Uploading {file?.name}...</p>
            <div className="relative h-3 w-full overflow-hidden rounded-4xl bg-muted">
              <div className="absolute h-full w-1/3 animate-[indeterminate_1.5s_ease-in-out_infinite] rounded-4xl bg-primary" />
            </div>
          </div>
        )}

        {step === "tracking" && (
          <div className="flex flex-col gap-4">
            {isDone && (
              <div className="flex items-center gap-2 text-sm">
                <HugeiconsIcon
                  icon={Tick02Icon}
                  strokeWidth={2}
                  className="size-5 text-green-600"
                />
                Upload complete! Processing will begin shortly.
              </div>
            )}

            {isFailed && (
              <div className="flex items-center gap-2 text-sm text-destructive">
                <HugeiconsIcon
                  icon={Alert02Icon}
                  strokeWidth={2}
                  className="size-5"
                />
                {task.data?.error ?? "Ingestion failed."}
              </div>
            )}

            {!isDone && !isFailed && (
              <div className="flex flex-col gap-2">
                <p className="text-sm">Processing...</p>
                <div className="relative h-3 w-full overflow-hidden rounded-4xl bg-muted">
                  <div className="absolute h-full w-1/3 animate-[indeterminate_1.5s_ease-in-out_infinite] rounded-4xl bg-primary" />
                </div>
                <p className="text-xs text-muted-foreground">
                  Status: {task.data?.status ?? "Waiting..."}
                </p>
              </div>
            )}

            <DialogFooter>
              <Button variant="outline" onClick={handleClose}>
                {isDone || isFailed ? "Close" : "Close (continues in background)"}
              </Button>
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
