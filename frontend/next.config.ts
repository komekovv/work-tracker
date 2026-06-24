import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Static export: no Node server in production — FastAPI serves the built
  // `out/` directory (Phase 7). All logic lives in the backend API.
  output: "export",
  // next/image needs the optimizer server, which a static export doesn't have;
  // serve images as-is.
  images: { unoptimized: true },
  // React Compiler (enabled by the scaffold) — kept on.
  reactCompiler: true,
};

export default nextConfig;
