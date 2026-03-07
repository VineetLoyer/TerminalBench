export const API_URL = process.env.API_URL || "http://127.0.0.1:8741";

export async function api<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`${response.status} ${path}`);
  }
  return response.json() as Promise<T>;
}

export type Aggregate = {
  n: number;
  n_success: number;
  success_rate: number;
  n_regression: number;
  regression_rate: number;
  latency_p50: number;
  latency_p95: number;
  mean_prompt_tokens: number;
  mean_completion_tokens: number;
  total_cost_usd: number;
  mean_cost_usd: number;
};

export type Episode = {
  task_id: string;
  success: boolean;
  regression: boolean;
  steps: number;
  latency_sec: number;
  prompt_tokens: number;
  completion_tokens: number;
  cost_usd: number;
  repo: string;
  title: string;
  split: string;
  difficulty: string;
};

export type Run = {
  id: string;
  label: string;
  kind: string;
  date: string;
  notes: string;
  overall: Aggregate;
  train: Aggregate;
  held_out: Aggregate;
  by_repo: Record<string, Aggregate>;
  held_out_by_repo: Record<string, Aggregate>;
  episodes: Episode[];
};

export type Task = {
  id: string;
  repo: string;
  title: string;
  category: string;
  difficulty: string;
  split: string;
  instruction: string;
  timeout_sec: number;
  image: string;
  fixture: string | null;
  grader: { command: string; timeout_sec: number; regression_command: string | null };
  tags: string[];
};

export function pct(rate: number): string {
  return `${Math.round(rate * 100)}%`;
}

export function repoName(repo: string): string {
  return repo.split("/")[1] ?? repo;
}

export function money(value: number): string {
  return `$${value.toFixed(2)}`;
}

