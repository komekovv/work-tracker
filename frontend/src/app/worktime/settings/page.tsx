import Link from "next/link";

import { HolidaySettings } from "@/components/modules/worktime/holiday-settings";
import { TargetSettings } from "@/components/modules/worktime/target-settings";

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

      <TargetSettings />
      <HolidaySettings />
    </section>
  );
}
