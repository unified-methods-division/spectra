import { cn, formatRelativeTime } from "@/lib/utils"
import { themeFilterChipLabels } from "@/lib/theme-filter-chip"
import { motion } from "motion/react"
import type { FeedbackItem } from "@/types/api"
import type { KeyboardEvent } from "react"

type FeedbackRowProps = {
  item: FeedbackItem
  index: number
  isSelected: boolean
  onClick: () => void
  /** Theme values are slugs; updates explorer `?theme=` when set */
  onThemeClick?: (themeSlug: string) => void
  /** When set, richer `aria-label` / `title` use Theme.name for each slug */
  themeNameBySlug?: Record<string, string>
  /** Current `?theme=` filter; chip gets `aria-current` when it matches */
  activeThemeSlug?: string | null
}

const SENTIMENT_STYLES: Record<string, { text: string; bg: string }> = {
  positive: { text: "text-success", bg: "bg-success/10" },
  negative: { text: "text-destructive", bg: "bg-destructive/10" },
  neutral: { text: "text-muted-foreground", bg: "bg-muted" },
  mixed: { text: "text-warning", bg: "bg-warning/10" },
}

export function FeedbackRow({
  item,
  index,
  isSelected,
  onClick,
  onThemeClick,
  themeNameBySlug,
  activeThemeSlug,
}: FeedbackRowProps) {
  const sentiment = item.sentiment ? SENTIMENT_STYLES[item.sentiment] : null

  const handleRowKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key !== "Enter" && e.key !== " ") return
    e.preventDefault()
    onClick()
  }

  return (
    <motion.div
      role="button"
      tabIndex={0}
      initial={{ opacity: 0, x: -6 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{
        duration: 0.25,
        delay: index * 0.06,
        ease: [0.23, 1, 0.32, 1],
      }}
      onClick={onClick}
      onKeyDown={handleRowKeyDown}
      className={cn(
        "group relative w-full text-left py-5 pl-4 pr-3 cursor-pointer transition-colors duration-100",
        "hover:bg-foreground/[0.02]",
        "focus-visible:outline-none focus-visible:bg-foreground/[0.03]",
      )}
    >
      {/* Left accent bar */}
      <span
        className={cn(
          "absolute left-0 top-4 bottom-4 w-0.5 rounded-full bg-primary transition-opacity duration-150",
          isSelected ? "opacity-100" : "opacity-0 group-hover:opacity-100",
        )}
      />

      {/* Content — the user's voice, dominant element */}
      <p className="text-base leading-[1.6] text-foreground line-clamp-3">
        {item.content}
      </p>

      {/* Metadata row */}
      <div className="mt-2.5 flex items-center gap-2 text-xs tracking-wide">
        {/* Sentiment: dot + label */}
        {sentiment && (
          <>
            <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium", sentiment.text, sentiment.bg)}>
              {item.sentiment}
            </span>
            <span className="text-muted-foreground/40" aria-hidden>&middot;</span>
          </>
        )}

        {/* Theme tags */}
        {item.themes && item.themes.length > 0 && (
          <>
            <span
              className="flex items-center gap-1"
              role="group"
              aria-label="Themes on this feedback. Each button filters the list."
            >
              {item.themes.slice(0, 3).map((theme) =>
                onThemeClick ? (
                  <button
                    key={theme}
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation()
                      onThemeClick(theme)
                    }}
                    className={cn(
                      "min-h-6 min-w-6 touch-manipulation rounded px-1.5 py-px text-left text-xs font-mono text-muted-foreground",
                      "bg-foreground/8 transition-colors cursor-pointer [-webkit-tap-highlight-color:transparent]",
                      "hover:bg-foreground/15 hover:text-foreground",
                      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                      activeThemeSlug === theme &&
                        "bg-primary/15 text-foreground ring-1 ring-primary/30",
                    )}
                    {...themeFilterChipLabels(theme, themeNameBySlug?.[theme])}
                    aria-current={activeThemeSlug === theme ? true : undefined}
                  >
                    {theme}
                  </button>
                ) : (
                  <span
                    key={theme}
                    className="bg-foreground/8 px-1.5 py-px rounded text-xs font-mono text-muted-foreground"
                  >
                    {theme}
                  </span>
                ),
              )}
              {item.themes.length > 3 && (
                <span
                  className="text-xs text-muted-foreground/50"
                  title={`${item.themes.length - 3} more theme${item.themes.length - 3 === 1 ? "" : "s"} on this item — open the row for the full list.`}
                >
                  +{item.themes.length - 3}
                </span>
              )}
            </span>
            <span className="text-muted-foreground/40" aria-hidden>&middot;</span>
          </>
        )}

        {/* Source + time */}
        <span className="text-muted-foreground">{item.source_name}</span>
        <span className="text-muted-foreground/40" aria-hidden>&middot;</span>
        <span className="text-muted-foreground">
          {formatRelativeTime(item.received_at)}
        </span>
      </div>
    </motion.div>
  )
}
