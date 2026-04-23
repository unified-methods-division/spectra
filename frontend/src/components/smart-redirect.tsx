import { Navigate } from "react-router"
import { useSources } from "@/hooks/use-sources"

export function SmartRedirect() {
  const { data: sources, isLoading } = useSources()

  if (isLoading) return null
  if (!sources || sources.length === 0) return <Navigate to="/sources" replace />
  return <Navigate to="/dashboard" replace />
}