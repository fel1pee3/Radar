import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { validateContract } from '../dist/index.js';

const cases = JSON.parse(readFileSync(new URL('../fixtures/cases.json', import.meta.url), 'utf8'));
for (const fixture of cases) {
  test(fixture.name, () =>
    assert.equal(validateContract(fixture.schema, fixture.value), fixture.valid),
  );
}
test('números não finitos não são aceitos', () => {
  const value = structuredClone(cases.find((fixture) => fixture.schema === 'event-v1').value);
  value.pose = [{ index: 11, x: Infinity, y: 0, visibility: 1 }];
  assert.equal(validateContract('event-v1', value), false);
});
