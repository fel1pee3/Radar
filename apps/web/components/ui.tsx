'use client';
import Link from 'next/link';
import type { ReactNode } from 'react';
import type { Camera, Incident } from '../lib/models';
export const labels: Record<string, string> = {
  OPEN: 'Aberto',
  ACKNOWLEDGED: 'Reconhecido',
  IN_PROGRESS: 'Atendimento registrado',
  RESOLVED: 'Encerrado',
  DISMISSED: 'Descartado',
  SIMULATED: 'Simulado',
  REPLAY: 'Reprodução',
  LIVE: 'Ao vivo',
  TEST: 'Teste',
  CURRENT: 'Atual',
  DELAYED: 'Atrasado',
  CLOCK_UNCERTAIN: 'Relógio incerto',
  PERSON_ON_FLOOR: 'Possível pessoa no chão',
  POSSIBLE_FALL: 'Possível queda',
  ONLINE: 'Execução ativa',
  DEGRADED: 'Execução degradada',
  OFFLINE: 'Sem comunicação',
  PAUSED: 'Pausada',
  SOURCE_ENDED: 'Fonte encerrada',
  UNREVIEWED: 'Não revisado',
  PERSON_ON_FLOOR_CONFIRMED: 'Postura no chão confirmada',
  FALL_REPORTED: 'Queda relatada',
  FALSE_POSITIVE: 'Falso positivo',
  INCONCLUSIVE: 'Inconclusivo',
  ASSISTANCE_RECORDED: 'Assistência registrada',
  NO_ASSISTANCE_NEEDED: 'Sem necessidade de assistência',
  TEST_COMPLETED: 'Teste concluído',
  FALSE_DETECTION: 'Detecção incorreta',
  TEST_EVENT: 'Evento de teste',
  DUPLICATE: 'Duplicado',
  OTHER: 'Outro motivo',
  RECOGNIZE: 'Reconhecimento',
  START_RESPONSE: 'Início de atendimento registrado',
  SET_REVIEW: 'Revisão humana',
  RESOLVE: 'Encerramento',
  DISMISS: 'Descarte',
  ADD_NOTE: 'Nota adicionada',
  SNAPSHOT_ACCESSED: 'Imagem consultada',
  SNAPSHOT_DELETED: 'Imagem excluída',
  EVIDENCE_PREFERENCE_CHANGED: 'Preferência de evidência alterada',
  RETENTION_PREFERENCE_CHANGED: 'Preferência de retenção alterada',
  INCIDENT_CREATED: 'Incidente criado',
  SIMULATED_NOTIFICATION_RECORDED: 'Aviso local registrado',
};
export const label = (value: string | null | undefined) =>
  value ? (labels[value] ?? value) : 'Não informado';
export function Stamp({
  value,
  timezone = 'America/Sao_Paulo',
}: {
  value: string | null;
  timezone?: string;
}) {
  if (!value) return <span>Não recebido</span>;
  return (
    <time dateTime={value}>
      {new Intl.DateTimeFormat('pt-BR', {
        timeZone: timezone,
        dateStyle: 'short',
        timeStyle: 'medium',
      }).format(new Date(value))}
      <small className="timezone">{timezone}</small>
    </time>
  );
}
export function Badge({ value }: { value: string }) {
  return (
    <span className={`badge badge-${value.toLowerCase()}`} title={value}>
      {label(value)}
    </span>
  );
}
export function Title({
  eyebrow,
  title,
  children,
}: {
  eyebrow: string;
  title: string;
  children?: ReactNode;
}) {
  return (
    <header className="page-title">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
      </div>
      {children}
    </header>
  );
}
export function ResourceState({
  resource,
  empty = false,
  children,
}: {
  resource: { data?: unknown; error?: string; updatedAt?: Date; refresh(): void };
  empty?: boolean;
  children: ReactNode;
}) {
  return (
    <>
      {resource.error && (
        <div className="alert error" role="alert">
          <strong>Atualização indisponível.</strong> {resource.error}{' '}
          {resource.data ? 'Os dados anteriores estão desatualizados.' : ''}
          <button onClick={resource.refresh}>Tentar novamente</button>
        </div>
      )}
      {!resource.data && !resource.error ? (
        <p role="status" className="empty">
          Carregando dados…
        </p>
      ) : resource.data ? (
        <>
          <p className="refresh-note">
            {resource.error ? 'Última consulta válida' : 'Atualizado'}:{' '}
            {resource.updatedAt?.toLocaleTimeString('pt-BR')} · consultas a cada 2 s enquanto a aba
            estiver visível
          </p>
          {empty ? (
            <div className="empty">
              <span className="empty-symbol">◎</span>
              <h2>Nenhum registro encontrado</h2>
              <p>Os registros aparecerão aqui quando forem recebidos pela API.</p>
            </div>
          ) : (
            children
          )}
        </>
      ) : null}
    </>
  );
}
export function SourceCard({
  camera,
  site,
  outdated = false,
}: {
  camera: Camera;
  site?: string;
  outdated?: boolean;
}) {
  const heartbeat = camera.health.heartbeat;
  return (
    <article className={`source-card ${camera.health.stale ? 'stale' : ''}`}>
      <div className="row">
        <span className="source-icon">▣</span>
        {outdated ? (
          <span className="badge">Estado não atualizado</span>
        ) : (
          <Badge value={camera.health.state} />
        )}
      </div>
      <h3>{camera.name}</h3>
      <p className="muted">
        {site ?? camera.siteId} · {camera.type}
      </p>
      {outdated && (
        <p className="warning">
          API indisponível. Último estado conhecido: {label(camera.health.state)}.
        </p>
      )}
      {heartbeat ? (
        <>
          <Badge value={heartbeat.mode} />
          <p>
            {heartbeat.mode === 'SIMULATED'
              ? 'Heartbeat do simulador; nenhuma câmera física comprovada.'
              : 'Estado informado pela execução.'}
          </p>
          <p className="fine">
            Último heartbeat: <Stamp value={camera.health.receivedAt} />
          </p>
          {heartbeat.qualityFlags.length > 0 && (
            <p className="error">Flags: {heartbeat.qualityFlags.join(', ')}</p>
          )}
          {camera.health.stale && (
            <p className="warning">
              Informação desatualizada · {Math.floor((camera.health.ageMs ?? 0) / 1000)} s desde o
              recebimento
            </p>
          )}
        </>
      ) : (
        <p className="fine">Sem heartbeat. Cadastrar esta câmera não inicia captura.</p>
      )}
      <p className="fine">Execução esperada: {camera.expectedRunning ? 'sim' : 'não'}</p>
    </article>
  );
}
export function IncidentRow({
  incident,
  camera,
  site,
  timezone,
  suffix = '',
}: {
  incident: Incident;
  camera?: string;
  site?: string;
  timezone?: string;
  suffix?: string;
}) {
  return (
    <Link className="incident-row" href={`/incidentes/${incident.id}${suffix}`}>
      <div className="incident-icon">◎</div>
      <div className="incident-main">
        <h3>{label(incident.kind)}</h3>
        <p>
          {camera ?? incident.cameraId} <span className="muted">/ {site ?? incident.siteId}</span>
        </p>
        <div className="badges">
          <Badge value={incident.mode} />
          <Badge value={incident.deliveryClass} />
        </div>
      </div>
      <div className="incident-time">
        <Stamp value={incident.occurredAt} timezone={timezone} />
      </div>
      <Badge value={incident.status} />
      <span aria-hidden="true">↗</span>
    </Link>
  );
}
