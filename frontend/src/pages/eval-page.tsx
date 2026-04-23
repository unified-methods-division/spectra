import { useState } from "react"
import { motion } from "motion/react"
import {
  useGoldEval,
  useGoldSetItems,
  useCreateGoldSetItem,
  useDeleteGoldSetItem,
} from "@/lib/api/eval"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { cn } from "@/lib/utils"
import { HugeiconsIcon } from "@hugeicons/react"
import { Delete02Icon } from "@hugeicons/core-free-icons"

const SENTIMENT_OPTIONS = ["positive", "neutral", "negative"] as const
const URGENCY_OPTIONS = ["low", "medium", "high", "critical"] as const

function EvalSummarySection() {
  const { data, isLoading, error } = useGoldEval()

  return (
    <div className="rounded-xl border border-foreground/8 bg-card/80 backdrop-blur-xl p-5">
      <p className="mb-3 text-xs font-medium tracking-[0.15em] text-muted-foreground/50 uppercase">
        Gold eval
      </p>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : error ? (
        <p className="text-sm text-destructive">Couldn't load eval results.</p>
      ) : !data ? (
        <p className="text-sm text-muted-foreground">No eval data yet.</p>
      ) : (
        <>
          <p className="font-mono text-xl tabular-nums">
            {(data.overall_accuracy * 100).toFixed(1)}%
          </p>
          <p className="mt-0.5 text-xs text-muted-foreground">overall accuracy</p>

          <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div>
              <p className="text-xs font-medium tracking-[0.15em] text-muted-foreground/60 uppercase">
                Sentiment
              </p>
              <p className="mt-1 font-mono text-sm tabular-nums">
                {data.field_accuracy.sentiment != null
                  ? `${(data.field_accuracy.sentiment * 100).toFixed(1)}%`
                  : "—"}
              </p>
            </div>
            <div>
              <p className="text-xs font-medium tracking-[0.15em] text-muted-foreground/60 uppercase">
                Urgency
              </p>
              <p className="mt-1 font-mono text-sm tabular-nums">
                {data.field_accuracy.urgency != null
                  ? `${(data.field_accuracy.urgency * 100).toFixed(1)}%`
                  : "—"}
              </p>
            </div>
            <div>
              <p className="text-xs font-medium tracking-[0.15em] text-muted-foreground/60 uppercase">
                Theme prec.
              </p>
              <p className="mt-1 font-mono text-sm tabular-nums">
                {data.theme_precision != null
                  ? `${(data.theme_precision * 100).toFixed(1)}%`
                  : "—"}
              </p>
            </div>
            <div>
              <p className="text-xs font-medium tracking-[0.15em] text-muted-foreground/60 uppercase">
                Theme recall
              </p>
              <p className="mt-1 font-mono text-sm tabular-nums">
                {data.theme_recall != null
                  ? `${(data.theme_recall * 100).toFixed(1)}%`
                  : "—"}
              </p>
            </div>
          </div>

          <p className="mt-3 font-mono text-xs tabular-nums text-muted-foreground/60">
            {data.items_evaluated} items evaluated
          </p>
        </>
      )}
    </div>
  )
}

function DeleteCell({ id }: { id: string }) {
  const del = useDeleteGoldSetItem()
  const [confirming, setConfirming] = useState(false)

  if (confirming) {
    return (
      <div className="flex items-center gap-1">
        <Button
          size="xs"
          variant="destructive"
          onClick={() => {
            del.mutate(id)
            setConfirming(false)
          }}
          disabled={del.isPending}
        >
          Confirm?
        </Button>
        <Button
          size="xs"
          variant="ghost"
          onClick={() => setConfirming(false)}
        >
          Cancel
        </Button>
      </div>
    )
  }

  return (
    <Button
      size="icon-xs"
      variant="ghost"
      onClick={() => setConfirming(true)}
      aria-label="Delete gold set item"
    >
      <HugeiconsIcon icon={Delete02Icon} strokeWidth={2} />
    </Button>
  )
}

function GoldItemsTableSection() {
  const { data, isLoading, error } = useGoldSetItems()

  return (
    <div className="rounded-xl border border-foreground/8 bg-card/80 backdrop-blur-xl p-5">
      <p className="mb-3 text-xs font-medium tracking-[0.15em] text-muted-foreground/50 uppercase">
        Gold set items
      </p>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : error ? (
        <p className="text-sm text-destructive">Couldn't load gold set items.</p>
      ) : !data || data.length === 0 ? null : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Item ID</TableHead>
              <TableHead>Sentiment</TableHead>
              <TableHead>Urgency</TableHead>
              <TableHead>Themes</TableHead>
              <TableHead className="w-24">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((item, i) => (
              <motion.tr
                key={item.id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
                className="border-b transition-colors hover:bg-muted/50"
              >
                <TableCell className="font-mono text-xs tabular-nums">
                  {item.feedback_item.slice(0, 8)}…
                </TableCell>
                <TableCell>
                  <Badge variant="secondary">{item.gold_sentiment}</Badge>
                </TableCell>
                <TableCell>
                  <Badge variant="outline">{item.gold_urgency}</Badge>
                </TableCell>
                <TableCell className="text-xs text-muted-foreground">
                  {item.gold_themes.join(", ")}
                </TableCell>
                <TableCell>
                  <DeleteCell id={item.id} />
                </TableCell>
              </motion.tr>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  )
}

function AddGoldItemSection() {
  const create = useCreateGoldSetItem()
  const [feedbackItem, setFeedbackItem] = useState("")
  const [sentiment, setSentiment] = useState("")
  const [urgency, setUrgency] = useState("")
  const [themes, setThemes] = useState("")
  const [errors, setErrors] = useState<Record<string, boolean>>({})
  const [justCreated, setJustCreated] = useState(false)

  const handleSubmit = () => {
    const newErrors: Record<string, boolean> = {}
    if (!feedbackItem) newErrors.feedbackItem = true
    if (!sentiment) newErrors.sentiment = true
    if (!urgency) newErrors.urgency = true
    if (!themes) newErrors.themes = true

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      return
    }

    const goldThemes = themes
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean)

    create.mutate(
      {
        feedbackItem,
        goldSentiment: sentiment,
        goldUrgency: urgency,
        goldThemes,
      },
      {
        onSuccess: () => {
          setFeedbackItem("")
          setSentiment("")
          setUrgency("")
          setThemes("")
          setErrors({})
          setJustCreated(true)
          setTimeout(() => setJustCreated(false), 2000)
        },
      },
    )
  }

  return (
    <div className="rounded-xl border border-foreground/8 bg-card/80 backdrop-blur-xl p-5">
      <p className="mb-3 text-xs font-medium tracking-[0.15em] text-muted-foreground/50 uppercase">
        Add gold item
      </p>

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label className="mb-1 block text-xs text-muted-foreground">
            Feedback item UUID
          </label>
          <Input
            value={feedbackItem}
            onChange={(e) => {
              setFeedbackItem(e.target.value)
              if (e.target.value) setErrors((prev) => ({ ...prev, feedbackItem: false }))
            }}
            placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
            aria-label="Feedback item UUID"
            aria-invalid={errors.feedbackItem}
            className={cn(errors.feedbackItem && "border-destructive")}
          />
          {errors.feedbackItem && (
            <p className="mt-1 text-xs text-destructive">Required</p>
          )}
        </div>

        <div>
          <label className="mb-1 block text-xs text-muted-foreground">
            Gold sentiment
          </label>
          <Select
            value={sentiment}
            onValueChange={(v) => {
              if (v != null) setSentiment(v)
              setErrors((prev) => ({ ...prev, sentiment: false }))
            }}
          >
            <SelectTrigger
              className={cn("w-full", errors.sentiment && "border-destructive")}
              aria-label="Gold sentiment"
            >
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
          {errors.sentiment && (
            <p className="mt-1 text-xs text-destructive">Required</p>
          )}
        </div>

        <div>
          <label className="mb-1 block text-xs text-muted-foreground">
            Gold urgency
          </label>
          <Select
            value={urgency}
            onValueChange={(v) => {
              if (v != null) setUrgency(v)
              setErrors((prev) => ({ ...prev, urgency: false }))
            }}
          >
            <SelectTrigger
              className={cn("w-full", errors.urgency && "border-destructive")}
              aria-label="Gold urgency"
            >
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
          {errors.urgency && (
            <p className="mt-1 text-xs text-destructive">Required</p>
          )}
        </div>

        <div>
          <label className="mb-1 block text-xs text-muted-foreground">
            Gold themes
          </label>
          <Input
            value={themes}
            onChange={(e) => {
              setThemes(e.target.value)
              if (e.target.value) setErrors((prev) => ({ ...prev, themes: false }))
            }}
            placeholder="comma-separated, e.g. pricing, support"
            aria-label="Gold themes"
            aria-invalid={errors.themes}
            className={cn(errors.themes && "border-destructive")}
          />
          {errors.themes && (
            <p className="mt-1 text-xs text-destructive">Required</p>
          )}
        </div>
      </div>

      <div className="mt-4">
        <Button
          onClick={handleSubmit}
          disabled={create.isPending}
        >
          {justCreated ? "✓ Added" : "Add to gold set"}
        </Button>
      </div>
    </div>
  )
}

function EmptyGoldState() {
  return (
    <div className="rounded-xl border border-foreground/8 bg-card/80 backdrop-blur-xl p-8 text-center">
      <p className="text-sm text-muted-foreground">
        No gold set items yet. A gold set is a collection of feedback items with
        known-correct labels used to measure AI classification accuracy over
        time. Add your first item below.
      </p>
    </div>
  )
}

export function EvalPage() {
  const { data: goldItems, isLoading: goldLoading } = useGoldSetItems()
  const hasItems = goldItems && goldItems.length > 0

  return (
    <div>
      <div className="relative">
        <div className="h-72">
          <img
            src="https://images.unsplash.com/photo-1504868584819-f8e61aeed528?q=80&w=1600&auto=format&fit=crop"
            alt=""
            className="h-full w-full object-cover"
          />
          <div className="absolute inset-0 bg-linear-to-b from-background/60 via-background/20 to-background" />
        </div>
      </div>

      <div className="relative -mt-24 mx-auto max-w-3xl px-10">
        <div className="mb-8">
          <span className="text-xs font-medium tracking-[0.2em] text-foreground/80 uppercase">
            Eval
          </span>
          <h1 className="text-3xl font-normal tracking-tight text-foreground">
            Gold set & accuracy
          </h1>
        </div>

        <div className="grid gap-4">
          <EvalSummarySection />

          {goldLoading ? (
            <div className="rounded-xl border border-foreground/8 bg-card/80 backdrop-blur-xl p-5">
              <p className="text-sm text-muted-foreground">Loading…</p>
            </div>
          ) : hasItems ? (
            <GoldItemsTableSection />
          ) : (
            <EmptyGoldState />
          )}

          <AddGoldItemSection />
        </div>
      </div>
    </div>
  )
}