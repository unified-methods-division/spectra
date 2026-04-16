import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { apiGet, apiPost, apiUpload } from "@/lib/api"
import type {
  Source,
  UploadResponse,
  TaskStatus,
  ProcessingStatus,
} from "@/types/api"

export function useSources() {
  return useQuery({
    queryKey: ["sources"],
    queryFn: () => apiGet<Source[]>("/api/ingestion/sources/"),
  })
}

export function useCreateSource() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { name: string; source_type: string }) =>
      apiPost<Source>("/api/ingestion/sources/", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources"] }),
  })
}

export function useUploadFile(sourceId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (file: File) => {
      const fd = new FormData()
      fd.append("file", file)
      return apiUpload<UploadResponse>(
        `/api/ingestion/sources/${sourceId}/uploads/`,
        fd,
      )
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources"] }),
  })
}

type UseTaskStatusOptions = {
  /** When the task reaches `success`, invalidates list + processing polling for this source. */
  sourceId?: string | null
}

export function useTaskStatus(taskId: string | null, options?: UseTaskStatusOptions) {
  const qc = useQueryClient()
  const sourceId = options?.sourceId ?? null

  return useQuery({
    queryKey: ["tasks", taskId],
    queryFn: async ({ signal }) => {
      const data = await apiGet<TaskStatus>(
        `/api/ingestion/uploads/tasks/${taskId}/`,
        { signal },
      )
      if (data.status === "success" && sourceId) {
        await Promise.all([
          qc.invalidateQueries({ queryKey: ["sources"] }),
          qc.invalidateQueries({ queryKey: ["processing-status", sourceId] }),
        ])
      }
      return data
    },
    enabled: !!taskId,
    refetchInterval: (q) => {
      const status = q.state.data?.status
      if (status === "success" || status === "failure") return false
      return 2000
    },
  })
}

export function useProcessingStatus(sourceId: string) {
  return useQuery({
    queryKey: ["processing-status", sourceId],
    queryFn: () =>
      apiGet<ProcessingStatus>(
        `/api/analysis/sources/${sourceId}/processing-status/`,
      ),
    refetchInterval: (query) => {
      const status = query.state.data?.overall_status
      if (status === "completed" || status === "failed") return false
      return 5000
    },
  })
}
