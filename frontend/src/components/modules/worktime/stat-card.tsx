import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  sub,
  accentClass,
}: {
  label: string;
  value: React.ReactNode;
  sub?: React.ReactNode;
  accentClass?: string;
}) {
  return (
    <Card className="p-5">
      <div className="flex items-center gap-2">
        {accentClass && (
          <span className={cn("h-2 w-2 rounded-full", accentClass)} aria-hidden />
        )}
        <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          {label}
        </span>
      </div>
      <div className="mt-2 text-3xl font-semibold tracking-tight tabular-nums">
        {value}
      </div>
      {sub && <div className="mt-1 text-sm text-muted-foreground">{sub}</div>}
    </Card>
  );
}
