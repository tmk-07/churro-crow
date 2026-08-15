import { ENGINE_SOURCES } from "./engineSources";

const PYODIDE_VERSION = "0.27.7";
const PYODIDE_BASE = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;

interface PyodideRuntime {
  FS: {
    mkdirTree(path: string): void;
    writeFile(path: string, contents: string, options: { encoding: "utf8" }): void;
  };
  globals: {
    set(name: string, value: unknown): void;
    delete(name: string): void;
  };
  runPython(code: string): unknown;
}

type LoadPyodide = (options: { indexURL: string }) => Promise<PyodideRuntime>;

type EngineRequest = {
  id: number;
  method: "config" | "check" | "solve";
  payload: unknown;
};

let runtimePromise: Promise<PyodideRuntime> | null = null;

async function createRuntime(): Promise<PyodideRuntime> {
  const module = await import(/* @vite-ignore */ `${PYODIDE_BASE}pyodide.mjs`) as {
    loadPyodide: LoadPyodide;
  };
  const pyodide = await module.loadPyodide({ indexURL: PYODIDE_BASE });
  pyodide.FS.mkdirTree("/onsets_engine");
  for (const [name, source] of Object.entries(ENGINE_SOURCES)) {
    pyodide.FS.writeFile(`/onsets_engine/${name}`, source, { encoding: "utf8" });
  }
  pyodide.runPython("import sys; sys.path.insert(0, '/'); import onsets_engine.browser_api as browser_api");
  return pyodide;
}

function runtime(): Promise<PyodideRuntime> {
  runtimePromise ??= createRuntime();
  return runtimePromise;
}

self.onmessage = async (event: MessageEvent<EngineRequest>) => {
  const { id, method, payload } = event.data;
  try {
    const pyodide = await runtime();
    pyodide.globals.set("__browser_method", method);
    pyodide.globals.set("__browser_payload", JSON.stringify(payload ?? {}));
    const raw = pyodide.runPython(
      "browser_api.dispatch_json(__browser_method, __browser_payload)"
    );
    pyodide.globals.delete("__browser_method");
    pyodide.globals.delete("__browser_payload");
    self.postMessage({ id, ...JSON.parse(String(raw)) });
  } catch {
    runtimePromise = null;
    self.postMessage({
      id,
      ok: false,
      message: "The browser calculation engine could not start. Check your connection and reload the page.",
      issues: [],
    });
  }
};
