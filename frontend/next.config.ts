import type { NextConfig } from 'next';

// Backend is reached through the Next.js origin. Avoid browser CORS and
// public hard-coded localhost:8000 URLs.
const apiOrigin = process.env.RND_API_INTERNAL_URL ?? 'http://127.0.0.1:8000';
const config: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [{ source: '/backend/:path*', destination: `${apiOrigin}/:path*` }];
  },
};
export default config;
