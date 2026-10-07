import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Django's APPEND_SLASH API routes must pass through unchanged; otherwise
  // Next and Django redirect the same request in opposite directions.
  skipTrailingSlashRedirect: true,
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${process.env.KAZILAYER_API_URL ?? "http://127.0.0.1:8000"}/api/:path*/` }];
  },
  images: {
    remotePatterns: [{ protocol: "http", hostname: "127.0.0.1", port: "8000", pathname: "/media/**" }, { protocol: "http", hostname: "localhost", port: "8000", pathname: "/media/**" }],
  },
};

export default nextConfig;
