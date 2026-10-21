import type { EventV1, IncidentActionV1 } from '@radar/contracts';
export type User = { id: string; tenantId: string; email: string; role: 'OWNER' | 'OPERATOR' };
export type Page<T> = { items: T[]; nextCursor: string | null };
export type Site = { id: string; name: string; timezone: string };
export type Camera = {
  id: string;
  siteId: string;
  name: string;
  type: 'FILE' | 'WEBCAM' | 'RTSP';
  expectedRunning: boolean;
  device: { id: string };
  health: {
    state: string;
    receivedAt: string | null;
    ageMs: number | null;
    stale: boolean;
    heartbeat: { mode: EventV1['mode']; qualityFlags: string[]; captureState: string } | null;
  };
};
export type Status = 'OPEN' | 'ACKNOWLEDGED' | 'IN_PROGRESS' | 'RESOLVED' | 'DISMISSED';
export type Review =
  'UNREVIEWED' | 'PERSON_ON_FLOOR_CONFIRMED' | 'FALL_REPORTED' | 'FALSE_POSITIVE' | 'INCONCLUSIVE';
export type Incident = Pick<
  EventV1,
  | 'mode'
  | 'kind'
  | 'occurredAt'
  | 'detectedAt'
  | 'cameraId'
  | 'runId'
  | 'episodeId'
  | 'sourceOffsetMs'
> & {
  id: string;
  siteId: string;
  receivedAt: string;
  createdAt: string;
  updatedAt: string;
  status: Status;
  review: Review;
  outcome: string | null;
  dismissReason: string | null;
  version: number;
  deliveryClass: string;
  signals: EventV1['signals'] | null;
  pose: EventV1['pose'] | null;
  versions: EventV1['versions'] | null;
};
export type Audit = {
  id: string;
  actorId: string | null;
  action: string;
  createdAt: string;
  fromVersion: number | null;
  toVersion: number | null;
  incidentAction: {
    actionId: string;
    actorId: string;
    action: string;
    payload: IncidentActionV1 | null;
    result: { status: Status; review: Review; outcome: string | null };
  } | null;
};
export type Notice = {
  id: string;
  channel: string;
  urgent: boolean;
  message: string;
  createdAt: string;
  intent: {
    incidentId: string;
    incident: Pick<Incident, 'mode' | 'deliveryClass' | 'kind' | 'cameraId' | 'occurredAt'>;
  };
};
export type Credential = {
  id: string;
  deviceId: string;
  cameraId: string;
  version: number;
  createdAt: string;
  token: string;
};
