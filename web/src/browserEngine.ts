import { ApiError } from "./apiError";

type EngineMethod = "config" | "check" | "solve";

type EngineResponse<T> =
  | { id: number; ok: true; data: T }
  | { id: number; ok: false; message: string; issues: string[] };

let worker: Worker | null = null;
let nextId = 1;
const pending = new Map<number, {
  resolve(value: unknown): void;
  reject(reason: unknown): void;
}>();

function getWorker(): Worker {
  if (worker) return worker;
  worker = new Worker(new URL("./engine.worker.ts", import.meta.url), { type: "module" });
  worker.onmessage = (event: MessageEvent<EngineResponse<unknown>>) => {
    const request = pending.get(event.data.id);
    if (!request) return;
    pending.delete(event.data.id);
    if (event.data.ok) request.resolve(event.data.data);
    else request.reject(new ApiError(event.data.message, event.data.issues));
  };
  worker.onerror = (event) => {
    const error = new ApiError(`The browser calculation engine stopped: ${event.message}`);
    pending.forEach(({ reject }) => reject(error));
    pending.clear();
    worker?.terminate();
    worker = null;
  };
  return worker;
}

export function browserRequest<T>(method: EngineMethod, payload: unknown = {}): Promise<T> {
  const id = nextId++;
  return new Promise<T>((resolve, reject) => {
    pending.set(id, { resolve: resolve as (value: unknown) => void, reject });
    getWorker().postMessage({ id, method, payload });
  });
}
