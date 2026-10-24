import { execFileSync } from 'node:child_process';
import { mkdirSync, copyFileSync, writeFileSync, readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { randomUUID, createHash } from 'node:crypto';
import { sourceIdentity } from './source.mjs';
const identity = sourceIdentity(),
  directory = resolve('.local/releases', `v0.1-candidate-${randomUUID()}`),
  files = [];
for (const name of execFileSync(
  'git',
  ['ls-files', '--cached', '--others', '--exclude-standard', '-z'],
  { encoding: 'utf8' },
)
  .split('\0')
  .filter(Boolean)) {
  if (name.startsWith('.local/') || /\.(dump|mp4|task|sqlite|jpg|png)$/.test(name))
    throw new Error('Arquivo privado entre candidatos.');
  const target = resolve(directory, 'source', name);
  mkdirSync(dirname(target), { recursive: true });
  copyFileSync(name, target);
  files.push({ name, sha256: createHash('sha256').update(readFileSync(target)).digest('hex') });
}
writeFileSync(
  resolve(directory, 'release.json'),
  JSON.stringify(
    {
      version: '0.1-candidate',
      status: 'PARCIAL',
      identity,
      createdAt: new Date().toISOString(),
      releaseReady: false,
      files,
      excluded: [
        'private environment',
        'credentials',
        'media',
        'models',
        'logs',
        'databases',
        'dependencies',
        'tool binaries',
      ],
      published: false,
    },
    null,
    2,
  ),
);
console.log(
  JSON.stringify(
    { status: 'ok', releaseReady: false, directory, source: identity, files: files.length },
    null,
    2,
  ),
);
