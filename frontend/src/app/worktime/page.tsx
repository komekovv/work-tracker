import Link from "next/link";

import { Card } from "@/components/ui/card";

export default function WorktimePage() {
  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Worktime</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Monthly calendar and session history.
          </p>
        </div>
        <Link
          href="/worktime/settings"
          className="rounded-md px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          Targets &amp; holidays
        </Link>
      </div>

      <Card className="p-6">
        <p className="text-sm text-muted-foreground">
          Calendar and session list arrive next.
        </p>
      </Card>
    </section>
  );
}
