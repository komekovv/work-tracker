import { Card } from "@/components/ui/card";

export default function SettingsPage() {
  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Theme and general preferences.
        </p>
      </div>

      <Card className="p-6">
        <p className="text-sm text-muted-foreground">
          Theme and dynamic settings arrive in a later step.
        </p>
      </Card>
    </section>
  );
}
