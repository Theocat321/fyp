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
};

export default nextConfig;
