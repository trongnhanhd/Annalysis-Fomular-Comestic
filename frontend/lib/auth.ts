import { createHmac, timingSafeEqual } from 'node:crypto';

const name = 'rd_session';
export const cookieName = name;
function configuredSecret(): string { return process.env.WEB_ACCESS_TOKEN || ''; }
export function validPassword(value: string): boolean {
  const secret = configuredSecret();
  if (!secret || !value) return false;
  const actual = Buffer.from(value); const expected = Buffer.from(secret);
  return actual.length === expected.length && timingSafeEqual(actual, expected);
}
function signature(): string {
  const secret = configuredSecret();
  return secret ? createHmac('sha256', secret).update('cosmetic-rd-session-v1').digest('hex') : '';
}
export function validSession(value: string | undefined): boolean {
  const sig = signature();
  if (!sig || !value || !/^[0-9a-f]{64}$/.test(value)) return false;
  return timingSafeEqual(Buffer.from(value), Buffer.from(sig));
}
export function makeSession(): string { return signature(); }
