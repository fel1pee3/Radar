import { Ajv } from 'ajv';
import addFormats from 'ajv-formats';
import event from './schemas/event-v1.json' with { type: 'json' };
import heartbeat from './schemas/heartbeat-v1.json' with { type: 'json' };
import action from './schemas/incident-action-v1.json' with { type: 'json' };

export const schemas = {
  'event-v1': event,
  'heartbeat-v1': heartbeat,
  'incident-action-v1': action,
};
export type ContractName = keyof typeof schemas;
const ajv = new Ajv({ allErrors: true, strict: true, strictNumbers: true, coerceTypes: false });
addFormats.default(ajv);
// Mesma precisão UTC em ambos os runtimes; rejeita datas normalizadas e leap seconds.
ajv.addFormat('date-time', {
  type: 'string',
  validate(value: string) {
    const match = /^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d{1,3}))?Z$/.exec(value);
    if (!match || match[1]!.startsWith('0000')) return false;
    const time = Date.parse(value);
    return (
      Number.isFinite(time) &&
      new Date(time).toISOString() === `${match[1]}.${(match[2] ?? '').padEnd(3, '0')}Z`
    );
  },
});
const validators = Object.fromEntries(
  Object.entries(schemas).map(([name, schema]) => [name, ajv.compile(schema)]),
);

export function validateContract(name: ContractName, value: unknown): boolean {
  if (!validators[name]!(value)) return false;
  if (name === 'event-v1') {
    const points = (value as { pose: { index: number }[] }).pose;
    if (new Set(points.map((point) => point.index)).size !== points.length) return false;
  }
  return true;
}
