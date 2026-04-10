import { useState } from "react"
import { AnimatePresence, motion } from "motion/react"
import { useFeedbackItems, type ExplorerFilters } from "@/hooks/use-explorer"
import { useSources } from "@/hooks/use-sources"
import { FilterBar } from "@/components/explorer/filter-bar"
import { FeedbackRow } from "@/components/explorer/feedback-row"
import { DetailPanel } from "@/components/explorer/detail-panel"
import { Button } from "@/components/ui/button"
import type { FeedbackItem } from "@/types/api"

export function ExplorerPage() {
  const [filters, setFilters] = useState<ExplorerFilters>({ page: 1 })
  const [selectedItem, setSelectedItem] = useState<FeedbackItem | null>(null)

  const { data, isLoading, error } = useFeedbackItems(filters)
  const { data: sources } = useSources()

  const totalPages = data ? Math.ceil(data.count / 20) : 0
  const currentPage = filters.page ?? 1

  return (
    <div>
      {/* Masthead */}
      <div className="relative">
        <div className="h-72">
          <img
            src="https://images.unsplash.com/photo-1730047614287-65e28e013ce1?q=80&w=1782&auto=format&fit=crop"
            alt=""
            className="h-full w-full object-cover"
          />
          <div className="absolute inset-0 bg-linear-to-b from-background/60 via-background/20 to-background" />
        </div>
      </div>

      {/* Content */}
      <div className="relative -mt-24 mx-auto max-w-3xl px-10">
        {/* Heading */}
        <div className="mb-8">
          <span className="text-xs font-medium tracking-[0.2em] text-foreground/80 uppercase">
            Feedback Explorer
          </span>
          <h1 className="text-3xl font-normal tracking-tight text-foreground">
            What your customers are saying
          </h1>
        </div>

        {/* Filters — sticky on scroll */}
        <div className="sticky top-0 z-30 -mx-10 px-10 py-3 bg-background/80 backdrop-blur-xl">
          <FilterBar
            filters={filters}
            onChange={setFilters}
            sources={sources ?? []}
          />
        </div>

        {/* Result count — section label */}
        {data && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.15 }}
            className="mt-8 mb-2 text-xs font-medium tracking-[0.15em] text-muted-foreground/50 uppercase"
          >
            {data.count.toLocaleString()} result{data.count !== 1 ? "s" : ""}
          </motion.p>
        )}

        {/* Loading */}
        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.2 }}
            className="flex flex-col items-center gap-4 py-20"
          >
            <div className="flex gap-1">
              {[0, 1, 2].map((i) => (
                <motion.span
                  key={i}
                  className="size-1.5 rounded-full bg-primary/40"
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{ duration: 2, repeat: Infinity, delay: i * 0.3 }}
                />
              ))}
            </div>
            <p className="text-sm text-muted-foreground">Loading feedback...</p>
          </motion.div>
        )}

        {/* Error */}
        {error && (
          <p className="py-8 text-center text-sm text-destructive">
            Couldn't reach the backend.
          </p>
        )}

        {/* Feed */}
        {data && data.results.length > 0 && (
          <div className="divide-y divide-border">
            {data.results.map((item, i) => (
              <FeedbackRow
                key={item.id}
                item={item}
                index={i}
                isSelected={selectedItem?.id === item.id}
                onClick={() => setSelectedItem(item)}
              />
            ))}
          </div>
        )}

        {/* Empty */}
        {data && data.results.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.15, duration: 0.3 }}
            className="flex flex-col items-center gap-2 py-20"
          >
            <p className="text-sm text-muted-foreground">No feedback found</p>
            <p className="text-xs text-muted-foreground/70">
              Try adjusting your filters or search.
            </p>
          </motion.div>
        )}

        {/* Pagination */}
        {data && totalPages > 1 && (
          <div className="flex items-center justify-between pt-4 mt-2 border-t border-border">
            <Button
              variant="ghost"
              size="sm"
              onClick={() =>
                setFilters((f) => ({ ...f, page: currentPage - 1 }))
              }
              disabled={currentPage <= 1}
              className="text-xs"
            >
              Previous
            </Button>
            <span className="text-xs text-muted-foreground tabular-nums font-mono">
              {currentPage} / {totalPages}
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() =>
                setFilters((f) => ({ ...f, page: currentPage + 1 }))
              }
              disabled={!data.next}
              className="text-xs"
            >
              Next
            </Button>
          </div>
        )}
      </div>

      {/* Detail panel */}
      <AnimatePresence>
        {selectedItem && (
          <DetailPanel
            item={selectedItem}
            onClose={() => setSelectedItem(null)}
          />
        )}
      </AnimatePresence>
    </div>
  )
}
