import Link from "next/link";
import { ApiDown, Shell } from "@/components/shell";
import { money, pct, tryApi, type Aggregate, type Run } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function RunsPage() {
  const data = await tryApi<{
    runs: Array<Pick<Run, "id" | "label" | "kind" | "date" | "notes" | "overall" | "held_out">>;
  }>("/runs");
  if (!data) return <ApiDown />;
  return (
    <Shell>
      <h1 className="text-2xl font-medium tracking-tight">Runs</h1>
      <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
        Each run is a CSV ledger of 60 episodes. The harness recomputes success, regressions,
        latency, tokens, and cost when the API loads it.
      </p>
      <div className="mt-6 space-y-3">
        {data.runs.length === 0 && (
          <p className="text-sm text-muted-foreground">No ledgers in results/.</p>
        )}
        {data.runs.map((run) => (
          <Link
            key={run.id}
            href={`/runs/${run.id}`}
            className="block rounded-lg border border-border p-4 hover:bg-muted/40"
          >
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <h2 className="font-medium">{run.label}</h2>
              <span className="font-mono text-xs text-muted-foreground">{run.date}</span>
            </div>
            <p className="mt-1 text-sm text-muted-foreground">{run.notes}</p>
            <Numbers overall={run.overall} heldOut={run.held_out} />
          </Link>
        ))}
      </div>
    </Shell>
  );
}

function Numbers({ overall, heldOut }: { overall: Aggregate; heldOut: Aggregate }) {
  return (
    <p className="mt-3 font-mono text-xs">
      {pct(overall.success_rate)} overall · {pct(heldOut.success_rate)} held-out · p50{" "}
      {overall.latency_p50.toFixed(0)}s · {money(overall.total_cost_usd)}
    </p>
  );
}
