import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { apiGet, apiPost } from "@/lib/api"
import type { Theme } from "@/types/api"

export function useThemes() {
  return useQuery({
    queryKey: ["themes"],
    queryFn: () => apiGet<Theme[]>("/api/themes/"),
  })
}

export function useDiscoverThemes() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => apiPost("/api/themes/discover/"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["themes"] }),
  })
}
