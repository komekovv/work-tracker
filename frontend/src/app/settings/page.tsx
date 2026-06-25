import { GeneralSettings } from "@/components/settings/general-settings";
import { ThemeControl } from "@/components/settings/theme-control";

export default function SettingsPage() {
  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Theme and general preferences.
        </p>
      </div>

      <ThemeControl />
      <GeneralSettings />
    </section>
  );
}
