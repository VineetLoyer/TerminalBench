import Link from "next/link";
import { Shell } from "@/components/shell";

export default function NotFound() {
  return (
    <Shell>
      <h1 className="text-xl font-medium">That page is not in the bank</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        <Link href="/tasks" className="underline">
          Back to the task list
        </Link>
      </p>
    </Shell>
  );
}
