import type { RuntimeResult, ScenarioSummary } from "./types";

const API_BASE = import.meta.env.VITE_AXIOM_API_BASE ?? "/api";

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function fetchRuntimeScenarios(): Promise<ScenarioSummary[]> {
  const response = await fetch(`${API_BASE}/v1/runtime/scenarios`);
  return readJson<ScenarioSummary[]>(response);
}

export async function evaluateRuntimeScenario(scenarioId: string): Promise<RuntimeResult> {
  const response = await fetch(`${API_BASE}/v1/runtime/evaluate/${scenarioId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" }
  });
  return readJson<RuntimeResult>(response);
}

export async function evaluateRawContext(rawText: string): Promise<RuntimeResult> {
  const response = await fetch(`${API_BASE}/v1/intake/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      input_mode: "paste_context",
      raw_text: rawText,
      metadata: { source: "public_demo_ui" }
    })
  });
  return readJson<RuntimeResult>(response);
}
