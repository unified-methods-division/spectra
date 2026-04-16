import { useRef, useState } from "react"
import { AnimatePresence, motion } from "motion/react"
import { Button } from "@/components/ui/button"
import { useUploadFile, useTaskStatus } from "@/hooks/use-sources"
import { HugeiconsIcon } from "@hugeicons/react"
import { Cancel01Icon } from "@hugeicons/core-free-icons"

export type UploadPanelStep = "select" | "uploading" | "tracking"

type Props = {
  sourceId: string
  onClose: () => void
  onStepChange?: (step: UploadPanelStep) => void
}

type PanelState = {
  step: UploadPanelStep
  file: File | null
  taskId: string | null
  dragOver: boolean
}

const initialPanelState: PanelState = {
  step: "select",
  file: null,
  taskId: null,
  dragOver: false,
}

const stepTransition = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
  transition: { duration: 0.15 },
}

export function UploadPanel({ sourceId, onClose, onStepChange }: Props) {
  const [panel, setPanel] = useState<PanelState>(initialPanelState)
  const { step, file, taskId, dragOver } = panel
  const inputRef = useRef<HTMLInputElement>(null)

  const upload = useUploadFile(sourceId)
  const task = useTaskStatus(taskId, { sourceId })

  function reset() {
    setPanel(initialPanelState)
    onStepChange?.("select")
  }

  function handleClose() {
    reset()
    onClose()
  }

  function handleFileChange(f: File | null) {
    if (!f) return
    setPanel((p) => ({ ...p, file: f }))
  }

  function handleUpload() {
    if (!file) return
    setPanel((p) => ({ ...p, step: "uploading" }))
    onStepChange?.("uploading")
    upload.mutate(file, {
      onSuccess: (data) => {
        setPanel((p) => ({ ...p, step: "tracking", taskId: data.task_id }))
        onStepChange?.("tracking")
      },
      onError: () => {
        setPanel((p) => ({ ...p, step: "select" }))
        onStepChange?.("select")
      },
    })
  }

  const isDone = task.data?.status === "success"
  const isFailed = task.data?.status === "failure" || upload.isError

  return (
    <div className="pb-3 pl-4">
      <div className="flex items-center gap-2">
        <div className="flex-1 min-w-0">
          <AnimatePresence mode="wait">
            {step === "select" && (
              <motion.div key="select" {...stepTransition}>
                <div
                  className={`flex cursor-pointer items-center rounded-lg border-2 border-dashed px-3 py-2.5 text-xs transition-all duration-150 ${
                    dragOver
                      ? "border-primary/40 bg-primary/10 text-primary"
                      : file
                        ? "border-foreground/10 bg-primary/5 text-foreground"
                        : "border-foreground/10 bg-foreground/3 text-muted-foreground hover:border-foreground/20"
                  }`}
                  onClick={() => inputRef.current?.click()}
                  onDragOver={(e) => { e.preventDefault(); setPanel((p) => ({ ...p, dragOver: true })) }}
                  onDragLeave={() => setPanel((p) => ({ ...p, dragOver: false }))}
                  onDrop={(e) => {
                    e.preventDefault()
                    const dropped = e.dataTransfer.files[0]
                    setPanel((p) => ({
                      ...p,
                      dragOver: false,
                      ...(dropped ? { file: dropped } : {}),
                    }))
                  }}
                >
                  {file ? (
                    <span className="truncate">
                      <span className="font-medium">{file.name}</span>
                      {" "}
                      <span className="text-muted-foreground">
                        {(file.size / 1024).toFixed(1)} KB
                      </span>
                    </span>
                  ) : (
                    "Drop file or click to browse"
                  )}
                  <input
                    ref={inputRef}
                    type="file"
                    accept=".csv,.jsonl"
                    className="hidden"
                    onChange={(e) => handleFileChange(e.target.files?.[0] ?? null)}
                  />
                </div>
              </motion.div>
            )}

            {step === "uploading" && (
              <motion.div key="uploading" {...stepTransition} className="flex h-10 items-center gap-3">
                <div className="relative h-1 flex-1 overflow-hidden rounded bg-muted">
                  <motion.div
                    className="absolute h-full w-1/3 rounded bg-primary"
                    animate={{ left: ["-33%", "100%"] }}
                    transition={{ duration: 1.2, repeat: Infinity, ease: "easeInOut" }}
                  />
                </div>
                <span className="text-xs text-muted-foreground shrink-0">Uploading</span>
              </motion.div>
            )}

            {step === "tracking" && (
              <motion.div key="tracking" {...stepTransition} className="flex h-10 items-center gap-2">
                {isDone && (
                  <>
                    <motion.span
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ type: "spring", duration: 0.3, bounce: 0.3 }}
                      className="size-1.5 rounded-full bg-success"
                    />
                    <span className="text-xs text-success">Import complete</span>
                  </>
                )}
                {isFailed && (
                  <>
                    <span className="size-1.5 rounded-full bg-destructive" />
                    <span className="text-xs text-destructive">
                      {task.data?.error ?? "Import failed"}
                    </span>
                  </>
                )}
                {!isDone && !isFailed && (
                  <>
                    <div className="relative h-1 flex-1 overflow-hidden rounded bg-muted">
                      <motion.div
                        className="absolute h-full w-1/3 rounded bg-primary"
                        animate={{ left: ["-33%", "100%"] }}
                        transition={{ duration: 1.2, repeat: Infinity, ease: "easeInOut" }}
                      />
                    </div>
                    <span className="text-xs text-muted-foreground shrink-0">Importing</span>
                  </>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {step === "select" && (
          <Button size="xs" className="h-10" onClick={handleUpload} disabled={!file}>
            Upload
          </Button>
        )}
        <Button variant="ghost" size="icon-xs" onClick={handleClose}>
          <HugeiconsIcon icon={Cancel01Icon} strokeWidth={2} />
        </Button>
      </div>
    </div>
  )
}
