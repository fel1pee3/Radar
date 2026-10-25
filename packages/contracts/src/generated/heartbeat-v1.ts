/* Gerado do JSON Schema versionado. Execute pnpm contracts:generate. */

export interface HeartbeatV1 {
  schemaVersion: 1;
  cameraId: string;
  runId: string;
  mode: 'SIMULATED' | 'REPLAY' | 'LIVE';
  sequence: number;
  sentAt: string;
  captureState: 'RUNNING' | 'PAUSED' | 'ENDED' | 'ERROR';
  /**
   * @maxItems 8
   */
  qualityFlags: (
    | 'LOW_LIGHT'
    | 'POSSIBLE_FROZEN'
    | 'LOW_FPS'
    | 'FRAME_TIMEOUT'
    | 'CALIBRATION_REQUIRED'
    | 'STORAGE_FULL'
    | 'CAPTURE_ERROR'
    | 'MODEL_ERROR'
    | 'NO_POSE_DETECTED'
    | 'POSE_UNOBSERVABLE'
    | 'POSTURE_UNCERTAIN'
    | 'CONTEXT_UNSUPPORTED'
  )[];
  analysisFps: number;
  outboxPending: number;
  lastFrameAgeMs: number | null;
  inferenceState: 'WARMING_UP' | 'NO_POSE' | 'ONE_VALID_POSE' | 'LOW_CONFIDENCE' | 'MULTIPLE_POSES';
  versions: {
    worker: string;
    model: string;
    policy: string;
    calibration: string;
  };
}
