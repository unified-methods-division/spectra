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

export function useTaskStatus(taskId: string | null) {
  return useQuery({
    queryKey: ["tasks", taskId],
    queryFn: () => apiGet<TaskStatus>(`/api/ingestion/uploads/tasks/${taskId}/`),
    enabled: !!taskId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
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
