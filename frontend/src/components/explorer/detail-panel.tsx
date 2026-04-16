import { useState } from "react"
import { cn, formatRelativeTime } from "@/lib/utils"
import { AnimatePresence, motion } from "motion/react"
import { Button } from "@/components/ui/button"
import { HugeiconsIcon } from "@hugeicons/react"
import { Cancel01Icon, PencilEdit01Icon, Tick02Icon } from "@hugeicons/core-free-icons"
import { useSubmitCorrection } from "@/hooks/use-explorer"
import type { FeedbackItem, Sentiment, Urgency } from "@/types/api"

type DetailPanelProps = {
  item: FeedbackItem
  onClose: () => void
  /** Slug matches `?theme=`; only used from Explorer */
  onFilterByTheme?: (themeSlug: string) => void
}

const SENTIMENT_OPTIONS: { value: Sentiment; label: string; className: string }[] = [
  { value: "positive", label: "Positive", className: "text-success" },
  { value: "negative", label: "Negative", className: "text-destructive" },
  { value: "neutral", label: "Neutral", className: "text-muted-foreground" },
  { value: "mixed", label: "Mixed", className: "text-warning" },
]

const URGENCY_OPTIONS: { value: Urgency; label: string; className?: string }[] = [
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High", className: "text-warning" },
  { value: "critical", label: "Critical", className: "text-destructive" },
]

const SENTIMENT_STYLES: Record<string, { text: string; bg: string }> = {
  positive: { text: "text-success", bg: "bg-success/10" },
  negative: { text: "text-destructive", bg: "bg-destructive/10" },
  neutral: { text: "text-muted-foreground", bg: "bg-muted" },
  mixed: { text: "text-warning", bg: "bg-warning/10" },
}

const URGENCY_STYLES: Record<string, string> = {
  low: "text-muted-foreground bg-muted",
  medium: "text-foreground bg-foreground/8",
  high: "text-warning bg-warning/10",
  critical: "text-destructive bg-destructive/10",
}

function confidenceLabel(confidence: number): { text: string; className: string } {
  if (confidence >= 0.9) return { text: "High", className: "text-success" }
  if (confidence >= 0.7) return { text: "Medium", className: "text-warning" }
  return { text: "Low", className: "text-destructive" }
}

/* ─── Toast ─── */

function CorrectionToast({ visible }: { visible: boolean }) {
  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 8 }}
          transition={{ duration: 0.15 }}
          className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 rounded-lg border border-foreground/8 bg-card/90 backdrop-blur-xl px-4 py-2 text-xs text-muted-foreground shadow-lg"
        >
          Got it — this helps the AI learn.
        </motion.div>
      )}
    </AnimatePresence>
  )
}

/* ─── Inline correction fields ─── */

function CorrectableField({
  currentValue,
  displayValue,
  displayClassName,
  options,
  fieldName,
  itemId,
  onCorrected,
}: {
  currentValue: string | null
  displayValue: string
  displayClassName?: string
  options: { value: string; label: string; className?: string }[]
  fieldName: "sentiment" | "urgency"
  itemId: string
  onCorrected: () => void
}) {
  const [editing, setEditing] = useState(false)
  const [corrected, setCorrected] = useState(false)
  const correction = useSubmitCorrection()

  const handleSelect = async (newValue: string) => {
    if (newValue === currentValue) {
      setEditing(false)
      return
    }
    await correction.mutateAsync({
      feedback_item: itemId,
      field_corrected: fieldName,
      ai_value: currentValue,
      human_value: newValue,
    })
    setEditing(false)
    setCorrected(true)
    onCorrected()
    setTimeout(() => setCorrected(false), 1500)
  }

  return (
    <div className="relative flex items-center gap-1.5">
      <AnimatePresence mode="wait">
        {editing ? (
          <motion.div
            key="selector"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.1 }}
            className="flex items-center gap-1"
          >
            {options.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => handleSelect(opt.value)}
                className={cn(
                  "rounded px-2 py-0.5 text-xs transition-colors cursor-pointer",
                  opt.value === currentValue
                    ? "bg-foreground/10 font-medium"
                    : "hover:bg-foreground/5",
                  opt.className,
                )}
              >
                {opt.label}
              </button>
            ))}
            <button
              type="button"
              onClick={() => setEditing(false)}
              className="ml-1 text-muted-foreground/50 hover:text-muted-foreground cursor-pointer"
            >
              <HugeiconsIcon icon={Cancel01Icon} strokeWidth={2} className="size-3" />
            </button>
          </motion.div>
        ) : (
          <motion.div
            key="display"
            initial={corrected ? { scale: 1.05 } : false}
            animate={{ scale: 1 }}
            transition={{ type: "spring", bounce: 0.3, duration: 0.2 }}
            className="flex items-center gap-1.5 cursor-pointer"
            onClick={() => setEditing(true)}
          >
            <span className={cn("text-sm", displayClassName)}>
              {displayValue}
            </span>
            {corrected ? (
              <motion.span
                initial={{ opacity: 1, scale: 0.8 }}
                animate={{ opacity: 0, scale: 1 }}
                transition={{ duration: 0.6, delay: 0.3 }}
                className="text-success"
              >
                <HugeiconsIcon icon={Tick02Icon} strokeWidth={2} className="size-3.5" />
              </motion.span>
            ) : (
              <HugeiconsIcon
                icon={PencilEdit01Icon}
                strokeWidth={2}
                className="size-4 text-muted-foreground hover:text-foreground transition-colors"
              />
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function CorrectableThemes({
  themes,
  itemId,
  onCorrected,
  onFilterByTheme,
}: {
  themes: string[]
  itemId: string
  onCorrected: () => void
  onFilterByTheme?: (themeSlug: string) => void
}) {
  const [editing, setEditing] = useState(false)
  const [removing, setRemoving] = useState<string | null>(null)
  const [corrected, setCorrected] = useState(false)
  const correction = useSubmitCorrection()

  const handleRemoveTheme = async (theme: string) => {
    setRemoving(theme)
    const newThemes = themes.filter((t) => t !== theme)
    await correction.mutateAsync({
      feedback_item: itemId,
      field_corrected: "themes",
      ai_value: themes,
      human_value: newThemes,
    })
    setRemoving(null)
    setEditing(false)
    setCorrected(true)
    onCorrected()
    setTimeout(() => setCorrected(false), 1500)
  }

  return (
    <div className="group/field flex items-start justify-between py-3">
      <span className="text-xs text-muted-foreground pt-1">
        Themes
      </span>
      <div className="flex flex-wrap gap-1 justify-end items-center max-w-[65%]">
        {themes.map((theme) =>
          !editing && onFilterByTheme ? (
            <button
              key={theme}
              type="button"
              onClick={() => onFilterByTheme(theme)}
              className={cn(
                "inline-flex min-h-6 touch-manipulation items-center gap-1 rounded bg-foreground/8 px-1.5 py-0.5 text-xs font-mono text-muted-foreground transition-colors",
                "cursor-pointer hover:bg-foreground/15 hover:text-foreground",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                removing === theme && "opacity-50",
              )}
              aria-label={`Filter by theme ${theme}`}
            >
              {theme}
            </button>
          ) : (
            <span
              key={theme}
              className={cn(
                "inline-flex items-center gap-1 bg-foreground/8 px-1.5 py-0.5 rounded text-xs font-mono text-muted-foreground",
                removing === theme && "opacity-50",
              )}
            >
              {theme}
              {editing && (
                <button
                  type="button"
                  onClick={() => handleRemoveTheme(theme)}
                  className="text-muted-foreground/40 hover:text-destructive cursor-pointer"
                >
                  <HugeiconsIcon icon={Cancel01Icon} strokeWidth={2} className="size-2.5" />
                </button>
              )}
            </span>
          ),
        )}
        {corrected && (
          <motion.span
            initial={{ opacity: 1, scale: 0.8 }}
            animate={{ opacity: 0, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="text-success"
          >
            <HugeiconsIcon icon={Tick02Icon} strokeWidth={2} className="size-3.5" />
          </motion.span>
        )}
        <button
          type="button"
          onClick={() => setEditing(!editing)}
          className={cn(
            "transition-colors cursor-pointer",
            editing ? "text-muted-foreground" : "text-muted-foreground hover:text-foreground",
          )}
          aria-label="Edit themes"
        >
          <HugeiconsIcon
            icon={editing ? Cancel01Icon : PencilEdit01Icon}
            strokeWidth={2}
            className="size-4"
          />
        </button>
      </div>
    </div>
  )
}

/* ─── Main panel ─── */

export function DetailPanel({ item, onClose, onFilterByTheme }: DetailPanelProps) {
  const [toastVisible, setToastVisible] = useState(false)

  const showToast = () => {
    setToastVisible(true)
    setTimeout(() => setToastVisible(false), 2000)
  }

  const conf = item.sentiment_confidence != null ? confidenceLabel(item.sentiment_confidence) : null

  return (
    <>
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.15 }}
        className="fixed inset-0 z-40 bg-background/40 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Panel */}
      <motion.aside
        initial={{ x: "100%" }}
        animate={{ x: 0 }}
        exit={{ x: "100%" }}
        transition={{ duration: 0.2, ease: [0.23, 1, 0.32, 1] }}
        className="fixed right-0 top-0 bottom-0 z-50 w-[440px] max-w-full overflow-y-auto border-l border-foreground/8 bg-card/80 backdrop-blur-xl"
      >
        <div className="p-6">
          {/* Header */}
          <div className="flex items-start justify-between mb-2">
            <h2 className="text-lg font-medium tracking-tight text-foreground">
              Feedback
            </h2>
            <Button
              variant="ghost"
              size="icon-xs"
              onClick={onClose}
              aria-label="Close panel"
            >
              <HugeiconsIcon icon={Cancel01Icon} strokeWidth={2} />
            </Button>
          </div>

          {/* Source + time context line */}
          <p className="text-sm text-muted-foreground mb-6">
            {item.source_name}{item.author ? ` · ${item.author}` : ""} · {formatRelativeTime(item.received_at)}
          </p>

          {/* User's voice — the centerpiece */}
          <blockquote className="text-base leading-[1.7] text-foreground mb-10 border-l-2 border-primary/30 pl-4">
            {item.content}
          </blockquote>

          {/* AI Analysis */}
          <section className="mb-10">
            <h3 className="text-sm font-medium text-foreground mb-4">
              AI Analysis
            </h3>

            {/* Summary — what the user wants first */}
            {item.ai_summary && (
              <p className="mb-4 text-sm text-foreground leading-relaxed">
                {item.ai_summary}
              </p>
            )}

            {/* Classification — correctable */}
            <div className="rounded-lg border border-foreground/5 px-4">
              <div className="group/field flex items-center justify-between py-3">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">Sentiment</span>
                  {conf && (
                    <span className="text-xs font-mono text-muted-foreground tabular-nums">
                      {Math.round(item.sentiment_confidence! * 100)}%
                    </span>
                  )}
                </div>
                <CorrectableField
                  currentValue={item.sentiment}
                  displayValue={item.sentiment ?? "Unclassified"}
                  displayClassName={
                    item.sentiment
                      ? cn("rounded-full px-2 py-0.5", SENTIMENT_STYLES[item.sentiment].text, SENTIMENT_STYLES[item.sentiment].bg)
                      : "text-muted-foreground/50"
                  }
                  options={SENTIMENT_OPTIONS}
                  fieldName="sentiment"
                  itemId={item.id}
                  onCorrected={showToast}
                />
              </div>

              <div className="border-t border-foreground/5" />

              <div className="group/field flex items-center justify-between py-3">
                <span className="text-sm text-muted-foreground">Urgency</span>
                <CorrectableField
                  currentValue={item.urgency}
                  displayValue={item.urgency ?? "Unclassified"}
                  displayClassName={
                    item.urgency
                      ? cn("rounded-full px-2 py-0.5", URGENCY_STYLES[item.urgency])
                      : "text-muted-foreground/50"
                  }
                  options={URGENCY_OPTIONS}
                  fieldName="urgency"
                  itemId={item.id}
                  onCorrected={showToast}
                />
              </div>

              {item.themes && item.themes.length > 0 && (
                <>
                  <div className="border-t border-foreground/5" />
                  <CorrectableThemes
                    themes={item.themes}
                    itemId={item.id}
                    onCorrected={showToast}
                    onFilterByTheme={onFilterByTheme}
                  />
                </>
              )}
            </div>
          </section>

        </div>
      </motion.aside>

      <CorrectionToast visible={toastVisible} />
    </>
  )
}
