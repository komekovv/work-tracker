"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

type Preference = "light" | "dark" | "system";
type Resolved = "light" | "dark";

interface ThemeContextValue {
  preference: Preference; // what the user chose
  resolved: Resolved; // what is actually applied
  setPreference: (preference: Preference) => void;
  toggle: () => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

const STORAGE_KEY = "theme";

function systemTheme(): Resolved {
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}
function resolve(pref: Preference): Resolved {
  return pref === "system" ? systemTheme() : pref;
}
function applyClass(theme: Resolved): void {
  document.documentElement.classList.toggle("dark", theme === "dark");
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [preference, setPref] = useState<Preference>("system");
  const [resolved, setResolved] = useState<Resolved>("light");

  // Read the stored preference on mount (the no-flash script already set the
  // class; this syncs React state to it).
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as Preference | null;
    const pref: Preference =
      stored === "light" || stored === "dark" || stored === "system"
        ? stored
        : "system";
    setPref(pref);
    const r = resolve(pref);
    setResolved(r);
    applyClass(r);
  }, []);

  // While in "system" mode, follow OS theme changes live.
  useEffect(() => {
    if (preference !== "system") return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => {
      const r = systemTheme();
      setResolved(r);
      applyClass(r);
    };
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, [preference]);

  const setPreference = useCallback((next: Preference) => {
    setPref(next);
    localStorage.setItem(STORAGE_KEY, next);
    const r = resolve(next);
    setResolved(r);
    applyClass(r);
  }, []);

  const toggle = useCallback(() => {
    setPreference(resolved === "dark" ? "light" : "dark");
  }, [resolved, setPreference]);

  return (
    <ThemeContext.Provider value={{ preference, resolved, setPreference, toggle }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within a ThemeProvider");
  return ctx;
}

// Pre-paint theme setter for the layout. Honours an explicit light/dark choice,
// otherwise (missing or "system") follows the OS preference.
export const NO_FLASH_SCRIPT = `(function(){try{var t=localStorage.getItem('${STORAGE_KEY}');var d;if(t==='dark'){d=true;}else if(t==='light'){d=false;}else{d=window.matchMedia('(prefers-color-scheme: dark)').matches;}document.documentElement.classList.toggle('dark',d);}catch(e){}})();`;
