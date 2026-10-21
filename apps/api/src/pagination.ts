import { BadRequestException } from '@nestjs/common';
import { isUUID } from 'class-validator';
import type { ListDto } from './dto.js';

export function pageArguments(query: ListDto) {
  if (!query.cursor) return { take: query.limit + 1 };
  try {
    const value: unknown = JSON.parse(Buffer.from(query.cursor, 'base64url').toString('utf8'));
    if (
      typeof value !== 'object' ||
      value === null ||
      !('id' in value) ||
      !('createdAt' in value) ||
      typeof value.id !== 'string' ||
      !isUUID(value.id) ||
      typeof value.createdAt !== 'string'
    )
      throw new Error();
    const date = new Date(value.createdAt);
    if (!Number.isFinite(date.getTime()) || date.toISOString() !== value.createdAt)
      throw new Error();
    return {
      take: query.limit + 1,
      where: { OR: [{ createdAt: { gt: date } }, { createdAt: date, id: { gt: value.id } }] },
    };
  } catch {
    throw new BadRequestException('Cursor inválido.');
  }
}

export function pageResult<T extends { id: string; createdAt: Date }>(rows: T[], limit: number) {
  const items = rows.slice(0, limit);
  const last = items.at(-1);
  const nextCursor =
    rows.length > limit && last
      ? Buffer.from(
          JSON.stringify({ id: last.id, createdAt: last.createdAt.toISOString() }),
        ).toString('base64url')
      : null;
  return { items, nextCursor };
}
