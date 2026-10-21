const rawApiUrl = process.env.API_INTERNAL_URL ?? 'http://127.0.0.1:3001/v1';
let apiUrl;
try {
  apiUrl = new URL(rawApiUrl);
} catch {
  throw new Error('API_INTERNAL_URL inválida. Use http://127.0.0.1:<porta>/v1.');
}
if (
  apiUrl.protocol !== 'http:' ||
  apiUrl.hostname !== '127.0.0.1' ||
  apiUrl.pathname !== '/v1' ||
  apiUrl.username ||
  apiUrl.password ||
  apiUrl.search ||
  apiUrl.hash
) {
  throw new Error('API_INTERNAL_URL deve ser http://127.0.0.1:<porta>/v1, sem credenciais.');
}

/** @type {import('next').NextConfig} */
const config = {
  agentRules: false,
  distDir: process.env.RADAR_E2E_BUILD === 'true' ? '.next-e2e' : '.next',
  typescript: {
    tsconfigPath: process.env.RADAR_E2E_BUILD === 'true' ? 'tsconfig.e2e.json' : 'tsconfig.json',
  },
  async rewrites() {
    return [{ source: '/api/:path*', destination: `${apiUrl.href}/:path*` }];
  },
};
export default config;
