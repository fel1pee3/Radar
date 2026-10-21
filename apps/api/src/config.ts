export class ConfigurationError extends Error {}

export function validateDatabaseUrl(value: string | undefined): string {
  try {
    const url = new URL(value ?? '');
    if (
      url.protocol !== 'postgresql:' ||
      url.hostname !== '127.0.0.1' ||
      !url.port ||
      url.port === '5432' ||
      !url.username ||
      !url.password ||
      !/^\/[a-zA-Z0-9_]+$/.test(url.pathname) ||
      url.search ||
      url.hash
    )
      throw new Error();
    return url.href;
  } catch {
    throw new ConfigurationError(
      'DATABASE_URL deve apontar ao PostgreSQL do projeto em loopback (15432 nesta máquina), com banco e credenciais. A porta 5432 do host é reservada à instalação existente.',
    );
  }
}

export interface Settings {
  databaseUrl: string;
  host: '127.0.0.1';
  port: number;
  webOrigin: string;
  secureCookie: boolean;
}

export function readSettings(env: NodeJS.ProcessEnv = process.env): Settings {
  const host = env.API_HOST ?? '127.0.0.1';
  const port = env.API_PORT ?? '3001';
  if (host !== '127.0.0.1') throw new ConfigurationError('API_HOST deve ser 127.0.0.1.');
  if (!/^\d+$/.test(port) || Number(port) < 1 || Number(port) > 65535) {
    throw new ConfigurationError('API_PORT deve ser um inteiro entre 1 e 65535.');
  }
  let origin: URL;
  try {
    origin = new URL(env.WEB_ORIGIN ?? 'http://127.0.0.1:3000');
  } catch {
    throw new ConfigurationError('WEB_ORIGIN inválida.');
  }
  if (
    origin.hostname !== '127.0.0.1' ||
    origin.pathname !== '/' ||
    origin.search ||
    origin.hash ||
    origin.username ||
    origin.password ||
    !['http:', 'https:'].includes(origin.protocol)
  ) {
    throw new ConfigurationError(
      'WEB_ORIGIN deve ser uma origem de loopback sem caminho ou credenciais.',
    );
  }
  const insecure = env.NODE_ENV === 'development' && env.ALLOW_INSECURE_LOCAL_HTTP === 'true';
  if (origin.protocol === 'http:' && !insecure) {
    throw new ConfigurationError(
      'HTTP exige NODE_ENV=development e ALLOW_INSECURE_LOCAL_HTTP=true em loopback.',
    );
  }
  return {
    host,
    port: Number(port),
    webOrigin: origin.origin,
    secureCookie: origin.protocol !== 'http:',
    databaseUrl: validateDatabaseUrl(env.DATABASE_URL),
  };
}

export const SETTINGS = Symbol('SETTINGS');
