import { motion } from "motion/react"
import { useThemes, useDiscoverThemes } from "@/hooks/use-themes"
import { ThemeCard } from "@/components/themes/theme-card"
import { Button } from "@/components/ui/button"
import { HugeiconsIcon } from "@hugeicons/react"
import { AiSearchIcon, Loading03Icon } from "@hugeicons/core-free-icons"

export function ThemesPage() {
  const { data: themes, isLoading, error } = useThemes()
  const discover = useDiscoverThemes()

  return (
    <div>
      {/* Masthead */}
      <div className="relative">
        <div className="h-72">
          <img
            src="https://images.unsplash.com/photo-1507925921958-8a62f3d1a50d?w=1400&q=80&auto=format&fit=crop"
            alt=""
            className="h-full w-full object-cover"
          />
          <div className="absolute inset-0 bg-linear-to-b from-background/40 via-background/10 to-background" />
        </div>
      </div>

      {/* Content */}
      <div className="relative -mt-24 mx-auto max-w-3xl px-10">
        {/* Header */}
        <div className="flex items-end justify-between mb-5">
          <div>
            <span className="text-xs font-medium tracking-[0.2em] text-foreground/80 uppercase">
              Theme Discovery
            </span>
            <h1 className="text-3xl font-normal tracking-tight text-foreground">
              What patterns live in your data
            </h1>
          </div>
          <Button
            onClick={() => discover.mutate()}
            disabled={discover.isPending}
            size="sm"
            variant="outline"
          >
            {discover.isPending ? (
              <HugeiconsIcon
                icon={Loading03Icon}
                className="animate-spin"
                data-icon="inline-start"
                strokeWidth={2}
              />
            ) : (
              <HugeiconsIcon
                icon={AiSearchIcon}
                data-icon="inline-start"
                strokeWidth={2}
              />
            )}
            {discover.isPending ? "Discovering\u2026" : "Discover themes"}
          </Button>
        </div>

        {/* Panel */}
        <div className="rounded-xl border border-foreground/8 bg-card/80 backdrop-blur-xl p-5">
          {/* Loading */}
          {isLoading && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <div
                  key={i}
                  className="rounded-xl border border-foreground/5 bg-muted/30 p-4 animate-pulse"
                >
                  <div className="h-3.5 w-2/3 rounded bg-muted" />
                  <div className="mt-2.5 h-2.5 w-full rounded bg-muted/70" />
                  <div className="mt-1.5 h-2.5 w-4/5 rounded bg-muted/50" />
                  <div className="mt-4 flex justify-between">
                    <div className="h-2.5 w-14 rounded bg-muted/50" />
                    <div className="h-2.5 w-10 rounded bg-muted/30" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Error */}
          {error && (
            <p className="py-8 text-center text-sm text-destructive">
              Couldn't load themes. Check that the backend is running.
            </p>
          )}

          {/* Empty */}
          {themes && themes.length === 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.15, duration: 0.3 }}
              className="flex flex-col items-center gap-2 py-16"
            >
              <HugeiconsIcon
                icon={AiSearchIcon}
                className="size-8 text-muted-foreground/30"
                strokeWidth={1.5}
              />
              <p className="text-sm text-muted-foreground">
                No themes discovered yet
              </p>
              <p className="text-xs text-muted-foreground/60 max-w-[40ch] text-center">
                Run discovery to find patterns in your feedback. Themes are
                clustered from embeddings and named by an LLM.
              </p>
            </motion.div>
          )}

          {/* Theme grid */}
          {themes && themes.length > 0 && (
            <>
              <p className="mb-3 text-xs font-medium tracking-[0.15em] text-muted-foreground/50 uppercase">
                {themes.length} theme{themes.length !== 1 ? "s" : ""}
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {themes.map((theme, i) => (
                  <ThemeCard key={theme.id} theme={theme} index={i} />
                ))}
              </div>
            </>
          )}
        </div>

        {/* Discovery status toast */}
        {discover.isSuccess && (
          <motion.p
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-3 text-center text-xs text-success"
          >
            Discovery complete. Themes refreshed.
          </motion.p>
        )}
      </div>
    </div>
  )
}
