/* Gerado do JSON Schema versionado. Execute pnpm contracts:generate. */

export type IncidentActionV1 =
  | {
      actionId: string;
      expectedVersion: number;
      action: 'RECOGNIZE';
    }
  | {
      actionId: string;
      expectedVersion: number;
      action: 'START_RESPONSE';
    }
  | {
      actionId: string;
      expectedVersion: number;
      action: 'SET_REVIEW';
      review:
        | 'UNREVIEWED'
        | 'PERSON_ON_FLOOR_CONFIRMED'
        | 'FALL_REPORTED'
        | 'FALSE_POSITIVE'
        | 'INCONCLUSIVE';
      note?: string;
    }
  | {
      actionId: string;
      expectedVersion: number;
      action: 'RESOLVE';
      review: 'PERSON_ON_FLOOR_CONFIRMED' | 'FALL_REPORTED' | 'FALSE_POSITIVE' | 'INCONCLUSIVE';
      outcome: 'ASSISTANCE_RECORDED' | 'NO_ASSISTANCE_NEEDED' | 'INCONCLUSIVE' | 'TEST_COMPLETED';
    }
  | {
      actionId: string;
      expectedVersion: number;
      action: 'DISMISS';
      reason: 'FALSE_DETECTION' | 'TEST_EVENT' | 'DUPLICATE' | 'OTHER';
      note?: string;
    }
  | {
      actionId: string;
      expectedVersion: number;
      action: 'ADD_NOTE';
      note: string;
    };
