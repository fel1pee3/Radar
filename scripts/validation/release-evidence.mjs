import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

export const REQUIRED_CHECKS = [
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
const hash = (bytes) => createHash('sha256').update(bytes).digest('hex');
export const subjectHash = (subject) =>
  hash(
    JSON.stringify(
      Object.fromEntries(Object.entries(subject).sort(([a], [b]) => a.localeCompare(b))),
    ),
  );
export function verifiedJson(ref) {
  if (!ref || typeof ref.path !== 'string' || !/^[a-f0-9]{64}$/.test(ref.sha256 ?? ''))
    throw new Error('Referência sem caminho/hash');
  const bytes = readFileSync(resolve(ref.path));
  if (hash(bytes) !== ref.sha256) throw new Error('Evidência alterada: ' + ref.path);
  return JSON.parse(bytes.toString('utf8').replace(/^\uFEFF/, ''));
}
export function currentSubject(index, source) {
  const subject = { sourceSha256: source.sourceSha256 };
  for (const name of ['configuration', 'model', 'classifier', 'policy', 'protocol']) {
    const file = index?.subjectFiles?.[name];
    subject[name + 'Sha256'] = file && existsFile(file) ? hash(readFileSync(file)) : 'UNAVAILABLE';
  }
  return subject;
}
function existsFile(path) {
  try {
    return readFileSync(path).length > 0;
  } catch {
    return false;
  }
}
export function engineeringStatus(evidence, source) {
  if (!evidence) return { status: 'PENDENTE', reason: 'Sem comprovante de engenharia.' };
  const checks = REQUIRED_CHECKS.map((name) => {
    const rows = evidence.checks?.filter((c) => c.name === name) ?? [];
    if (rows.length !== 1) return { name, status: 'PENDENTE' };
    const c = rows[0];
    if (c.exitCode !== 0) return { name, status: 'REPROVADO' };
    // Legacy receipt is valid only against its full source identity.
    if (!c.inputs?.length)
      return {
        name,
        status:
          evidence.source?.sourceSha256 === source.sourceSha256 ? 'APROVADO' : 'DESATUALIZADO',
      };
    try {
      if (!c.log || hash(readFileSync(c.log.path)) !== c.log.sha256)
        return { name, status: 'REPROVADO' };
      const current = c.inputs.every((r) => hash(readFileSync(r.path)) === r.sha256);
      return { name, status: current ? 'APROVADO' : 'DESATUALIZADO', reused: c.reusedFrom ?? null };
    } catch {
      return { name, status: 'DESATUALIZADO' };
    }
  });
  return { status: aggregate(checks), checks };
}
export function aggregate(rows) {
  if (rows.some((r) => r.status === 'REPROVADO')) return 'REPROVADO';
  if (rows.some((r) => r.status === 'DESATUALIZADO')) return 'DESATUALIZADO';
  if (rows.some((r) => r.status === 'PENDENTE')) return 'PENDENTE';
  return 'APROVADO';
}
function assertMetrics(m) {
  return (
    m &&
    Number.isFinite(m.decisionCoverage) &&
    m.decisionCoverage >= 0.8 &&
    m.decisionCoverage <= 1 &&
    Number.isFinite(m.maxObservationGapMs) &&
    m.maxObservationGapMs >= 0 &&
    m.maxObservationGapMs <= 500 &&
    Number.isFinite(m.maxDecisionAgeMs) &&
    m.maxDecisionAgeMs >= 0 &&
    m.maxDecisionAgeMs <= 2000
  );
}
export function judge(kind, value) {
  if (kind === 'regression') {
    return (
      value.scope === 'DEVELOPMENT' &&
      value.cases?.length === 36 &&
      new Set(value.cases.map((c) => c.id)).size === 36 &&
      value.cases.every((c) => c.completed && c.score?.approved === true) &&
      ['floor03', 'floor05', 'floor07', 'controlled-lying'].every((id) =>
        value.cases.some((c) => c.id === id && c.score.missed === 0),
      )
    );
  }
  if (kind === 'transitions') {
    return (
      value.annotatedTransitions >= 4 &&
      value.supportedFallEvents === value.annotatedTransitions &&
      value.unjustifiedFallEvents === 0 &&
      ['HUMAN_ANNOTATED', 'HUMAN_CONFIRMED_SOURCE_INTERVALS'].includes(value.annotationSource) &&
      value.confoundsReviewed === true
    );
  }
  if (kind === 'independent') {
    return (
      value.role === 'FINAL_RESERVED' &&
      value.frozenBeforeInference === true &&
      value.overlapByHash === 0 &&
      value.overlapByRecording === 0 &&
      value.overlapByParticipant === 0 &&
      value.targets >= 4 &&
      value.controls >= 8 &&
      value.missed === 0 &&
      value.falseAlerts === 0 &&
      value.duplicates === 0 &&
      value.inconclusive === 0 &&
      Number.isFinite(value.maxHumanAnnotatedLatencyMs) &&
      value.maxHumanAnnotatedLatencyMs >= 0 &&
      value.maxHumanAnnotatedLatencyMs <= 5000 &&
      assertMetrics(value)
    );
  }
  if (kind === 'physical') {
    return (
      value.mode === 'LIVE' &&
      value.plannedSeconds === 600 &&
      Number.isFinite(value.executedSeconds) &&
      value.executedSeconds >= 600 &&
      value.stopReason === 'MAX_RUN_SECONDS' &&
      value.captureState === 'ENDED' &&
      value.pending === 0 &&
      value.missingProfiles === 0 &&
      value.positiveEpisodes >= 1 &&
      value.rearmed === true &&
      value.duplicates === 0 &&
      value.falseAlerts === 0 &&
      value.controlsHumanConfirmed === true &&
      value.review?.actorKind === 'HUMAN' &&
      value.review?.persisted === true &&
      value.review?.incidentId &&
      value.review?.actionId &&
      Number.isFinite(value.maxHumanAnnotatedLatencyMs) &&
      value.maxHumanAnnotatedLatencyMs >= 0 &&
      value.maxHumanAnnotatedLatencyMs <= 5000 &&
      assertMetrics(value.plannedHorizon) &&
      assertMetrics(value.executedHorizon)
    );
  }
  if (kind === 'offline') {
    return (
      value.internetDisconnectedHumanConfirmed === true &&
      value.localReplayDelivered === true &&
      value.panelCheckedBeforeReconnect === true
    );
  }
  if (kind === 'recovery') {
    return (
      value.apiUnavailableExercised === true &&
      value.restartExercised === true &&
      value.delivered === 1 &&
      value.incidents === 1 &&
      value.notices === 1 &&
      value.duplicateAck === true &&
      value.pending === 0
    );
  }
  return false;
}
export function functionalGates(index, currentSubject, read = verifiedJson) {
  const gates = ['regression', 'transitions', 'independent', 'physical', 'offline', 'recovery'].map(
    (kind) => {
      const ref = index?.evidence?.[kind];
      if (!ref) return { name: kind, status: 'PENDENTE', reason: 'Sem evidência vinculada.' };
      try {
        const receipt = read(ref);
        if (receipt.schemaVersion !== 1 || receipt.kind !== kind || !receipt.subject)
          throw new Error('Comprovante incompatível');
        if (
          Object.values(currentSubject).includes('UNAVAILABLE') ||
          subjectHash(receipt.subject) !== subjectHash(currentSubject)
        )
          return {
            name: kind,
            status: 'DESATUALIZADO',
            reason: 'Versão/configuração diferente.',
          };
        if (!receipt.artifacts?.length) throw new Error('Sem provas originais');
        for (const artifact of receipt.artifacts) {
          const bytes = readFileSync(artifact.path);
          if (hash(bytes) !== artifact.sha256) throw new Error('Prova alterada');
        }
        return {
          name: kind,
          status: judge(kind, receipt.measurements) ? 'APROVADO' : 'REPROVADO',
          evidence: ref.path,
        };
      } catch (error) {
        return { name: kind, status: 'REPROVADO', reason: error.message };
      }
    },
  );
  gates.push({
    name: 'presentation',
    status: 'DISPENSADO',
    reason: 'D50: apresentação formal dispensada pelo fundador.',
  });
  return gates;
}
export function verdict(prerequisites, engineering, gates, engineeringOnly = false) {
  const engineeringReady =
    prerequisites.every((x) => x.status === 'APROVADO') && engineering.status === 'APROVADO';
  const functionalReady = gates.every((x) => ['APROVADO', 'DISPENSADO'].includes(x.status));
  const releaseReady = engineeringReady && functionalReady;
  const failure =
    prerequisites.some((x) => x.status === 'REPROVADO') ||
    engineering.status === 'REPROVADO' ||
    (!engineeringOnly && gates.some((x) => x.status === 'REPROVADO'));
  return {
    engineeringReady,
    functionalReady,
    releaseReady,
    exitCode: (engineeringOnly ? engineeringReady : releaseReady) ? 0 : failure ? 1 : 2,
  };
}
