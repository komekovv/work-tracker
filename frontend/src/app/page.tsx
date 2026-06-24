import { Card } from "@/components/ui/card";

export default function Home() {
  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Your work-time and KPI overview.
        </p>
      </div>

      <Card className="p-6">
        <p className="text-sm text-muted-foreground">
          KPI cards, heatmap, and trend chart arrive next.
        </p>
        {/* Token swatches confirm the theme system is wired (temporary). */}
        <div className="mt-4 flex items-center gap-3 text-xs text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-full bg-target" /> target
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-full bg-bonus" /> bonus
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-full bg-leave" /> leave
          </span>
        </div>
      </Card>
    </section>
  );
}
