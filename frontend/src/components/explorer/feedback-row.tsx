import { cn, formatRelativeTime } from "@/lib/utils"
import { motion } from "motion/react"
import type { FeedbackItem } from "@/types/api"

type FeedbackRowProps = {
  item: FeedbackItem
  index: number
  isSelected: boolean
  onClick: () => void
}

const SENTIMENT_STYLES: Record<string, string> = {
  positive: "text-success",
  negative: "text-destructive",
  neutral: "text-muted-foreground",
  mixed: "text-warning",
}

export function FeedbackRow({ item, index, isSelected, onClick }: FeedbackRowProps) {
  return (
    <motion.button
      type="button"
      initial={{ opacity: 0, x: -6 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{
        duration: 0.25,
        delay: index * 0.06,
        ease: [0.23, 1, 0.32, 1],
      }}
      onClick={onClick}
      className={cn(
        "group relative w-full text-left py-4 pl-4 pr-3 cursor-pointer transition-colors duration-100",
        "hover:bg-foreground/[0.02]",
        "focus-visible:outline-none focus-visible:bg-foreground/[0.03]",
      )}
    >
      {/* Left accent bar */}
      <span
        className={cn(
          "absolute left-0 top-3 bottom-3 w-0.5 rounded-full bg-primary transition-opacity duration-150",
          isSelected ? "opacity-100" : "opacity-0 group-hover:opacity-100",
        )}
      />

      {/* Content — the user's voice */}
      <p className="text-[15px] leading-relaxed text-foreground line-clamp-3">
        {item.content}
      </p>

      {/* Metadata row */}
      <div className="mt-2 flex items-center gap-2 text-[11px] tracking-wide">
        {/* Sentiment as colored text */}
        {item.sentiment && (
          <>
            <span className={cn("font-medium", SENTIMENT_STYLES[item.sentiment])}>
              {item.sentiment}
            </span>
            <span className="text-muted-foreground/30" aria-hidden>&middot;</span>
          </>
        )}

        {/* Theme tags */}
        {item.themes && item.themes.length > 0 && (
          <>
            <span className="flex items-center gap-1">
              {item.themes.slice(0, 3).map((theme) => (
                <span
                  key={theme}
                  className="bg-foreground/8 px-1.5 py-px rounded text-[10px] font-mono text-muted-foreground"
                >
                  {theme}
                </span>
              ))}
              {item.themes.length > 3 && (
                <span className="text-[10px] text-muted-foreground/50">
                  +{item.themes.length - 3}
                </span>
              )}
            </span>
            <span className="text-muted-foreground/30" aria-hidden>&middot;</span>
          </>
        )}

        {/* Source + time */}
        <span className="text-muted-foreground/70">{item.source_name}</span>
        <span className="text-muted-foreground/30" aria-hidden>&middot;</span>
        <span className="text-muted-foreground/70">
          {formatRelativeTime(item.received_at)}
        </span>
      </div>
    </motion.button>
  )
}
