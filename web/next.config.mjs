import pkg from "@next/env";
const { loadEnvConfig } = pkg;
import path from "node:path";

// Load root .env so both apps can share a single file in dev
try {
  const rootDir = path.resolve(process.cwd(), "..");
  loadEnvConfig(rootDir, process.env.NODE_ENV !== "production");
} catch {}

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    // In local development, proxy Next.js API calls to the Python FastAPI server
    const isDev = process.env.NODE_ENV !== "production";
    if (!isDev) return [];
    const target = process.env.PY_BACKEND_URL || "http://localhost:8000";
    return [
      { source: "/api/chat", destination: `${target}/api/chat` },
      { source: "/api/chat-stream", destination: `${target}/api/chat-stream` },
    ];
  },
};

export default nextConfig;
