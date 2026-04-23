import { useState } from "react"
import { motion, AnimatePresence } from "motion/react"
import {
  useDisagreementRate,
  useDisagreements,
  useResolveDisagreement,
  type Disagreement,
} from "@/lib/api/eval"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Input } from "@/components/ui/input"

const SENTIMENT_OPTIONS = ["positive", "neutral", "negative"] as const
const URGENCY_OPTIONS = ["low", "medium", "high", "critical"] as const

function ResolveDialog({
  disagreement,
  open,
  onOpenChange,
}: {
  disagreement: Disagreement
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const resolve = useResolveDisagreement()
  const [value, setValue] = useState<string>("")

  const handleResolve = () => {
    const resolvedValue =
      disagreement.field_corrected === "themes"
        ? value
            .split(",")
            .map((t) => t.trim())
            .filter(Boolean)
        : value
    resolve.mutate(
      { disagreementId: disagreement.id, resolvedValue },
      {
        onSuccess: () => {
          setValue("")
          onOpenChange(false)
        },
      },
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Resolve Disagreement</DialogTitle>
          <DialogDescription>
            Field: {disagreement.field_corrected}
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-3">
          {disagreement.field_corrected === "sentiment" && (
            <Select value={value} onValueChange={(v) => v != null && setValue(v)}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select sentiment" />
              </SelectTrigger>
              <SelectContent>
                {SENTIMENT_OPTIONS.map((opt) => (
                  <SelectItem key={opt} value={opt}>
                    {opt}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}

          {disagreement.field_corrected === "urgency" && (
            <Select value={value} onValueChange={(v) => v != null && setValue(v)}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select urgency" />
              </SelectTrigger>
              <SelectContent>
                {URGENCY_OPTIONS.map((opt) => (
                  <SelectItem key={opt} value={opt}>
                    {opt}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}

          {disagreement.field_corrected === "themes" && (
            <Input
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder="comma-separated themes"
            />
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleResolve} disabled={!value || resolve.isPending}>
            Resolve
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function DisagreementRow({
  disagreement,
  index,
  onResolve,
}: {
  disagreement: Disagreement
  index: number
  onResolve: (d: Disagreement) => void
}) {
  const truncatedId = disagreement.feedback_item.slice(0, 8) + "…"

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04 }}
      className="flex items-center justify-between gap-3 rounded-lg border border-foreground/5 bg-background/50 px-3 py-2"
    >
      <div className="flex items-center gap-3 min-w-0">
        <span className="font-mono text-xs tabular-nums text-muted-foreground/70 uppercase">
          {disagreement.field_corrected}
        </span>
        <span className="font-mono text-xs tabular-nums text-muted-foreground/50 truncate">
          {truncatedId}
        </span>
      </div>
      <Button
        size="xs"
        variant="outline"
        onClick={() => onResolve(disagreement)}
        aria-label={`Resolve ${disagreement.field_corrected} disagreement for ${truncatedId}`}
      >
        Resolve
      </Button>
    </motion.div>
  )
}

export function DisagreementRateCard() {
  const rateQ = useDisagreementRate()
  const disQ = useDisagreements("pending")

  const isLoading = rateQ.isLoading || disQ.isLoading
  const error = rateQ.error ?? disQ.error

  const pending = disQ.data ?? []
  const pendingCount = pending.length
  const rate = rateQ.data?.disagreement_rate

  const [activeDisagreement, setActiveDisagreement] = useState<Disagreement | null>(null)
  const visibleDisagreements = pending.slice(0, 5)
  const overflow = pendingCount - visibleDisagreements.length

  return (
    <div className="rounded-xl border border-foreground/8 bg-card/80 backdrop-blur-xl p-5">
      <p className="mb-3 text-xs font-medium tracking-[0.15em] text-muted-foreground/50 uppercase">
        Disagreement rate
      </p>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : error ? (
        <p className="text-sm text-destructive">
          Couldn't load disagreement rate.
        </p>
      ) : (
        <>
          <p className="font-mono text-xl tabular-nums">
            {rate != null ? `${rate}%` : "—"}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            {pendingCount} pending
          </p>

          {pendingCount === 0 ? (
            <p className="mt-3 text-xs text-muted-foreground/60">
              No pending disagreements
            </p>
          ) : (
            <div className="mt-3 grid gap-1.5">
              <AnimatePresence>
                {visibleDisagreements.map((d, i) => (
                  <DisagreementRow
                    key={d.id}
                    disagreement={d}
                    index={i}
                    onResolve={setActiveDisagreement}
                  />
                ))}
              </AnimatePresence>
              {overflow > 0 && (
                <p className="text-xs text-muted-foreground/60 mt-1">
                  +{overflow} more
                </p>
              )}
            </div>
          )}
        </>
      )}

      {activeDisagreement && (
        <ResolveDialog
          disagreement={activeDisagreement}
          open={!!activeDisagreement}
          onOpenChange={(open) => {
            if (!open) setActiveDisagreement(null)
          }}
        />
      )}
    </div>
  )
}