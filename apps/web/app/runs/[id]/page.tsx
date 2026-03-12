import Link from "next/link";
import { ApiDown, Missing, Shell } from "@/components/shell";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { money, pct, repoName, type Run } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function RunPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const response = await fetch(`${process.env.API_URL || "http://127.0.0.1:8741"}/runs/${id}`, {
    cache: "no-store",
  }).catch(() => null);
  if (!response) return <ApiDown />;
  if (response.status === 404) {
    return (
      <Missing
        title="That run is not in the ledger"
        detail={`No recorded run is named “${id}”.`}
        href="/runs"
        linkLabel="Back to the runs"
      />
    );
  }
  if (!response.ok) return <ApiDown />;
  const run = (await response.json().catch(() => null)) as Run | null;
  if (!run) return <ApiDown />;
  return (
    <Shell>
      <Link href="/runs" className="text-sm text-muted-foreground hover:text-foreground">
        Runs
      </Link>
      <h1 className="mt-2 text-2xl font-medium tracking-tight">{run.label}</h1>
      <p className="mt-2 max-w-2xl text-sm text-muted-foreground">{run.notes}</p>
      <div className="mt-4 flex flex-wrap gap-2 font-mono text-xs">
        <Badge variant="outline">{pct(run.overall.success_rate)} overall</Badge>
        <Badge variant="outline">{pct(run.held_out.success_rate)} held-out</Badge>
        <Badge variant="outline">{run.overall.n_regression} regressions</Badge>
        <Badge variant="outline">{money(run.overall.total_cost_usd)}</Badge>
      </div>
      <div className="mt-6 overflow-x-auto rounded-lg border border-border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Task</TableHead>
              <TableHead>Split</TableHead>
              <TableHead>Result</TableHead>
              <TableHead>Steps</TableHead>
              <TableHead>Latency</TableHead>
              <TableHead>Tokens</TableHead>
              <TableHead>Cost</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {run.episodes.map((episode) => (
              <TableRow key={episode.task_id}>
                <TableCell>
                  <Link href={`/tasks/${episode.task_id}`} className="hover:underline">
                    {episode.title}
                  </Link>
                  <div className="text-xs text-muted-foreground">{repoName(episode.repo)}</div>
                </TableCell>
                <TableCell>{episode.split === "held_out" ? "held-out" : "train"}</TableCell>
                <TableCell>
                  {episode.success ? "Pass" : "Fail"}
                  {episode.regression ? " · regression" : ""}
                </TableCell>
                <TableCell>{episode.steps}</TableCell>
                <TableCell>{episode.latency_sec.toFixed(0)}s</TableCell>
                <TableCell className="font-mono text-xs">
                  {episode.prompt_tokens.toLocaleString()}+{episode.completion_tokens.toLocaleString()}
                </TableCell>
                <TableCell>{money(episode.cost_usd)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </Shell>
  );
}
