import type { EventV1 } from '@radar/contracts';
const edges = [
  [11, 12],
  [11, 13],
  [13, 15],
  [12, 14],
  [14, 16],
  [15, 17],
  [15, 19],
  [15, 21],
  [16, 18],
  [16, 20],
  [16, 22],
  [11, 23],
  [12, 24],
  [23, 24],
  [23, 25],
  [25, 27],
  [24, 26],
  [26, 28],
  [27, 29],
  [29, 31],
  [27, 31],
  [28, 30],
  [30, 32],
  [28, 32],
];
export function Pose({ points, mode }: { points: EventV1['pose'] | null; mode: EventV1['mode'] }) {
  if (!points?.length)
    return (
      <div className="pose-empty">
        <span>◇</span>
        <p>Sem pose de evidência neste evento.</p>
        <small>A ausência de pose não informa se há uma pessoa no local.</small>
      </div>
    );
  const usesKeypointScore = points.some((point) => 'confidence' in point);
  const visible = points.filter(
    (point) => ('confidence' in point ? point.confidence : point.visibility) >= 0.5,
  );
  const byId = new Map(visible.map((point) => [point.index, point]));
  return (
    <figure className="pose-figure">
      <svg
        viewBox="0 0 640 480"
        role="img"
        aria-label={
          mode === 'SIMULATED'
            ? 'Esqueleto de pose sintética simulada'
            : 'Esqueleto corporal de evidência'
        }
      >
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#203c3e" strokeWidth="1" />
          </pattern>
        </defs>
        <rect width="640" height="480" fill="url(#grid)" />
        {edges.map(([a, b]) => {
          const start = byId.get(a!),
            end = byId.get(b!);
          return start && end ? (
            <line
              key={`${a}-${b}`}
              x1={start.x * 640}
              y1={start.y * 480}
              x2={end.x * 640}
              y2={end.y * 480}
              stroke="#92e3bf"
              strokeWidth="5"
            />
          ) : null;
        })}
        {visible.map((point) => (
          <circle key={point.index} cx={point.x * 640} cy={point.y * 480} r="6" fill="#d7f8e9" />
        ))}
      </svg>
      <figcaption>
        {mode === 'SIMULATED'
          ? 'POSE SINTÉTICA · EVIDÊNCIA SIMULADA'
          : 'POSE CORPORAL · EVIDÊNCIA DO EVENTO'}
        <small>
          {usesKeypointScore
            ? 'RTMO experimental · Score articular ≥ 0,5; não comprova visibilidade. Sem imagem de câmera.'
            : 'Pontos com visibilidade ≥ 0,5. Sem imagem de câmera.'}
        </small>
      </figcaption>
    </figure>
  );
}
