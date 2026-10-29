import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import { sourceIdentity } from './source.mjs';
import {
  engineeringStatus,
  functionalGates,
  verdict,
  currentSubject,
} from './release-evidence.mjs';

function argument(name, fallback) {
  const i = process.argv.indexOf(name);
  return i < 0 ? fallback : process.argv[i + 1];
}
function optionalJson(path) {
  if (!existsSync(path)) return null;
  return JSON.parse(readFileSync(path, 'utf8').replace(/^\uFEFF/, ''));
}
try {
  const engineeringOnly = process.argv.includes('--engineering');
  const prerequisites = [
    ['Node', process.version === 'v24.22.1'],
    [
      'pnpm',
      Boolean(process.env.npm_execpath) &&
        spawnSync(process.execPath, [process.env.npm_execpath, '--version'], {
          encoding: 'utf8',
        }).stdout?.trim() === '10.34.7',
    ],
    ['uv', spawnSync('uv', ['--version'], { encoding: 'utf8' }).stdout?.startsWith('uv 0.13.4')],
    [
      'Docker',
      spawnSync('docker', ['info', '--format', '{{.ServerVersion}}'], { encoding: 'utf8' })
        .status === 0,
    ],
    ['Configuração local', ['.env', 'apps/api/.env', 'apps/web/.env'].every(existsSync)],
  ].map(([name, passed]) => ({ name, status: passed ? 'APROVADO' : 'REPROVADO' }));
  const source = sourceIdentity();
  const index = optionalJson(argument('--evidence', '.local/release-evidence.json'));
  const subject = currentSubject(index, source);
  const engineering = engineeringStatus(
    optionalJson(argument('--engineering-evidence', '.local/etapa08/engineering.json')),
    source,
  );
  const gates = functionalGates(index, subject);
  const result = {
    source,
    subject,
    prerequisites,
    engineering,
    gates,
    nominalPhysicalSeconds: 600,
    historicalFailure:
      'Teste original de 30 minutos não comprovado; falha aos 27min45s preservada.',
    ...verdict(prerequisites, engineering, gates, engineeringOnly),
    exitCodes:
      '0=escopo solicitado aprovado; 1=reprovação/falha; 2=pendência ou evidência desatualizada',
  };
  console.log(JSON.stringify(result, null, 2));
  process.exitCode = result.exitCode;
} catch (error) {
  console.error(
    JSON.stringify({ status: 'REPROVADO', reason: error.message, releaseReady: false }),
  );
  process.exitCode = 1;
}
