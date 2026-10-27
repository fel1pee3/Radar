import { createHash } from 'node:crypto';
import { HttpException, Injectable, UnprocessableEntityException } from '@nestjs/common';
import type { PipeTransform } from '@nestjs/common';
import { validateContract } from '@radar/contracts';
import type { EventV1 } from '@radar/contracts';
import type { Prisma } from './generated/prisma/client.js';

export type Transaction = Prisma.TransactionClient;
export const CLOCK = Symbol('CLOCK');
export interface Clock {
  now(): Date;
}
@Injectable()
export class SystemClock implements Clock {
  now(): Date {
    return new Date();
  }
}
export const NOTIFICATIONS_ENABLED = Symbol('NOTIFICATIONS_ENABLED');

export class ContractPipe implements PipeTransform {
  constructor(private readonly name: 'event-v1' | 'heartbeat-v1' | 'incident-action-v1') {}
  transform(value: unknown): unknown {
    if (!validateContract(this.name, value)) {
      throw new UnprocessableEntityException({
        code: 'INVALID_PAYLOAD',
        message: 'Payload incompatível com o contrato v1.',
      });
    }
    return value;
  }
}

export function fail(status: number, code: string): never {
  throw new HttpException({ code, message: code }, status);
}
export function canonical(value: unknown): string {
  if (value === null || typeof value !== 'object') return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  return `{${Object.entries(value)
    .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
    .map(([key, item]) => `${JSON.stringify(key)}:${canonical(item)}`)
    .join(',')}}`;
}
export const contentHash = (value: unknown): string =>
  createHash('sha256').update(canonical(value)).digest('hex');

export function episodeHash(event: EventV1): string {
  const { eventId: ignored, ...context } = event;
  void ignored;
  return contentHash(context);
}
export type DeliveryStateHint = 'DELAYED' | 'CLOCK_UNCERTAIN';

export function deliveryStateHint(value: unknown): DeliveryStateHint | undefined {
  if (value === undefined) return undefined;
  if (value !== 'DELAYED' && value !== 'CLOCK_UNCERTAIN') fail(400, 'INVALID_DELIVERY_STATE');
  return value;
}

export function deliveryClass(
  event: Pick<EventV1, 'mode' | 'detectedAt' | 'occurredAt'>,
  receivedAt: Date,
  hint?: DeliveryStateHint,
) {
  if (event.mode !== 'LIVE') return 'TEST' as const;
  const detected = Date.parse(event.detectedAt);
  if (
    hint === 'CLOCK_UNCERTAIN' ||
    detected > receivedAt.getTime() + 30000 ||
    Date.parse(event.occurredAt) > detected
  )
    return 'CLOCK_UNCERTAIN' as const;
  if (hint === 'DELAYED' || receivedAt.getTime() - detected > 120000) return 'DELAYED' as const;
  return 'CURRENT' as const;
}

export async function lockCamera(
  tx: Transaction,
  tenantId: string,
  cameraId: string,
): Promise<void> {
  const found = await tx.$queryRaw<
    { id: string }[]
  >`SELECT "id" FROM "Camera" WHERE "tenantId"=${tenantId}::uuid AND "id"=${cameraId}::uuid FOR UPDATE`;
  if (!found.length) fail(403, 'CAMERA_SCOPE_MISMATCH');
}
