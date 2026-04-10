import { useCallback, useEffect, useRef, useState } from "react"
import { cn } from "@/lib/utils"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { HugeiconsIcon } from "@hugeicons/react"
import { Cancel01Icon, Search01Icon } from "@hugeicons/core-free-icons"
import { motion, AnimatePresence } from "motion/react"
import type { ExplorerFilters } from "@/hooks/use-explorer"
import type { Source } from "@/types/api"

type FilterBarProps = {
  filters: ExplorerFilters
  onChange: (filters: ExplorerFilters) => void
  sources: Source[]
}

const SENTIMENT_OPTIONS = [
  { value: "positive", label: "Positive", className: "text-success" },
  { value: "negative", label: "Negative", className: "text-destructive" },
  { value: "neutral", label: "Neutral", className: "text-muted-foreground" },
  { value: "mixed", label: "Mixed", className: "text-warning" },
] as const

type ActiveFilter = {
  key: keyof ExplorerFilters
  label: string
}

function getActiveFilters(filters: ExplorerFilters, sources: Source[]): ActiveFilter[] {
  const active: ActiveFilter[] = []
  if (filters.sentiment) {
    active.push({
      key: "sentiment",
      label: filters.sentiment.charAt(0).toUpperCase() + filters.sentiment.slice(1),
    })
  }
  if (filters.source) {
    const src = sources.find((s) => s.id === filters.source)
    active.push({ key: "source", label: src?.name ?? "Source" })
  }
  if (filters.date_from) {
    active.push({ key: "date_from", label: `From ${filters.date_from}` })
  }
  if (filters.date_to) {
    active.push({ key: "date_to", label: `Until ${filters.date_to}` })
  }
  return active
}

export function FilterBar({ filters, onChange, sources }: FilterBarProps) {
  const [searchValue, setSearchValue] = useState(filters.search ?? "")
  const debounceRef = useRef<ReturnType<typeof setTimeout>>()

  const handleSearchChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value
      setSearchValue(value)

      if (debounceRef.current) clearTimeout(debounceRef.current)
      debounceRef.current = setTimeout(() => {
        onChange({ ...filters, search: value || undefined, page: 1 })
      }, 300)
    },
    [filters, onChange],
  )

  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [])

  const activeFilters = getActiveFilters(filters, sources)

  const clearFilter = (key: keyof ExplorerFilters) => {
    const next = { ...filters, page: 1 }
    delete next[key]
    onChange(next)
  }

  return (
    <div className="space-y-3">
      {/* Search */}
      <div className="relative">
        <HugeiconsIcon
          icon={Search01Icon}
          strokeWidth={1.5}
          className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground/50"
        />
        <Input
          value={searchValue}
          onChange={handleSearchChange}
          placeholder="What are users saying about..."
          className="pl-9 h-10 text-[15px]"
        />
      </div>

      {/* Filter row */}
      <div className="flex items-center gap-2">
        {/* Sentiment */}
        <Select
          value={filters.sentiment ?? ""}
          onValueChange={(val) =>
            onChange({
              ...filters,
              sentiment: val || undefined,
              page: 1,
            })
          }
        >
          <SelectTrigger size="sm" className="text-xs">
            <SelectValue placeholder="Sentiment" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">All sentiments</SelectItem>
            {SENTIMENT_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                <span className="flex items-center gap-2">
                  <span
                    className={cn(
                      "size-1.5 rounded-full",
                      opt.value === "positive" && "bg-success",
                      opt.value === "negative" && "bg-destructive",
                      opt.value === "neutral" && "bg-muted-foreground",
                      opt.value === "mixed" && "bg-warning",
                    )}
                  />
                  {opt.label}
                </span>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Source */}
        <Select
          value={filters.source ?? ""}
          onValueChange={(val) =>
            onChange({ ...filters, source: val || undefined, page: 1 })
          }
        >
          <SelectTrigger size="sm" className="text-xs">
            <SelectValue placeholder="Source" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">All sources</SelectItem>
            {sources.map((src) => (
              <SelectItem key={src.id} value={src.id}>
                {src.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Date from */}
        <Input
          type="date"
          value={filters.date_from ?? ""}
          onChange={(e) =>
            onChange({
              ...filters,
              date_from: e.target.value || undefined,
              page: 1,
            })
          }
          className="h-8 w-auto text-xs text-muted-foreground"
          aria-label="From date"
        />

        {/* Date to */}
        <Input
          type="date"
          value={filters.date_to ?? ""}
          onChange={(e) =>
            onChange({
              ...filters,
              date_to: e.target.value || undefined,
              page: 1,
            })
          }
          className="h-8 w-auto text-xs text-muted-foreground"
          aria-label="Until date"
        />
      </div>

      {/* Active filter chips */}
      <AnimatePresence>
        {activeFilters.length > 0 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.97 }}
            transition={{ duration: 0.1 }}
            className="flex flex-wrap gap-1.5"
          >
            {activeFilters.map((f) => (
              <motion.button
                key={f.key}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ duration: 0.1 }}
                onClick={() => clearFilter(f.key)}
                className="inline-flex items-center gap-1 rounded-md bg-foreground/8 px-2 py-0.5 text-[11px] text-muted-foreground transition-colors hover:bg-foreground/12 hover:text-foreground cursor-pointer"
              >
                {f.label}
                <HugeiconsIcon icon={Cancel01Icon} strokeWidth={2} className="size-3" />
              </motion.button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
