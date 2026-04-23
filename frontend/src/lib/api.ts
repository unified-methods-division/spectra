const BASE_URL = import.meta.env.VITE_API_URL ?? ""
const TENANT_ID = import.meta.env.VITE_TENANT_ID ?? ""

class ApiError extends Error {
  status: number
  body: unknown

  constructor(status: number, body: unknown) {
    super(`API error ${status}`)
    this.status = status
    this.body = body
  }
}

function getCsrfToken(): string {
  const match = document.cookie.match(/csrftoken=([^;]+)/)
  return match?.[1] ?? ""
}

function headers(extra?: HeadersInit): Headers {
  const h = new Headers(extra)
  if (TENANT_ID) h.set("X-Tenant-ID", TENANT_ID)
  const csrf = getCsrfToken()
  if (csrf) h.set("X-CSRFToken", csrf)
  return h
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => res.statusText)
    throw new ApiError(res.status, body)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export async function apiGet<T>(
  path: string,
  options?: { signal?: AbortSignal },
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    signal: options?.signal,
    headers: headers({ "Content-Type": "application/json" }),
    credentials: "include",
  })
  return handleResponse<T>(res)
}

export async function apiPost<T>(
  path: string,
  body?: unknown,
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    credentials: "include",
    body: body ? JSON.stringify(body) : undefined,
  })
  return handleResponse<T>(res)
}

export async function apiPut<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "PUT",
    headers: headers({ "Content-Type": "application/json" }),
    credentials: "include",
    body: body ? JSON.stringify(body) : undefined,
  })
  return handleResponse<T>(res)
}

export async function apiDelete<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "DELETE",
    headers: headers({ "Content-Type": "application/json" }),
    credentials: "include",
  })
  return handleResponse<T>(res)
}

export async function apiUpload<T>(
  path: string,
  formData: FormData,
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: headers(),
    credentials: "include",
    body: formData,
  })
  return handleResponse<T>(res)
}

export { ApiError }
