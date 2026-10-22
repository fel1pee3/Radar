import { ConsoleLogger } from '@nestjs/common';
import { appendFileSync, mkdirSync, readdirSync, statSync, unlinkSync, lstatSync } from 'node:fs';
import { resolve, join, dirname } from 'node:path';
import { randomUUID } from 'node:crypto';

// Only controlled technical facts reach console/disk; library strings are never copied.
export class TechnicalLogger extends ConsoleLogger {
  private file = '';
  constructor(
    readonly directory = resolve(
      process.cwd().endsWith(join('apps', 'api')) ? '../..' : '.',
      '.local/api-logs',
    ),
    private readonly clock = () => new Date(),
  ) {
    super('RadarAPI', { json: true });
  }
  cleanup() {
    mkdirSync(this.directory, { recursive: true, mode: 0o700 });
    let current = resolve(this.directory);
    while (true) {
      if (lstatSync(current).isSymbolicLink()) throw new Error('PRIVATE_LOG_DIRECTORY_REQUIRED');
      const parent = dirname(current);
      if (parent === current) break;
      current = parent;
    }
    const files = readdirSync(this.directory)
      .filter((n) => /^technical-[0-9a-f-]+\.log$/.test(n))
      .map((n) => ({ path: join(this.directory, n), stat: lstatSync(join(this.directory, n)) }))
      .filter((f) => f.stat.isFile() && !f.stat.isSymbolicLink())
      .sort((a, b) => a.stat.mtimeMs - b.stat.mtimeMs);
    let bytes = files.reduce((n, f) => n + f.stat.size, 0);
    for (const f of files)
      if (this.clock().getTime() - f.stat.mtimeMs >= 7 * 86400000 || bytes > 9 * 1024 * 1024) {
        unlinkSync(f.path);
        bytes -= f.stat.size;
        if (f.path === this.file) this.file = '';
      }
  }
  private record(level: 'log' | 'warn' | 'error', message: unknown) {
    const value =
      typeof message === 'object' && message !== null ? (message as Record<string, unknown>) : {};
    const event = ['request_failed', 'retention_failed'].includes(String(value.event))
      ? value.event
      : 'runtime_message';
    const record = {
      at: this.clock().toISOString(),
      level,
      event,
      code: [
        'INTERNAL_ERROR',
        'DATABASE_UNAVAILABLE',
        'CLEANUP_PENDING',
        'EVIDENCE_STORAGE_UNAVAILABLE',
      ].includes(String(value.code))
        ? value.code
        : undefined,
      status: typeof value.status === 'number' ? value.status : undefined,
    };
    super[level](record);
    try {
      this.cleanup();
      if (!this.file || statSync(this.file).size >= 1024 * 1024)
        this.file = join(this.directory, `technical-${randomUUID()}.log`);
      appendFileSync(this.file, JSON.stringify(record) + '\n', { mode: 0o600 });
    } catch {
      super.error({ event: 'technical_log_unavailable' });
    }
  }
  override log(message: unknown) {
    this.record('log', message);
  }
  override warn(message: unknown) {
    this.record('warn', message);
  }
  override error(message: unknown) {
    this.record('error', message);
  }
  override debug() {}
  override verbose() {}
}
