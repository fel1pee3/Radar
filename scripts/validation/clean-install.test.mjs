import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync, symlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { cleanInstallRuntime, cleanInstallResultPath } from './clean-install.mjs';

function fixture() {
  const root = mkdtempSync(join(tmpdir(), 'radar-clean-planning-'));
  mkdirSync(join(root, '.local', 'runtime'), { recursive: true });
  const python = join(root, '.local', 'runtime', 'python.exe');
  writeFileSync(python, 'Planning fixture only; never execute this file.');
  return { root, python, close: () => rmSync(root, { recursive: true, force: true }) };
}

test('default clean installation preserves the existing 3.12 selection', () => {
  const result = cleanInstallRuntime({ RADAR_SIGNED_PYTHON: 'ignored-without-explicit-opt-in' });
  assert.equal(result.requested, 'PYTHON312');
  assert.equal(result.project, 'services/edge');
  assert.equal(result.python, null);
  assert.deepEqual(result.syncArguments, ['sync', '--project', 'services/edge', '--frozen']);
  assert.deepEqual(result.runArguments, ['run', '--project', 'services/edge', '--frozen']);
});

test('signed selection fixes all Python commands to the explicit executable and disables downloads', () => {
  const f = fixture();
  try {
    const result = cleanInstallRuntime(
      { RADAR_VALIDATION_RUNTIME: 'PYTHON313_SIGNED', RADAR_SIGNED_PYTHON: f.python },
      f.root,
    );
    assert.equal(result.project, 'experiments/python313-cpu');
    assert.equal(result.python, f.python);
    for (const args of [result.syncArguments, result.runArguments]) {
      assert.equal(args[args.indexOf('--python') + 1], f.python);
      assert.ok(args.includes('--frozen') && args.includes('--no-python-downloads'));
      assert.ok(!args.includes('services/edge'));
    }
    // This is a command plan, not a substitute for the PSF signature verifier.
    assert.equal(Object.hasOwn(result, 'verified'), false);
  } finally {
    f.close();
  }
});

test('unknown runtime and absent, relative, wrong-name or outside Python fail before execution', () => {
  const f = fixture();
  try {
    assert.throws(() => cleanInstallRuntime({ RADAR_VALIDATION_RUNTIME: 'UNKNOWN' }, f.root));
    for (const python of [
      undefined,
      '.local/runtime/python.exe',
      join(f.root, '.local/runtime/missing/python.exe'),
      join(f.root, '.local/runtime/python313.dll'),
      join(f.root, 'outside/python.exe'),
    ]) {
      assert.throws(() =>
        cleanInstallRuntime(
          { RADAR_VALIDATION_RUNTIME: 'PYTHON313_SIGNED', RADAR_SIGNED_PYTHON: python },
          f.root,
        ),
      );
    }
  } finally {
    f.close();
  }
});

test('explicit fresh receipt preserves historical and existing receipt bytes', () => {
  const f = fixture();
  try {
    const historical = join(f.root, '.local/etapa08/clean-install.json');
    mkdirSync(join(f.root, '.local/etapa08'));
    writeFileSync(historical, 'historical proof');
    assert.equal(cleanInstallResultPath({}, f.root), historical);
    const target = join(f.root, '.local/new-clean-install.json');
    assert.equal(cleanInstallResultPath({ RADAR_CLEAN_INSTALL_RESULT: target }, f.root), target);
    assert.throws(
      () => cleanInstallResultPath({ RADAR_CLEAN_INSTALL_RESULT: historical }, f.root),
      /preservado/,
    );
    assert.throws(() =>
      cleanInstallResultPath({ RADAR_CLEAN_INSTALL_RESULT: join(f.root, 'outside.json') }, f.root),
    );
    assert.throws(() =>
      cleanInstallResultPath(
        { RADAR_CLEAN_INSTALL_RESULT: join(f.root, '.local/nonexistent/result.json') },
        f.root,
      ),
    );
    assert.equal(readFileSync(historical, 'utf8'), 'historical proof');
  } finally {
    f.close();
  }
});

test('receipt and runtime cannot escape .local through a directory junction', (t) => {
  const f = fixture();
  try {
    const outside = join(f.root, 'outside-local');
    mkdirSync(outside);
    writeFileSync(join(outside, 'python.exe'), 'never executed');
    const link = join(f.root, '.local/link');
    try {
      symlinkSync(outside, link, 'junction');
    } catch (error) {
      if (['EPERM', 'EACCES'].includes(error.code)) {
        t.skip('OS does not permit test junction creation');
        return;
      }
      throw error;
    }
    assert.throws(
      () =>
        cleanInstallResultPath({ RADAR_CLEAN_INSTALL_RESULT: join(link, 'result.json') }, f.root),
      /Redirecionamento/,
    );
    assert.throws(
      () =>
        cleanInstallRuntime(
          {
            RADAR_VALIDATION_RUNTIME: 'PYTHON313_SIGNED',
            RADAR_SIGNED_PYTHON: join(link, 'python.exe'),
          },
          f.root,
        ),
      /Redirecionamento/,
    );
  } finally {
    f.close();
  }
});
