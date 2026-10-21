export interface HealthLiveResponse {
  status: 'ok';
}

export type { EventV1 } from './generated/event-v1.js';
export type { HeartbeatV1 } from './generated/heartbeat-v1.js';
export type { IncidentActionV1 } from './generated/incident-action-v1.js';
export { schemas, validateContract } from './validation.js';
