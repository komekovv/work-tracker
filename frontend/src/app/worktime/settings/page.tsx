import Link from "next/link";

import { Card } from "@/components/ui/card";

export default function WorktimeSettingsPage() {
  return (
    <section className="space-y-6">
      <div>
        <Link
          href="/worktime"
          className="text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          ← Worktime
        </Link>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight">
          Targets &amp; holidays
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Set daily/weekday targets and mark holidays, leave, and vacation.
        </p>
      </div>

      <Card className="p-6">
        <p className="text-sm text-muted-foreground">
          Target and holiday management arrives in a later step.
        </p>
      </Card>
    </section>
  );
}
