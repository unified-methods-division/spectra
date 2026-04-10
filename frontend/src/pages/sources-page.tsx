import { useState } from "react"
import { AnimatePresence, LayoutGroup, motion } from "motion/react"
import { useSources } from "@/hooks/use-sources"
import SourcesList from "@/components/sources-list"
import { CreateSourceForm } from "@/components/create-source-form"
import { Button } from "@/components/ui/button"
import { HugeiconsIcon } from "@hugeicons/react"
import { Add01Icon } from "@hugeicons/core-free-icons"

export function SourcesPage() {
  const { data: sources, isLoading, error } = useSources()
  const [showCreate, setShowCreate] = useState(false)
  const [uploadSourceId, setUploadSourceId] = useState<string | null>(null)

  return (
    <div>
      {/* Masthead — full bleed */}
      <div className="relative">
        <div className="h-72">
          <img
            src="https://images.unsplash.com/photo-1620641788421-7a1c342ea42e?w=1400&q=80&auto=format&fit=crop"
            alt=""
            className="h-full w-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-background/20 via-transparent to-background" />
        </div>
      </div>

      {/* Content — overlaps the masthead */}
      <div className="relative -mt-24 mx-auto max-w-2xl px-10">
        <div className="flex items-center justify-between mb-5">
          <h1 className="text-3xl font-normal tracking-tight text-foreground">
            Sources
          </h1>
          {!showCreate && (
            <Button onClick={() => setShowCreate(true)} size="sm" variant="outline">
              <HugeiconsIcon
                icon={Add01Icon}
                data-icon="inline-start"
                strokeWidth={2}
              />
              Add source
            </Button>
          )}
        </div>

        <div className="rounded-xl border border-foreground/8 bg-card/80 backdrop-blur-xl p-5">
          <LayoutGroup>
            <AnimatePresence>
              {showCreate && (
                <motion.div
                  key="create-form"
                  layout
                  initial={{ opacity: 0, scale: 0.97 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.97 }}
                  style={{ originY: 0 }}
                  transition={{ duration: 0.15, ease: [0.23, 1, 0.32, 1] }}
                  className="mb-4"
                >
                  <CreateSourceForm onDone={() => setShowCreate(false)} />
                </motion.div>
              )}
            </AnimatePresence>

            <motion.div layout transition={{ duration: 0.2, ease: [0.23, 1, 0.32, 1] }}>
              {isLoading && (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.3, duration: 0.2 }}
                  className="py-8 text-center text-xs text-muted-foreground"
                >
                  Loading sources...
                </motion.p>
              )}

              {error && (
                <p className="py-8 text-center text-sm text-destructive">
                  Couldn't reach the backend.
                </p>
              )}

              {sources && (
                <SourcesList
                  sources={sources}
                  uploadingSourceId={uploadSourceId}
                  onUpload={setUploadSourceId}
                />
              )}
            </motion.div>
          </LayoutGroup>
        </div>
      </div>
    </div>
  )
}
