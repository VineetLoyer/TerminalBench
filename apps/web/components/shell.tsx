import Link from "next/link";

const links = [
  { href: "/", label: "Overview" },
  { href: "/tasks", label: "Tasks" },
  { href: "/runs", label: "Runs" },
  { href: "/training", label: "Training" },
];

export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-full bg-background text-foreground">
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <Link href="/" className="flex items-baseline gap-2">
            <span className="font-medium tracking-tight">TerminalBench</span>
            <span className="font-mono text-xs text-muted-foreground">march 2026</span>
          </Link>
          <nav className="flex gap-1 text-sm">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="rounded-md px-2.5 py-1 text-muted-foreground hover:bg-muted hover:text-foreground"
              >
                {link.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
    </div>
  );
}

export function ApiDown() {
  return (
    <Shell>
      <h1 className="text-xl font-medium">API is not running</h1>
      <p className="mt-2 max-w-xl text-sm text-muted-foreground">
        The dashboard reads the task bank and the March 2026 runs from the FastAPI
        service. Start it from the repo root, then reload this page.
      </p>
      <pre className="mt-4 overflow-x-auto rounded-lg border border-border bg-card p-3 font-mono text-xs">
        terminalbench serve --port 8741
      </pre>
    </Shell>
  );
}
