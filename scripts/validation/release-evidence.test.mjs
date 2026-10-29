import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import {
  judge,
  functionalGates,
  verdict,
  engineeringStatus,
  REQUIRED_CHECKS,
  currentSubject,
} from './release-evidence.mjs';
test('absence never certifies manual work; D50 is dispensed, not performed', () => {
  const gates = functionalGates(null, {});
  assert.equal(gates.filter((g) => g.status === 'PENDENTE').length, 6);
  assert.equal(gates.at(-1).status, 'DISPENSADO');
  assert.equal(verdict([], { status: 'APROVADO' }, gates).exitCode, 2);
});
test('full release verdict depends on evidence; engineering cannot certify perception', () => {
  assert.equal(verdict([], { status: 'APROVADO' }, [{ status: 'APROVADO' }]).releaseReady, true);
  const fail = verdict([], { status: 'APROVADO' }, [{ status: 'REPROVADO' }]);
  assert.equal(fail.releaseReady, false);
  assert.equal(fail.exitCode, 1);
  assert.equal(verdict([], { status: 'APROVADO' }, [{ status: 'PENDENTE' }], true).exitCode, 0);
});
test('inconclusive controls and historical missing case block regression', () => {
  const cases = Array.from({ length: 36 }, (_, i) => ({
    id: String(i),
    completed: true,
    score: { approved: true, missed: 0 },
  }));
  assert.equal(judge('regression', { scope: 'DEVELOPMENT', cases }), false);
  ['floor03', 'floor05', 'floor07', 'controlled-lying'].forEach((id, i) => (cases[i].id = id));
  assert.equal(judge('regression', { scope: 'DEVELOPMENT', cases }), true);
  cases[3].score.approved = false;
  assert.equal(judge('regression', { scope: 'DEVELOPMENT', cases }), false);
});
test('physical requires 600 seconds, human onset and persisted human review', () => {
  const metrics = { decisionCoverage: 0.85, maxObservationGapMs: 500, maxDecisionAgeMs: 2000 };
  const v = {
    mode: 'LIVE',
    plannedSeconds: 600,
    executedSeconds: 600.5,
    stopReason: 'MAX_RUN_SECONDS',
    captureState: 'ENDED',
    pending: 0,
    missingProfiles: 0,
    positiveEpisodes: 1,
    rearmed: true,
    duplicates: 0,
    falseAlerts: 0,
    controlsHumanConfirmed: true,
    maxHumanAnnotatedLatencyMs: 4000,
    plannedHorizon: metrics,
    executedHorizon: metrics,
    review: { actorKind: 'HUMAN', persisted: true, incidentId: 'i', actionId: 'a' },
  };
  assert.equal(judge('physical', v), true);
  for (const change of [
    { plannedSeconds: 60 },
    { executedSeconds: 599 },
    { maxHumanAnnotatedLatencyMs: null },
    { maxHumanAnnotatedLatencyMs: -1 },
    { plannedHorizon: { ...metrics, decisionCoverage: 1.1 } },
    { review: { ...v.review, actorKind: 'AUTOMATED' } },
    { plannedHorizon: { ...metrics, decisionCoverage: 0.799 } },
  ])
    assert.equal(judge('physical', { ...v, ...change }), false);
});
test('changed subject and altered proof cannot approve; hashes bind config', () => {
  const directory = mkdtempSync(join(tmpdir(), 'radar-receipt-'));
  try {
    const file = join(directory, 'proof.json');
    writeFileSync(file, '{}');
    const sha256 = createHash('sha256').update('{}').digest('hex');
    const subject = { sourceSha256: 'old' };
    const receipt = {
      schemaVersion: 1,
      kind: 'offline',
      subject,
      artifacts: [{ path: file, sha256 }],
      measurements: {
        internetDisconnectedHumanConfirmed: true,
        localReplayDelivered: true,
        panelCheckedBeforeReconnect: true,
      },
    };
    const index = { evidence: { offline: { path: 'receipt' } } };
    assert.equal(
      functionalGates(index, { sourceSha256: 'new' }, () => receipt)[4].status,
      'DESATUALIZADO',
    );
    assert.equal(functionalGates(index, subject, () => receipt)[4].status, 'APROVADO');
    writeFileSync(file, 'changed');
    assert.equal(functionalGates(index, subject, () => receipt)[4].status, 'REPROVADO');
    assert.equal(currentSubject({}, subject).configurationSha256, 'UNAVAILABLE');
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});
test('engineering requires each check exactly once and matching evidence revision', () => {
  const checks = REQUIRED_CHECKS.map((name) => ({ name, exitCode: 0 }));
  assert.equal(
    engineeringStatus({ source: { sourceSha256: 'a' }, checks }, { sourceSha256: 'a' }).status,
    'APROVADO',
  );
  assert.equal(
    engineeringStatus({ source: { sourceSha256: 'a' }, checks }, { sourceSha256: 'b' }).status,
    'DESATUALIZADO',
  );
  assert.equal(
    engineeringStatus({ checks: checks.slice(1) }, { sourceSha256: 'a' }).status,
    'DESATUALIZADO',
  );
});

test('transition verdict requires an explicit human annotation source', () => {
  const v = {
    annotatedTransitions: 4,
    supportedFallEvents: 4,
    unjustifiedFallEvents: 0,
    confoundsReviewed: true,
  };
  assert.equal(judge('transitions', v), false);
  assert.equal(judge('transitions', { ...v, annotationSource: 'DETECTOR_PREDICTIONS' }), false);
  assert.equal(judge('transitions', { ...v, annotationSource: 'HUMAN_ANNOTATED' }), true);
});
