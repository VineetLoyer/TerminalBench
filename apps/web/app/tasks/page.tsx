import Link from "next/link";
import { ApiDown, Shell } from "@/components/shell";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { repoName, tryApi, type Task } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function TasksPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; split?: string; repo?: string }>;
}) {
  const params = await searchParams;
  const data = await tryApi<{ tasks: Task[] }>("/tasks");
  if (!data) return <ApiDown />;
  const q = (params.q || "").toLowerCase();
  const tasks = data.tasks.filter((task) => {
    if (params.split && task.split !== params.split) return false;
    if (params.repo && task.repo !== params.repo) return false;
    if (!q) return true;
    return (
      task.id.includes(q) ||
      task.title.toLowerCase().includes(q) ||
      task.repo.toLowerCase().includes(q)
    );
  });
  const repos = [...new Set(data.tasks.map((task) => task.repo))];
  return (
    <Shell>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-medium tracking-tight">Task bank</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {tasks.length} shown of {data.tasks.length}. Five tasks have local fixtures; the rest are full-repo specs for the Docker sandbox.
          </p>
        </div>
      </div>
      <form className="mb-4 flex flex-wrap gap-2">
        <Input name="q" defaultValue={params.q || ""} placeholder="Filter by name" className="max-w-xs" />
        <select name="split" defaultValue={params.split || ""} className="h-8 rounded-lg border border-input bg-background px-2 text-sm">
          <option value="">Both splits</option>
          <option value="train">Train</option>
          <option value="held_out">Held-out</option>
        </select>
        <select name="repo" defaultValue={params.repo || ""} className="h-8 rounded-lg border border-input bg-background px-2 text-sm">
          <option value="">All repos</option>
          {repos.map((repo) => (
            <option key={repo} value={repo}>
              {repoName(repo)}
            </option>
          ))}
        </select>
        <button type="submit" className="h-8 rounded-lg bg-primary px-3 text-sm text-primary-foreground">
          Apply
        </button>
      </form>
      <div className="overflow-x-auto rounded-lg border border-border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Task</TableHead>
              <TableHead>Repo</TableHead>
              <TableHead>Split</TableHead>
              <TableHead>Difficulty</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {tasks.map((task) => (
              <TableRow key={task.id}>
                <TableCell>
                  <Link href={`/tasks/${task.id}`} className="font-medium hover:underline">
                    {task.title}
                  </Link>
                  <div className="font-mono text-xs text-muted-foreground">{task.id}</div>
                </TableCell>
                <TableCell>{repoName(task.repo)}</TableCell>
                <TableCell>
                  <Badge variant="outline">{task.split === "held_out" ? "held-out" : "train"}</Badge>
                </TableCell>
                <TableCell className="capitalize">{task.difficulty}</TableCell>
              </TableRow>
            ))}
            {tasks.length === 0 && (
              <TableRow>
                <TableCell colSpan={4} className="text-muted-foreground">
                  No tasks match that filter.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </Shell>
  );
}
