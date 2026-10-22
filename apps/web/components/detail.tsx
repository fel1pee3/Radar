'use client';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useState, useRef } from 'react';
import type { FormEvent } from 'react';
import type { IncidentActionV1 } from '@radar/contracts';
import type { Incident, Page, Audit, Review } from '../lib/models';
import { api, ApiError } from '../lib/api';
import { usePolling } from '../lib/polling';
import { useSession } from './session';
import { useCatalog } from './views';
import { Badge, ResourceState, Stamp, Title, label } from './ui';
import { Snapshot } from './evidence';
import { Pose } from './pose';
const reviews: Review[] = [
  'UNREVIEWED',
  'PERSON_ON_FLOOR_CONFIRMED',
  'FALL_REPORTED',
  'FALSE_POSITIVE',
  'INCONCLUSIVE',
];
const signals: Record<string, string> = {
  floorDurationMs: 'Duração no piso (ms)',
  torsoAngleDeg: 'Ângulo do tronco (°)',
  bboxAspectRatio: 'Razão de aspecto corporal',
  hipInFloorZone: 'Quadril na região de piso',
  rapidDescentObserved: 'Descida rápida observada',
  validPoseFraction: 'Fração de pose válida',
  analysisFps: 'Análises por segundo',
};
export function IncidentDetail({ id }: { id: string }) {
  const { expired } = useSession();
  const params = useSearchParams();
  const catalog = useCatalog();
  const resource = usePolling<Incident>(`/incidents/${id}`, !expired);
  const audit = usePolling<Page<Audit>>(`/audit?incidentId=${id}`, !expired, true);
  const incident = resource.data;
  const site = incident && catalog.site(incident.siteId);
  const [floorVersion, setFloorVersion] = useState(0);
  const newer = !!incident && incident.version >= floorVersion;
  return (
    <>
      <Link className="back-link" href={`/incidentes${params.size ? `?${params}` : ''}`}>
        ← Voltar aos incidentes
      </Link>
      <Title
        eyebrow="CONTEXTO E REVISÃO"
        title={incident ? label(incident.kind) : 'Detalhe do incidente'}
      />
      <ResourceState resource={resource}>
        {incident && (
          <>
            <div className="detail-summary">
              <div className="badges">
                <Badge value={incident.mode} />
                <Badge value={incident.deliveryClass} />
                <Badge value={incident.status} />
              </div>
              <p>
                {catalog.camera(incident.cameraId)?.name ?? incident.cameraId} ·{' '}
                {site?.name ?? incident.siteId}
              </p>
              <p className="fine">
                ID {incident.id} · versão {incident.version}
              </p>
              {incident.mode === 'SIMULATED' && (
                <p className="simulation-note">
                  Evento artificial. Este registro não comprova captura ou detecção por IA.
                </p>
              )}
              {['DELAYED', 'CLOCK_UNCERTAIN'].includes(incident.deliveryClass) && (
                <p className="warning">
                  {label(incident.deliveryClass)}: confira os horários originais antes de
                  interpretar a atualidade.
                </p>
              )}
            </div>
            <div className="detail-grid">
              <section className="panel">
                <div className="section-title">
                  <h2>Evidência corporal</h2>
                  <span className="fine">Evidência mínima</span>
                </div>
                {incident.evidenceMode === 'none' ? (
                  <p>Evidência corporal desabilitada.</p>
                ) : incident.poseRedactedAt ? (
                  <p>Pose expirada pela política de retenção.</p>
                ) : (
                  <Pose points={incident.pose} mode={incident.mode} />
                )}
                <Snapshot
                  key={incident.id}
                  incident={incident}
                  onChange={() => {
                    resource.refresh();
                    audit.refresh();
                  }}
                />
                <h2>Sinais do evento</h2>
                {incident.signals ? (
                  <dl className="data-list">
                    {Object.entries(incident.signals).map(([key, value]) => (
                      <div key={key}>
                        <dt>{signals[key] ?? key}</dt>
                        <dd>{typeof value === 'boolean' ? (value ? 'Sim' : 'Não') : value}</dd>
                      </div>
                    ))}
                  </dl>
                ) : (
                  <p>Sinais indisponíveis ou redigidos.</p>
                )}
              </section>
              <div className="stack">
                <section className="panel">
                  <h2>Registro humano</h2>
                  <dl className="data-list">
                    <div>
                      <dt>Estado</dt>
                      <dd>{label(incident.status)}</dd>
                    </div>
                    <div>
                      <dt>Revisão</dt>
                      <dd>{label(incident.review)}</dd>
                    </div>
                    <div>
                      <dt>Desfecho</dt>
                      <dd>{label(incident.outcome)}</dd>
                    </div>
                    <div>
                      <dt>Motivo do descarte</dt>
                      <dd>{label(incident.dismissReason)}</dd>
                    </div>
                  </dl>
                </section>
                <section className="panel">
                  <h2>Revisar acontecimento</h2>
                  {!newer && <p className="warning">Aguardando a versão confirmada pela API…</p>}
                  <Actions
                    incident={incident}
                    disabled={!!resource.error || !newer || expired}
                    onCommitted={(version) => {
                      setFloorVersion(version);
                      resource.refresh();
                      audit.refresh();
                    }}
                    onConflict={() => {
                      resource.refresh();
                      audit.refresh();
                    }}
                  />
                </section>
              </div>
            </div>
            <section className="panel">
              <h2>Horários e versões</h2>
              <div className="metadata-grid">
                <div>
                  <h3>Horário original</h3>
                  <Stamp value={incident.occurredAt} timezone={site?.timezone} />
                </div>
                <div>
                  <h3>Emitido pelo worker</h3>
                  <Stamp value={incident.detectedAt} timezone={site?.timezone} />
                </div>
                <div>
                  <h3>Recebido pela API</h3>
                  <Stamp value={incident.receivedAt} timezone={site?.timezone} />
                </div>
                <div>
                  <h3>Offset do arquivo</h3>
                  <p>
                    {incident.sourceOffsetMs === null
                      ? 'Não se aplica'
                      : `${incident.sourceOffsetMs} ms`}
                  </p>
                </div>
              </div>
              <dl className="version-list">
                {incident.versions ? (
                  Object.entries(incident.versions).map(([key, value]) => (
                    <div key={key}>
                      <dt>
                        {
                          (
                            {
                              worker: 'Worker',
                              model: 'Modelo',
                              policy: 'Política',
                              calibration: 'Calibração',
                            } as Record<string, string>
                          )[key]
                        }
                      </dt>
                      <dd>{value}</dd>
                    </div>
                  ))
                ) : (
                  <p>Versões indisponíveis.</p>
                )}
              </dl>
            </section>
          </>
        )}
      </ResourceState>
      <section className="panel">
        <h2>Histórico auditado</h2>
        <ResourceState resource={audit} empty={!audit.data?.items.length}>
          <ol className="timeline">
            {audit.data?.items.map((entry) => (
              <li key={entry.id}>
                <span className="timeline-dot" />
                <div>
                  <strong>{label(entry.incidentAction?.action ?? entry.action)}</strong>
                  <p className="fine">
                    <Stamp value={entry.createdAt} timezone={site?.timezone} /> ·{' '}
                    {entry.actorId ? `Ator ${entry.actorId}` : 'Sistema local'}
                    {entry.toVersion
                      ? ` · versão ${entry.fromVersion ?? '—'} → ${entry.toVersion}`
                      : ''}
                  </p>
                  {entry.incidentAction?.payload && 'note' in entry.incidentAction.payload && (
                    <p className="note-text">{entry.incidentAction.payload.note}</p>
                  )}
                  {entry.incidentAction && (
                    <p>
                      {label(entry.incidentAction.result.status)} ·{' '}
                      {label(entry.incidentAction.result.review)}
                      {entry.incidentAction.result.outcome &&
                        ` · ${label(entry.incidentAction.result.outcome)}`}
                    </p>
                  )}
                </div>
              </li>
            ))}
          </ol>
        </ResourceState>
      </section>
    </>
  );
}
function Actions({
  incident,
  disabled,
  onCommitted,
  onConflict,
}: {
  incident: Incident;
  disabled: boolean;
  onCommitted(version: number): void;
  onConflict(): void;
}) {
  const [kind, setKind] = useState('ADD_NOTE');
  const [note, setNote] = useState('');
  const [review, setReview] = useState<Review>('INCONCLUSIVE');
  const [outcome, setOutcome] = useState('TEST_COMPLETED');
  const [reason, setReason] = useState('TEST_EVENT');
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [blocked, setBlocked] = useState(false);
  const [retrying, setRetrying] = useState(false);
  const pending = useRef<IncidentActionV1 | null>(null);
  const sending = useRef(false);
  const final = incident.status === 'RESOLVED' || incident.status === 'DISMISSED';
  const choices = [
    ...(incident.status === 'OPEN' ? ['RECOGNIZE'] : []),
    ...(incident.status === 'ACKNOWLEDGED' ? ['START_RESPONSE'] : []),
    ...(!final
      ? [
          'SET_REVIEW',
          ...(['ACKNOWLEDGED', 'IN_PROGRESS'].includes(incident.status) ? ['RESOLVE'] : []),
          'DISMISS',
        ]
      : []),
    'ADD_NOTE',
  ];
  function choose(value: string) {
    setKind(value);
    setRetrying(false);
    pending.current = null;
    setBlocked(false);
    setFeedback('');
  }
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (sending.current || disabled || blocked) return;
    sending.current = true;
    setBusy(true);
    setFeedback('');
    if (!pending.current) {
      const base = { actionId: crypto.randomUUID(), expectedVersion: incident.version };
      pending.current = (
        kind === 'SET_REVIEW'
          ? { ...base, action: kind, review, ...(note.trim() ? { note } : {}) }
          : kind === 'RESOLVE'
            ? { ...base, action: kind, review, outcome }
            : kind === 'DISMISS'
              ? { ...base, action: kind, reason, ...(note.trim() ? { note } : {}) }
              : kind === 'ADD_NOTE'
                ? { ...base, action: kind, note }
                : { ...base, action: kind }
      ) as IncidentActionV1;
    }
    try {
      const result = await api<{ version: number }>(`/incidents/${incident.id}/actions`, {
        method: 'POST',
        body: pending.current,
      });
      pending.current = null;
      setRetrying(false);
      setNote('');
      setFeedback('Ação registrada com sucesso.');
      onCommitted(result.version);
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        pending.current = null;
        setRetrying(false);
        setBlocked(true);
        setFeedback(
          'Conflito de versão ou intenção. O registro foi atualizado. Confira o estado e confirme sua intenção antes de enviar outra ação. Seu texto foi mantido.',
        );
        onConflict();
      } else if (
        error instanceof ApiError &&
        error.status >= 400 &&
        error.status < 500 &&
        error.status !== 401
      ) {
        pending.current = null;
        setRetrying(false);
        setFeedback(error.message);
      } else {
        setRetrying(true);
        setFeedback(
          'Não foi possível confirmar a gravação. O texto e a identidade da tentativa foram mantidos. Use “Reenviar mesma tentativa” após restabelecer a conexão.',
        );
      }
    } finally {
      sending.current = false;
      setBusy(false);
    }
  }
  const locked = busy || retrying;
  return (
    <form className="stack" onSubmit={submit}>
      <label>
        Ação
        <select value={kind} onChange={(event) => choose(event.target.value)} disabled={locked}>
          {choices.map((value) => (
            <option key={value} value={value}>
              {label(value)}
            </option>
          ))}
          {!choices.includes(kind) && (
            <option value={kind} disabled>
              Ação anterior indisponível
            </option>
          )}
        </select>
      </label>
      {(kind === 'SET_REVIEW' || kind === 'RESOLVE') && (
        <label>
          Revisão humana
          <select
            value={review}
            disabled={locked}
            onChange={(event) => setReview(event.target.value as Review)}
          >
            {reviews
              .filter((value) => kind !== 'RESOLVE' || value !== 'UNREVIEWED')
              .map((value) => (
                <option key={value} value={value}>
                  {label(value)}
                </option>
              ))}
          </select>
        </label>
      )}
      {kind === 'RESOLVE' && (
        <label>
          Desfecho
          <select
            value={outcome}
            disabled={locked}
            onChange={(event) => setOutcome(event.target.value)}
          >
            {['ASSISTANCE_RECORDED', 'NO_ASSISTANCE_NEEDED', 'INCONCLUSIVE', 'TEST_COMPLETED'].map(
              (value) => (
                <option key={value} value={value}>
                  {label(value)}
                </option>
              ),
            )}
          </select>
        </label>
      )}
      {kind === 'DISMISS' && (
        <label>
          Motivo
          <select
            value={reason}
            disabled={locked}
            onChange={(event) => setReason(event.target.value)}
          >
            {['FALSE_DETECTION', 'TEST_EVENT', 'DUPLICATE', 'OTHER'].map((value) => (
              <option key={value} value={value}>
                {label(value)}
              </option>
            ))}
          </select>
        </label>
      )}
      {['ADD_NOTE', 'SET_REVIEW', 'DISMISS'].includes(kind) && (
        <label>
          Nota
          <textarea
            aria-label="Nota"
            value={note}
            onChange={(event) => setNote(event.target.value)}
            maxLength={2000}
            required={kind === 'ADD_NOTE' || (kind === 'DISMISS' && reason === 'OTHER')}
            disabled={locked}
            rows={4}
          />
          <small>{Array.from(note).length}/2.000 caracteres</small>
        </label>
      )}
      {feedback && (
        <p role="status" className={blocked ? 'warning' : 'action-feedback'}>
          {feedback}
        </p>
      )}
      {blocked ? (
        <button
          key="prepare"
          type="button"
          onClick={(event) => {
            event.preventDefault();
            setBlocked(false);
            setFeedback('Confira a ação escolhida e envie para usar a versão atual.');
          }}
        >
          Conferi o estado; preparar nova tentativa
        </button>
      ) : (
        <button
          key="submit"
          type="submit"
          className="primary"
          disabled={
            busy ||
            disabled ||
            (!retrying && !choices.includes(kind)) ||
            ((kind === 'ADD_NOTE' || (kind === 'DISMISS' && reason === 'OTHER')) && !note.trim())
          }
        >
          {busy ? 'Registrando…' : retrying ? 'Reenviar mesma tentativa' : 'Registrar ação'}
        </button>
      )}
      <p className="fine">
        Versão exibida: {incident.version}. Atendimento registrado não significa socorro garantido.
      </p>
    </form>
  );
}
