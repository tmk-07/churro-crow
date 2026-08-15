import type { ApiConfig, ApiErrorShape, CheckResponse, SolveResponse } from "./types";
import { browserRequest } from "./browserEngine";
import { ApiError } from "./apiError";
export { ApiError };

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
const USE_HTTP_API = Boolean(API_BASE);

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new ApiError("The calculation API is not reachable yet.");
  }
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = (body.detail ?? body) as Partial<ApiErrorShape>;
    throw new ApiError(detail.message ?? "The request could not be completed.", detail.issues ?? []);
  }
  return body as T;
}

export const getConfig = () => USE_HTTP_API
  ? request<ApiConfig>("/api/config")
  : browserRequest<ApiConfig>("config");

export const checkExpression = (payload: unknown) => USE_HTTP_API
  ? request<CheckResponse>("/api/check", { method: "POST", body: JSON.stringify(payload) })
  : browserRequest<CheckResponse>("check", payload);

export const solveShake = (payload: unknown) => USE_HTTP_API
  ? request<SolveResponse>("/api/solve", { method: "POST", body: JSON.stringify(payload) })
  : browserRequest<SolveResponse>("solve", payload);
