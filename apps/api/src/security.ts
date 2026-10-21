import { createHash, randomBytes } from 'node:crypto';
import { argon2id, hash, verify } from 'argon2';
import type { Request } from 'express';

export const SESSION_COOKIE = 'radar_session';
export const SESSION_TTL_MS = 8 * 60 * 60 * 1000;
export const tokenHash = (token: string): string =>
  createHash('sha256').update(token).digest('hex');
export const newToken = (kind: 'ses' | 'dev'): string =>
  `${kind}_${randomBytes(32).toString('base64url')}`;
export const validToken = (value: unknown, kind: 'ses' | 'dev'): value is string =>
  typeof value === 'string' && new RegExp(`^${kind}_[A-Za-z0-9_-]{43}$`).test(value);

export function sessionToken(request: Request): string | null {
  const values = (request.headers.cookie ?? '')
    .split(';')
    .map((part) => part.trim())
    .filter((part) => part.startsWith(`${SESSION_COOKIE}=`));
  if (values.length !== 1) return null;
  const value = values[0]!.slice(SESSION_COOKIE.length + 1);
  return validToken(value, 'ses') ? value : null;
}

export function hashPassword(password: string): Promise<string> {
  return hash(password, { type: argon2id, memoryCost: 65536, timeCost: 3, parallelism: 1 });
}

export async function checkPassword(encoded: string, password: string): Promise<boolean> {
  try {
    return await verify(encoded, password);
  } catch {
    return false;
  }
}

export function validatePassword(password: unknown): asserts password is string {
  if (typeof password !== 'string' || password.length < 12 || password.length > 128) {
    throw new Error('A senha deve ter entre 12 e 128 caracteres.');
  }
}
