"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { ThemeToggle } from "@/components/ui/theme-toggle";
import { modules } from "@/lib/modules";
import { cn } from "@/lib/utils";

export function Header() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-10 border-b border-border bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="mx-auto flex h-14 w-full max-w-6xl items-center justify-between px-4">
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2">
            <span
              aria-hidden="true"
              className="grid h-6 w-6 place-items-center rounded-md bg-primary text-[11px] font-bold text-primary-foreground"
            >
              W
            </span>
            <span className="text-sm font-semibold tracking-tight">
              Work Tracker
            </span>
          </Link>

          <nav className="flex items-center gap-1">
            {modules.map((m) => {
              const active = pathname === m.href;
              return (
                <Link
                  key={m.id}
                  href={m.href}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "rounded-md px-3 py-1.5 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                    active
                      ? "bg-muted font-medium text-foreground"
                      : "text-muted-foreground hover:text-foreground",
                  )}
                >
                  {m.label}
                </Link>
              );
            })}
          </nav>
        </div>

        <ThemeToggle />
      </div>
    </header>
  );
}
