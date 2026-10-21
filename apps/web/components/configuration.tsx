'use client';
import { useState, useRef } from 'react';
import type { FormEvent } from 'react';
import type { Camera, Credential, Page } from '../lib/models';
import { api } from '../lib/api';
import { usePolling } from '../lib/polling';
import { useSession } from './session';
import { useCatalog } from './views';
import { ResourceState, Title, Stamp } from './ui';
export function Configuration() {
  const { user } = useSession();
  const catalog = useCatalog();
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>, path: string, camera = false) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setMessage('');
    const form = event.currentTarget;
    const data = new FormData(form);
    try {
      await api(path, {
        method: 'POST',
        body: camera
          ? {
              name: String(data.get('name')),
              siteId: String(data.get('siteId')),
              type: String(data.get('type')),
            }
          : { name: String(data.get('name')), timezone: String(data.get('timezone')) },
      });
      form.reset();
      catalog.cameras.refresh();
      catalog.sites.refresh();
      setMessage('Cadastro criado.');
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : 'Não foi possível criar. Confira a lista antes de repetir.',
      );
    } finally {
      setBusy(false);
    }
  }
  if (user?.role !== 'OWNER')
    return (
      <>
        <Title eyebrow="PERMISSÕES" title="Configuração restrita" />
        <p role="alert">
          A configuração exige um proprietário. Operadores podem consultar fontes e revisar
          incidentes.
        </p>
      </>
    );
  return (
    <>
      <Title eyebrow="PREPARAR A BANCADA" title="Configuração" />
      <p className="lead">
        Locais, câmeras lógicas e credenciais. O cadastro não abre uma câmera nem inicia captura.
      </p>
      {message && (
        <p className="info-strip" role="status">
          {message}
        </p>
      )}
      <div className="config-grid">
        <section className="panel">
          <h2>Novo local</h2>
          <form className="stack" onSubmit={(event) => submit(event, '/sites')}>
            <label>
              Nome do local
              <input name="name" required maxLength={120} />
            </label>
            <label>
              Fuso horário
              <input name="timezone" required maxLength={80} defaultValue="America/Sao_Paulo" />
            </label>
            <button className="primary" disabled={busy}>
              Criar local
            </button>
          </form>
          <ResourceState resource={catalog.sites} empty={!catalog.sites.data?.items.length}>
            <ul className="plain-list">
              {catalog.sites.data?.items.map((site) => (
                <li key={site.id}>
                  <strong>{site.name}</strong>
                  <small>{site.timezone}</small>
                </li>
              ))}
            </ul>
          </ResourceState>
        </section>
        <section className="panel">
          <h2>Nova câmera lógica</h2>
          <form className="stack" onSubmit={(event) => submit(event, '/cameras', true)}>
            <label>
              Nome da câmera
              <input name="name" required maxLength={120} />
            </label>
            <label>
              Local
              <select name="siteId" required>
                <option value="">Selecione</option>
                {catalog.sites.data?.items.map((site) => (
                  <option key={site.id} value={site.id}>
                    {site.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Tipo da fonte
              <select name="type">
                <option value="FILE">Arquivo (FILE)</option>
                <option value="WEBCAM">Webcam (WEBCAM)</option>
                <option value="RTSP">Câmera IP (RTSP)</option>
              </select>
            </label>
            <p className="fine">
              O modo SIMULATED é definido pelo evento. URI e senha da câmera ficam fora do painel.
            </p>
            <button className="primary" disabled={busy}>
              Criar câmera
            </button>
          </form>
        </section>
      </div>
      <h2>Câmeras cadastradas</h2>
      <ResourceState resource={catalog.cameras} empty={!catalog.cameras.data?.items.length}>
        <div className="stack">
          {catalog.cameras.data?.items.map((camera) => (
            <CameraEditor
              key={camera.id}
              camera={camera}
              sites={catalog.sites.data?.items ?? []}
              onSaved={catalog.cameras.refresh}
            />
          ))}
        </div>
      </ResourceState>
    </>
  );
}
function CameraEditor({
  camera,
  sites,
  onSaved,
}: {
  camera: Camera;
  sites: { id: string; name: string }[];
  onSaved(): void;
}) {
  const { expired } = useSession();
  const [editing, setEditing] = useState(false);
  const [secret, setSecret] = useState<Credential | null>(null);
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const mutation = useRef(false);
  const credentials = usePolling<Page<Omit<Credential, 'token'> & { revokedAt: string | null }>>(
    `/cameras/${camera.id}/device-credentials`,
    !expired,
    true,
  );
  async function execute(work: () => Promise<void>) {
    if (mutation.current) return;
    mutation.current = true;
    setBusy(true);
    setMessage('');
    try {
      await work();
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : 'Operação não confirmada. Confira os metadados antes de repetir.',
      );
    } finally {
      mutation.current = false;
      setBusy(false);
    }
  }
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    await execute(async () => {
      await api(`/cameras/${camera.id}`, {
        method: 'PATCH',
        body: {
          name: String(data.get('name')),
          siteId: String(data.get('siteId')),
          type: String(data.get('type')),
          expectedRunning: data.get('expectedRunning') === 'on',
        },
      });
      setEditing(false);
      onSaved();
      setMessage('Câmera atualizada.');
    });
  }
  async function issue() {
    setConfirm(false);
    setSecret(null);
    await execute(async () => {
      const issued = await api<Credential>(`/cameras/${camera.id}/device-credentials`, {
        method: 'POST',
        body: {},
      });
      setSecret(issued);
      credentials.refresh();
    });
  }
  return (
    <section className="panel camera-editor">
      <div className="section-title">
        <div>
          <h3>{camera.name}</h3>
          <p className="fine">
            {camera.type} · ID <code>{camera.id}</code>
          </p>
        </div>
        <button onClick={() => setEditing((value) => !value)} disabled={busy}>
          {editing ? 'Cancelar edição' : 'Editar câmera'}
        </button>
      </div>
      {editing && (
        <form className="stack" onSubmit={save}>
          <label>
            Nome
            <input name="name" defaultValue={camera.name} required maxLength={120} />
          </label>
          <label>
            Local
            <select name="siteId" defaultValue={camera.siteId}>
              {sites.map((site) => (
                <option key={site.id} value={site.id}>
                  {site.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Tipo
            <select name="type" defaultValue={camera.type}>
              {['FILE', 'WEBCAM', 'RTSP'].map((type) => (
                <option key={type}>{type}</option>
              ))}
            </select>
          </label>
          <label className="check-label">
            <input type="checkbox" name="expectedRunning" defaultChecked={camera.expectedRunning} />{' '}
            Espero uma execução ativa
          </label>
          <button className="primary" disabled={busy}>
            Salvar câmera
          </button>
        </form>
      )}
      <div className="credential-area">
        <h3>Credenciais de worker</h3>
        <p className="fine">
          Emitir ou rotacionar revoga a credencial anterior. O token aparece uma única vez e
          permanece apenas nesta tela até ser ocultado.
        </p>
        {confirm ? (
          <div className="info-strip">
            <p>
              Confirmar emissão/rotação para <strong>{camera.name}</strong>? O token anterior
              deixará de funcionar.
            </p>
            <button className="primary" disabled={busy} onClick={issue}>
              Confirmar emissão/rotação
            </button>{' '}
            <button onClick={() => setConfirm(false)}>Cancelar</button>
          </div>
        ) : (
          <button onClick={() => setConfirm(true)} disabled={busy}>
            Emitir/rotacionar credencial
          </button>
        )}
        {secret && (
          <div className="secret-box">
            <strong>Token exibido uma vez</strong>
            <p>Copie para sua configuração privada. Não compartilhe nem salve no Git.</p>
            <code data-testid="issued-token">{secret.token}</code>
            <div className="row">
              <button
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(secret.token);
                    setMessage('Token copiado. Guarde no arquivo privado.');
                  } catch {
                    setMessage('Não foi possível copiar. Selecione o token manualmente.');
                  }
                }}
              >
                Copiar token
              </button>
              <button onClick={() => setSecret(null)}>Ocultei e guardei o token</button>
            </div>
          </div>
        )}
        <ResourceState resource={credentials} empty={!credentials.data?.items.length}>
          <ul className="credential-list">
            {credentials.data?.items.map((credential) => (
              <li key={credential.id}>
                <div>
                  <strong>
                    Versão {credential.version} · {credential.revokedAt ? 'Revogada' : 'Ativa'}
                  </strong>
                  <small>ID {credential.id}</small>
                  <Stamp value={credential.createdAt} />
                </div>
                {!credential.revokedAt && (
                  <button
                    disabled={busy}
                    onClick={() =>
                      execute(async () => {
                        await api(`/device-credentials/${credential.id}`, { method: 'DELETE' });
                        if (secret?.id === credential.id) setSecret(null);
                        credentials.refresh();
                        setMessage('Credencial revogada.');
                      })
                    }
                  >
                    Revogar credencial
                  </button>
                )}
              </li>
            ))}
          </ul>
        </ResourceState>
      </div>
      {message && <p role="status">{message}</p>}
    </section>
  );
}
