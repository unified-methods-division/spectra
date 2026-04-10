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
          <div className="absolute inset-0 bg-gradient-to-b from-background/20 via-transparent to-background" />
        </div>
      </div>

      {/* Content */}
      <div className="relative -mt-24 mx-auto max-w-4xl px-10">
        <div className="mb-5">
          <h1 className="text-3xl font-normal tracking-tight text-foreground">
            Explorer
          </h1>
        </div>

        <div className="rounded-xl border border-foreground/8 bg-card/80 backdrop-blur-xl p-5">
          {/* Filters */}
          <FilterBar
            filters={filters}
            onChange={setFilters}
            sources={sources ?? []}
          />

          {/* Result count */}
          {data && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.15 }}
              className="mt-4 mb-1 text-[11px] tracking-wide text-muted-foreground/70"
            >
              {data.count.toLocaleString()} conversation{data.count !== 1 ? "s" : ""}
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
              <p className="text-sm text-muted-foreground">Loading conversations...</p>
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
              <p className="text-sm text-muted-foreground">No conversations found</p>
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
              <span className="text-[11px] text-muted-foreground tabular-nums font-mono">
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
