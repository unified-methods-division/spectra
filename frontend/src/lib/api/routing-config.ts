import {
  useMutation,
  useQueries,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"
import { apiGet, apiPut } from "@/lib/api"

export interface RoutingConfig {
  id: string
  source: string
  confidence_threshold: number
  items_below_threshold_action: "flag" | "skip_ai"
  updated_at: string
  flagged_preview_count: number
}

const routingKey = (sourceId: string) => ["routing-config", sourceId] as const

function routingConfigQueryOptions(sourceId: string) {
  return {
    queryKey: routingKey(sourceId),
    queryFn: () =>
      apiGet<RoutingConfig>(`/api/ingestion/sources/${sourceId}/routing-config/`),
  }
}

/** One query. Prefer `useRoutingConfigsForSourceIds` when listing many sources. */
export function useRoutingConfig(sourceId: string | undefined) {
  return useQuery({
    ...routingConfigQueryOptions(sourceId!),
    enabled: !!sourceId,
  })
}

/** Parallel fetches; stable `queryKey` per id matches `useRoutingConfig` for invalidation. */
export function useRoutingConfigsForSourceIds(sourceIds: string[]) {
  return useQueries({
    queries: sourceIds.map((id) => routingConfigQueryOptions(id)),
  })
}

type UpdateParams = { sourceId: string; confidence_threshold: number }

export function useUpdateRoutingConfig() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ sourceId, confidence_threshold }: UpdateParams) =>
      apiPut<RoutingConfig>(
        `/api/ingestion/sources/${sourceId}/routing-config/`,
        { confidence_threshold },
      ),
    onSuccess: (_data, { sourceId }) => {
      void qc.invalidateQueries({ queryKey: routingKey(sourceId) })
    },
  })
}

