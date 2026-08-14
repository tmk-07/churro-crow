import type { ApiConfig, ApiErrorShape, CheckResponse, SolveResponse } from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export class ApiError extends Error {
  issues: string[];

  constructor(message: string, issues: string[] = []) {
    super(message);
    this.name = "ApiError";
    this.issues = issues;
  }
}

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

export const getConfig = () => request<ApiConfig>("/api/config");
export const checkExpression = (payload: unknown) => request<CheckResponse>("/api/check", {
  method: "POST",
  body: JSON.stringify(payload),
});
export const solveShake = (payload: unknown) => request<SolveResponse>("/api/solve", {
  method: "POST",
  body: JSON.stringify(payload),
});
