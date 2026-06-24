import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

import { Header } from "@/components/header";
import {
  NO_FLASH_SCRIPT,
  ThemeProvider,
} from "@/components/ui/theme-provider";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Work Tracker",
  description: "Personal work-time and KPI dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // suppressHydrationWarning: the ThemeProvider (Step 3) sets the `dark` class
  // on <html> before paint, which would otherwise mismatch the server markup.
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-background text-foreground font-sans">
        {/* Set the theme class before paint to avoid a flash of wrong theme. */}
        <script dangerouslySetInnerHTML={{ __html: NO_FLASH_SCRIPT }} />
        <ThemeProvider>
          <Header />
          <div className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
            {children}
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
