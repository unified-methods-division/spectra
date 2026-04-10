import { useState } from "react"
import { AnimatePresence, motion } from "motion/react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useCreateSource } from "@/hooks/use-sources"

const SOURCE_TYPES = [
  { value: "csv_upload", label: "CSV Upload", supported: true },
  { value: "webhook", label: "Webhook", supported: false },
  { value: "rss_pull", label: "RSS Pull", supported: false },
  { value: "api_pull", label: "API Pull", supported: false },
]

type Props = {
  onDone: () => void
}

export function CreateSourceForm({ onDone }: Props) {
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
          onDone()
        },
      },
    )
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-2 pb-2">
      <Input
        placeholder="Source name"
        value={name}
        onChange={(e) => setName(e.target.value)}
        required
        autoFocus
        className="flex-1"
      />
      <Select value={sourceType} onValueChange={(v) => v && setSourceType(v)}>
        <SelectTrigger className="w-36 shrink-0">
          <SelectValue>
            {SOURCE_TYPES.find((t) => t.value === sourceType)?.label}
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          {SOURCE_TYPES.map((t) => (
            <SelectItem key={t.value} value={t.value} disabled={!t.supported}>
              <span className="flex items-center gap-2">
                {t.label}
                {!t.supported && (
                  <span className="text-[10px] text-muted-foreground/50">Soon</span>
                )}
              </span>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Button
        type="submit"
        size="default"
        disabled={!name.trim() || createSource.isPending}
        className="relative overflow-hidden"
      >
        <AnimatePresence mode="wait" initial={false}>
          {createSource.isPending ? (
            <motion.span
              key="loading"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.15, ease: [0.23, 1, 0.32, 1] }}
              className="flex items-center gap-1.5"
            >
              <motion.span
                className="size-3 rounded-full border-2 border-primary-foreground/30 border-t-primary-foreground"
                animate={{ rotate: 360 }}
                transition={{ duration: 0.6, repeat: Infinity, ease: "linear" }}
              />
              Adding
            </motion.span>
          ) : (
            <motion.span
              key="idle"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.15, ease: [0.23, 1, 0.32, 1] }}
            >
              Add
            </motion.span>
          )}
        </AnimatePresence>
      </Button>
      <Button type="button" variant="ghost" size="default" onClick={onDone}>
        Cancel
      </Button>
    </form>
  )
}
