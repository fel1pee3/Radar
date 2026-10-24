import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync, existsSync } from 'node:fs';
// Fingerprint code, schemas, tests, manifests and lockfiles actually executed.
// Excludes private data, generated files, documentation and gitignored tool skills.
export function sourceIdentity() {
  const names = execFileSync(
    'git',
    ['ls-files', '--cached', '--others', '--exclude-standard', '-z'],
    { encoding: 'utf8' },
  )
    .split('\0')
    .filter(
      (p) =>
        p &&
        existsSync(p) &&
        !/^(docs|etapas)\//.test(p) &&
        p !== 'README.md' &&
        p !== 'apps/web/next-env.d.ts',
    )
    .sort();
  const hash = createHash('sha256');
  for (const name of names)
    hash
      .update(name)
      .update('\0')
      .update(readFileSync(name).toString('utf8').replace(/\r\n/g, '\n'))
      .update('\0');
  return {
    head: execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(),
    sourceSha256: hash.digest('hex'),
    dirty: execFileSync('git', ['status', '--porcelain'], { encoding: 'utf8' }).trim().length > 0,
    files: names.length,
  };
}
