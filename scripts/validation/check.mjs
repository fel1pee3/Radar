import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import { sourceIdentity } from './source.mjs';
const engineeringOnly = process.argv.includes('--engineering');
const prerequisites = [
  ['Node', process.version === 'v24.22.1'],
  [
    'pnpm',
    spawnSync(process.execPath, [process.env.npm_execpath, '--version'], {
      encoding: 'utf8',
    }).stdout?.trim() === '10.34.7',
  ],
  ['uv', spawnSync('uv', ['--version'], { encoding: 'utf8' }).stdout?.startsWith('uv 0.13.4')],
  [
    'Docker',
    spawnSync('docker', ['info', '--format', '{{.ServerVersion}}'], { encoding: 'utf8' }).status ===
      0,
  ],
  ['Configuração local', ['.env', 'apps/api/.env', 'apps/web/.env'].every(existsSync)],
];
let automated = null;
try {
  automated = JSON.parse(readFileSync('.local/etapa08/engineering.json', 'utf8'));
} catch {
  /* never infer execution from absence */
}
const expected = [
  'frozen-js',
  'frozen-python',
  'lint',
  'typecheck',
  'build',
  'edge-lint',
  'edge-env',
  'contracts',
  'simulator',
  'python',
  'api',
  'browser',
  'backup',
  'clean-install',
];
const valid =
  automated?.source?.sourceSha256 === sourceIdentity().sourceSha256 &&
  expected.every((name) => automated.checks.some((c) => c.name === name && c.exitCode === 0)) &&
  automated.checks.every((c) => c.exitCode === 0);
const result = {
  prerequisites: prerequisites.map(([name, passed]) => ({
    name,
    status: passed ? 'APROVADO' : 'FALHOU',
  })),
  automatedEngineering: valid
    ? 'APROVADO com evidência desta revisão'
    : 'NÃO VERIFICADO nesta revisão; execute pnpm.cmd demo:verify e confira os logs',
  manualGates: [
    'Novas cenas EVALUATION autorizadas e anotadas, separadas da calibração',
    'Evento LIVE por visão, incidente e revisão humana',
    'Webcam contínua por pelo menos 30 minutos reais e revisão de perdas/avisos',
    'Execução sem internet com comunicação local preservada',
    'Apresentação de 5–7 minutos executada pelo fundador',
  ].map((name) => ({ name, status: 'PENDENTE; conferir VALIDACAO_MANUAL_ETAPA_08.md' })),
  releaseReady: false,
  exitCodes:
    '0=engenharia aprovada (--engineering), 1=falha/engenharia sem evidência, 2=engenharia aprovada e gates manuais pendentes',
};
console.log(JSON.stringify(result, null, 2));
process.exitCode =
  prerequisites.some(([, passed]) => !passed) || !valid ? 1 : engineeringOnly ? 0 : 2;
