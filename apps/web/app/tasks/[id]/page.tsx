import Link from "next/link";
import { isNextNotFound } from "@/lib/api";
import { notFound } from "next/navigation";
import { ApiDown, Shell } from "@/components/shell";
import { Badge } from "@/components/ui/badge";
import { api, type Episode, type Run, type Task } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function TaskPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  try {
    const response = await fetch(`${process.env.API_URL || "http://127.0.0.1:8741"}/tasks/${id}`, {
      cache: "no-store",
    });
    if (response.status === 404) notFound();
    if (!response.ok) return <ApiDown />;
    const task = (await response.json()) as Task;
    const tuned = await api<Run>("/runs/2026-03-03-qlora-grpo");
    const baseline = await api<Run>("/runs/2026-02-24-baseline");
    const tunedEp = tuned.episodes.find((row) => row.task_id === id);
    const baseEp = baseline.episodes.find((row) => row.task_id === id);
    return (
      <Shell>
        <Link href="/tasks" className="text-sm text-muted-foreground hover:text-foreground">
          Task bank
        </Link>
        <h1 className="mt-2 text-2xl font-medium tracking-tight">{task.title}</h1>
        <div className="mt-3 flex flex-wrap gap-2">
          <Badge variant="outline">{task.repo}</Badge>
          <Badge variant="outline">{task.split === "held_out" ? "held-out" : "train"}</Badge>
          <Badge variant="outline">{task.difficulty}</Badge>
          <Badge variant="outline">{task.category}</Badge>
          {task.fixture && <Badge>local fixture</Badge>}
        </div>
        <pre className="mt-6 whitespace-pre-wrap rounded-lg border border-border bg-card p-4 font-sans text-sm leading-6">
          {task.instruction.trim()}
        </pre>
        <dl className="mt-6 grid gap-4 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-muted-foreground">Image</dt>
            <dd className="font-mono text-xs">{task.image}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Grader</dt>
            <dd className="font-mono text-xs">{task.grader.command}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Regression check</dt>
            <dd className="font-mono text-xs">{task.grader.regression_command || "none"}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Episode timeout</dt>
            <dd>{task.timeout_sec}s</dd>
          </div>
        </dl>
        <h2 className="mt-8 text-base font-medium">Recorded outcomes</h2>
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          <Outcome label="Baseline" episode={baseEp} />
          <Outcome label="QLoRA/GRPO" episode={tunedEp} />
        </div>
      </Shell>
    );
  } catch (error) {
    if (isNextNotFound(error)) throw error;
    return <ApiDown />;
  }
}

function Outcome({ label, episode }: { label: string; episode: Episode | undefined }) {
  if (!episode) {
    return <p className="text-sm text-muted-foreground">{label}: no row in the ledger.</p>;
  }
  return (
    <div className="rounded-lg border border-border p-3 text-sm">
      <div className="text-muted-foreground">{label}</div>
      <div className="mt-1 font-medium">{episode.success ? "Pass" : "Fail"}</div>
      <p className="mt-1 font-mono text-xs text-muted-foreground">
        {episode.steps} steps · {episode.latency_sec.toFixed(0)}s · {episode.prompt_tokens.toLocaleString()} prompt tokens
        {episode.regression ? " · regression" : ""}
      </p>
    </div>
  );
}
