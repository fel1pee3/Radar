/* Gerado do JSON Schema versionado. Execute pnpm contracts:generate. */

export type EventV1 = {
  schemaVersion: 1;
  eventType: 'INCIDENT_CANDIDATE';
  eventId: string;
  episodeId: string;
  cameraId: string;
  runId: string;
  mode: 'SIMULATED' | 'REPLAY' | 'LIVE';
  kind: 'PERSON_ON_FLOOR' | 'POSSIBLE_FALL';
  occurredAt: string;
  detectedAt: string;
  sourceOffsetMs: number | null;
  signals: {
    floorDurationMs: number;
    torsoAngleDeg: number;
    bboxAspectRatio: number;
    hipInFloorZone: boolean;
    rapidDescentObserved: boolean;
    validPoseFraction: number;
    analysisFps: number;
  };
  /**
   * @maxItems 22
   */
  pose: (
    | {
        index: number;
        x: number;
        y: number;
        visibility: number;
      }
    | {
        index: 11 | 12 | 13 | 14 | 15 | 16 | 23 | 24 | 25 | 26 | 27 | 28;
        x: number;
        y: number;
        confidence: number;
      }
  )[];
  versions: {
    worker: string;
    model: string;
    policy: string;
    calibration: string;
  };
  evidenceMode?: 'none' | 'skeleton' | 'snapshot';
};
