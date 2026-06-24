import { cn } from "@/lib/utils";

type Tone = "default" | "target" | "bonus" | "leave";

const TONES: Record<Tone, string> = {
  default: "bg-muted text-muted-foreground",
  target: "bg-target/15 text-target",
  bonus: "bg-bonus/15 text-bonus",
  leave: "bg-leave/20 text-foreground/70",
};

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: Tone;
}

export function Badge({ tone = "default", className, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        TONES[tone],
        className,
      )}
      {...props}
    />
  );
}
