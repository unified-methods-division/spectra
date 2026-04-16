import { motion } from "motion/react"
import { Link } from "react-router"
import { cn } from "@/lib/utils"
import { formatRelativeTime } from "@/lib/utils"
import type { Theme } from "@/types/api"

type Props = {
  theme: Theme
  index: number
}

export function ThemeCard({ theme, index }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.25,
        delay: index * 0.04,
        ease: [0.23, 1, 0.32, 1],
      }}
      className={cn(
        "group rounded-xl border border-foreground/8 bg-card p-4",
        "transition-all duration-150",
        "hover:-translate-y-px hover:shadow-md hover:shadow-black/3",
        "active:scale-[0.98]",
      )}
    >
      {/* Top row — name + source badge */}
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-sm font-medium text-foreground leading-snug">
          {theme.name}
        </h3>
        <SourceBadge source={theme.source} />
      </div>

      {/* Description */}
      {theme.description && (
        <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground line-clamp-2">
          {theme.description}
        </p>
      )}

      {/* Bottom row — item count + first seen */}
      <div className="mt-3 flex items-center justify-between gap-2">
        <span className="text-xs font-mono tabular-nums text-muted-foreground/70">
          {theme.item_count.toLocaleString()}&nbsp;item{theme.item_count !== 1 ? "s" : ""}
        </span>
        {theme.first_seen_at && (
          <span className="text-xs text-muted-foreground/50">
            {formatRelativeTime(theme.first_seen_at)}
          </span>
        )}
      </div>

      <Link
        to={`/explorer?theme=${encodeURIComponent(theme.slug)}`}
        className="mt-3 inline-flex text-xs font-medium text-primary underline-offset-2 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-sm"
      >
        Open in Explorer
      </Link>
    </motion.div>
  )
}

function SourceBadge({ source }: { source: Theme["source"] }) {
  if (source === "discovered") {
    return (
      <span className="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-accent px-2 py-0.5 text-[10px] font-medium tracking-wide text-accent-foreground">
        <span
          className="size-1.5 rounded-full bg-success"
          style={{ animation: "glow-pulse 2.5s ease-in-out infinite" }}
        />
        discovered
      </span>
    )
  }

  return (
    <span className="inline-flex shrink-0 items-center rounded-full border border-foreground/8 px-2 py-0.5 text-[10px] font-medium tracking-wide text-muted-foreground">
      manual
    </span>
  )
}
