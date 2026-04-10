import { useRouteError, isRouteErrorResponse, Link } from "react-router"
import { motion } from "motion/react"
import { Button } from "@/components/ui/button"

function ErrorPage({ code, title, message }: { code: string; title: string; message: string }) {
  return (
    <div className="flex min-h-svh bg-background">
      <div className="relative flex flex-1 flex-col">
        <div className="relative h-72 overflow-hidden">
          <img
            src="https://images.unsplash.com/photo-1620641788421-7a1c342ea42e?w=1400&q=80&auto=format&fit=crop"
            alt=""
            className="h-full w-full object-cover saturate-50"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-background/20 via-transparent to-background" />
        </div>

        <div className="relative -mt-32 flex flex-1 items-start justify-center">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
            className="flex flex-col items-center gap-6 rounded-xl border border-foreground/8 bg-card/80 px-16 py-12 text-center backdrop-blur-xl"
          >
            <span className="font-mono text-7xl font-extralight tracking-tighter text-primary/40">
              {code}
            </span>
            <div className="flex flex-col gap-1">
              <p className="text-sm font-medium text-foreground">{title}</p>
              <p className="max-w-xs text-sm text-muted-foreground">{message}</p>
            </div>
            <Button variant="outline" size="sm" render={<Link to="/sources" />}>
              Back to Sources
            </Button>
          </motion.div>
        </div>
      </div>
    </div>
  )
}

export function ErrorBoundary() {
  const error = useRouteError()
  const is404 = isRouteErrorResponse(error) && error.status === 404

  return is404
    ? <ErrorPage code="404" title="Page not found" message="The page you're looking for doesn't exist or has been moved." />
    : <ErrorPage code="500" title="Something broke" message="An unexpected error occurred. Try refreshing the page." />
}

export function NotFound() {
  return <ErrorPage code="404" title="Page not found" message="The page you're looking for doesn't exist or has been moved." />
}
