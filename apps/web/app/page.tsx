import Link from "next/link";
import { ApiDown, Shell } from "@/components/shell";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { money, pct, repoName, tryApi, type Run } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function OverviewPage() {
  const data = await tryApi<{ baseline: Run; tuned: Run }>("/compare");
  if (!data) return <ApiDown />;
  return (
    <Shell>
      <Overview baseline={data.baseline} tuned={data.tuned} />
    </Shell>
  );
}

function Overview({ baseline, tuned }: { baseline: Run; tuned: Run }) {
  const repos = Object.keys(tuned.held_out_by_repo);
  return (
    <div className="space-y-8">
      <div className="max-w-2xl">
        <p className="font-mono text-xs text-muted-foreground">held-out · 35 tasks</p>
        <h1 className="mt-2 text-4xl font-medium tracking-tight sm:text-5xl">
          {pct(baseline.held_out.success_rate)}
          <span className="text-muted-foreground"> → </span>
          {pct(tuned.held_out.success_rate)}
        </h1>
        <p className="mt-3 text-sm leading-6 text-muted-foreground">
          QLoRA and GRPO on Qwen2.5-3B-Instruct, scored in a Docker sandbox by a
          planner, an executor, and a reviewer. The tuned run solves{" "}
          {tuned.overall.n_success} of {tuned.overall.n} tasks ({pct(tuned.overall.success_rate)}).
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Held-out success" value={`${tuned.held_out.n_success}/${tuned.held_out.n}`} detail="was 12/35" />
        <Stat label="Regressions" value={`${tuned.overall.n_regression}`} detail={`${pct(tuned.overall.regression_rate)} of episodes`} />
        <Stat label="Latency p50" value={`${tuned.overall.latency_p50.toFixed(0)}s`} detail={`p95 ${tuned.overall.latency_p95.toFixed(0)}s`} />
        <Stat label="Run cost" value={money(tuned.overall.total_cost_usd)} detail={`${Math.round(tuned.overall.mean_prompt_tokens).toLocaleString()} prompt tok avg`} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Held-out success by repository</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {repos.map((repo) => {
            const before = baseline.held_out_by_repo[repo]?.success_rate ?? 0;
            const after = tuned.held_out_by_repo[repo]?.success_rate ?? 0;
            return (
              <div key={repo} className="grid gap-2 sm:grid-cols-[8rem_1fr_auto] sm:items-center">
                <div className="text-sm">{repoName(repo)}</div>
                <div className="space-y-1">
                  <Bar width={before} className="bg-muted-foreground/40" />
                  <Bar width={after} className="bg-primary" />
                </div>
                <div className="font-mono text-xs text-muted-foreground">
                  {pct(before)} → {pct(after)}
                </div>
              </div>
            );
          })}
          <p className="text-xs text-muted-foreground">Pale bar is the base 3B. Green bar is the adapter.</p>
        </CardContent>
      </Card>

      <div className="grid gap-3 md:grid-cols-2">
        <RunCard run={baseline} />
        <RunCard run={tuned} />
      </div>
    </div>
  );
}

function Stat({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-normal text-muted-foreground">{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="font-mono text-2xl">{value}</div>
        <p className="mt-1 text-xs text-muted-foreground">{detail}</p>
      </CardContent>
    </Card>
  );
}

function Bar({ width, className }: { width: number; className: string }) {
  return (
    <div className="h-2 rounded-full bg-muted">
      <div className={`h-2 rounded-full ${className}`} style={{ width: `${Math.max(width * 100, 2)}%` }} />
    </div>
  );
}

function RunCard({ run }: { run: Run }) {
  return (
    <Link href={`/runs/${run.id}`} className="block">
      <Card className="h-full transition-colors hover:bg-muted/40">
        <CardHeader>
          <div className="flex items-center justify-between gap-2">
            <CardTitle className="text-base">{run.label}</CardTitle>
            <Badge variant="outline">{run.date}</Badge>
          </div>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          <p>{run.notes}</p>
          <p className="mt-3 font-mono text-xs text-foreground">
            {pct(run.overall.success_rate)} overall · {pct(run.held_out.success_rate)} held-out
          </p>
        </CardContent>
      </Card>
    </Link>
  );
}
