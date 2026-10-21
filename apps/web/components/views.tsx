'use client';
import Link from 'next/link';
import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { usePolling } from '../lib/polling';
import type { Camera, Site, Incident, Notice, Page } from '../lib/models';
import { useSession } from './session';
import { Badge, IncidentRow, ResourceState, SourceCard, Stamp, Title, label } from './ui';
export function useCatalog() {
  const { expired } = useSession();
  const cameras = usePolling<Page<Camera>>('/cameras', !expired, true);
  const sites = usePolling<Page<Site>>('/sites', !expired, true);
  return {
    cameras,
    sites,
    camera: (id: string) => cameras.data?.items.find((item) => item.id === id),
    site: (id: string) => sites.data?.items.find((item) => item.id === id),
  };
}
export function Overview() {
  const { expired } = useSession();
  const catalog = useCatalog();
  const incidents = usePolling<Page<Incident>>('/incidents?status=OPEN&limit=6', !expired);
  return (
    <>
      <Title eyebrow="ACOMPANHAMENTO LOCAL" title="Visão geral">
        <span className="date-tag">Bancada de demonstração</span>
      </Title>
      <section className="intro-panel">
        <div>
          <span className="eyebrow">UMA SUSPEITA É O INÍCIO DA VERIFICAÇÃO</span>
          <h2>
            Contexto para observar.
            <br />
            Clareza para agir.
          </h2>
          <p>Acompanhe as fontes e registre a revisão de cada acontecimento.</p>
        </div>
        <div className="intro-orbit" aria-hidden="true">
          ◎<span>r</span>
        </div>
      </section>
      <section>
        <div className="section-title">
          <h2>Incidentes em aberto</h2>
          <Link href="/incidentes">Consultar todos ↗</Link>
        </div>
        <p className="muted">
          Até 6 registros em aberto, do mais antigo ao mais recente. Sem total global estimado.
        </p>
        <ResourceState resource={incidents} empty={!incidents.data?.items.length}>
          <div className="incident-list">
            {incidents.data?.items.map((incident) => (
              <IncidentRow
                key={incident.id}
                incident={incident}
                camera={catalog.camera(incident.cameraId)?.name}
                site={catalog.site(incident.siteId)?.name}
                timezone={catalog.site(incident.siteId)?.timezone}
              />
            ))}
          </div>
        </ResourceState>
      </section>
      <section>
        <div className="section-title">
          <h2>Estado das fontes</h2>
          <Link href="/fontes">Ver fontes ↗</Link>
        </div>
        <ResourceState resource={catalog.cameras} empty={!catalog.cameras.data?.items.length}>
          <div className="source-grid">
            {catalog.cameras.data?.items.map((camera) => (
              <SourceCard
                key={camera.id}
                camera={camera}
                outdated={!!catalog.cameras.error}
                site={catalog.site(camera.siteId)?.name}
              />
            ))}
          </div>
        </ResourceState>
        {catalog.sites.error && (
          <p className="error" role="alert">
            Nomes dos locais indisponíveis; exibindo identificadores.
          </p>
        )}
      </section>
    </>
  );
}
export function Sources() {
  const catalog = useCatalog();
  return (
    <>
      <Title eyebrow="DISPONIBILIDADE" title="Fontes" />
      <p className="lead">
        O heartbeat informa a execução. Cadastrar uma câmera lógica não inicia captura.
      </p>
      <ResourceState resource={catalog.cameras} empty={!catalog.cameras.data?.items.length}>
        <div className="source-grid">
          {catalog.cameras.data?.items.map((camera) => (
            <SourceCard
              key={camera.id}
              camera={camera}
              site={catalog.site(camera.siteId)?.name}
              outdated={!!catalog.cameras.error}
            />
          ))}
        </div>
      </ResourceState>
      {catalog.sites.error && (
        <p className="error" role="alert">
          Não foi possível atualizar os nomes dos locais.
        </p>
      )}
    </>
  );
}
export function Incidents() {
  const params = useSearchParams();
  const router = useRouter();
  const { expired } = useSession();
  const catalog = useCatalog();
  const query = new URLSearchParams();
  for (const name of ['status', 'mode', 'cameraId', 'from', 'to', 'cursor']) {
    const value = params.get(name);
    if (value) query.set(name, value);
  }
  query.set('limit', '20');
  const incidents = usePolling<Page<Incident>>(`/incidents?${query}`, !expired);
  function filters(form: HTMLFormElement) {
    const next = new URLSearchParams();
    new FormData(form).forEach((value, key) => {
      if (value) next.set(key, ['from', 'to'].includes(key) ? String(value) + 'Z' : String(value));
    });
    router.push(`/incidentes?${next}`);
  }
  const suffix = params.size ? `?${params}` : '';
  return (
    <>
      <Title eyebrow="REGISTROS PARA REVISÃO" title="Incidentes" />
      <p className="lead">
        Suspeitas recebidas pela API, com origem, contexto e estado da revisão.
      </p>
      <form
        className="filters"
        key={params.toString()}
        onSubmit={(event) => {
          event.preventDefault();
          filters(event.currentTarget);
        }}
      >
        <label>
          Estado
          <select name="status" defaultValue={params.get('status') ?? ''}>
            <option value="">Todos</option>
            {['OPEN', 'ACKNOWLEDGED', 'IN_PROGRESS', 'RESOLVED', 'DISMISSED'].map((value) => (
              <option key={value} value={value}>
                {label(value)}
              </option>
            ))}
          </select>
        </label>
        <label>
          Modo
          <select name="mode" defaultValue={params.get('mode') ?? ''}>
            <option value="">Todos os modos</option>
            {['SIMULATED', 'REPLAY', 'LIVE'].map((value) => (
              <option key={value} value={value}>
                {label(value)}
              </option>
            ))}
          </select>
        </label>
        <label>
          Câmera
          <CameraFilter
            initial={params.get('cameraId') ?? ''}
            cameras={catalog.cameras.data?.items ?? []}
          />
        </label>
        <label>
          De (UTC)
          <input
            name="from"
            type="datetime-local"
            step="1"
            defaultValue={params.get('from')?.replace('Z', '') ?? ''}
          />
        </label>
        <label>
          Até (UTC)
          <input
            name="to"
            type="datetime-local"
            step="1"
            defaultValue={params.get('to')?.replace('Z', '') ?? ''}
          />
        </label>
        <button className="primary">Aplicar filtros</button>
        <Link href="/incidentes">Limpar</Link>
      </form>
      <ResourceState resource={incidents} empty={!incidents.data?.items.length}>
        <div className="incident-list">
          {incidents.data?.items.map((incident) => (
            <IncidentRow
              key={incident.id}
              incident={incident}
              camera={catalog.camera(incident.cameraId)?.name}
              site={catalog.site(incident.siteId)?.name}
              timezone={catalog.site(incident.siteId)?.timezone}
              suffix={suffix}
            />
          ))}
        </div>
        <div className="pagination">
          <span>{incidents.data?.items.length} registros nesta página · ordem de criação</span>
          {params.get('cursor') && (
            <Link
              href={`/incidentes?${new URLSearchParams([...params].filter(([key]) => key !== 'cursor'))}`}
            >
              Primeira página
            </Link>
          )}
          {incidents.data?.nextCursor && (
            <Link
              href={`/incidentes?${new URLSearchParams([...params].filter(([key]) => key !== 'cursor').concat([['cursor', incidents.data.nextCursor]]))}`}
            >
              Próxima página →
            </Link>
          )}
        </div>
      </ResourceState>
      {(catalog.cameras.error || catalog.sites.error) && (
        <p className="error" role="alert">
          Catálogo desatualizado. Identificadores são exibidos quando os nomes não estão
          disponíveis.
        </p>
      )}
    </>
  );
}
export function Notices() {
  const { expired } = useSession();
  const catalog = useCatalog();
  const params = useSearchParams();
  const router = useRouter();
  const cursor = params.get('cursor');
  const notices = usePolling<Page<Notice>>(
    `/notifications?limit=20${cursor ? `&cursor=${encodeURIComponent(cursor)}` : ''}`,
    !expired,
  );
  return (
    <>
      <Title eyebrow="CAIXA LOCAL" title="Avisos locais" />
      <div className="info-strip">
        Canal SIMULATED: registros locais de demonstração. Não são mensagens enviadas a familiares
        ou contatos.
      </div>
      <ResourceState resource={notices} empty={!notices.data?.items.length}>
        <div className="notice-list">
          {notices.data?.items.map((notice) => (
            <article key={notice.id} className="notice-card">
              <div className="notice-icon">♧</div>
              <div>
                <div className="badges">
                  <span className="badge">Canal SIMULATED</span>
                  <Badge value={notice.intent.incident.mode} />
                  <Badge value={notice.intent.incident.deliveryClass} />
                </div>
                <h2>
                  <Link href={`/incidentes/${notice.intent.incidentId}`}>
                    {label(notice.intent.incident.kind)}
                  </Link>
                </h2>
                <p>
                  {catalog.camera(notice.intent.incident.cameraId)?.name ??
                    notice.intent.incident.cameraId}
                </p>
                <p className="muted">
                  Aviso registrado localmente · urgência:{' '}
                  {notice.urgent ? 'sim, conforme classificação original' : 'não'}
                </p>
                <Stamp value={notice.createdAt} />
              </div>
            </article>
          ))}
        </div>
        <div className="pagination">
          <button disabled={!cursor} onClick={() => router.push('/avisos')}>
            Primeira página
          </button>
          <button
            disabled={!notices.data?.nextCursor}
            onClick={() =>
              router.push(`/avisos?cursor=${encodeURIComponent(notices.data!.nextCursor!)}`)
            }
          >
            Próxima página →
          </button>
        </div>
      </ResourceState>
    </>
  );
}
function CameraFilter({ initial, cameras }: { initial: string; cameras: Camera[] }) {
  const [value, setValue] = useState(initial);
  return (
    <select name="cameraId" value={value} onChange={(event) => setValue(event.target.value)}>
      <option value="">Todas as câmeras</option>
      {cameras.map((camera) => (
        <option key={camera.id} value={camera.id}>
          {camera.name}
        </option>
      ))}
    </select>
  );
}
