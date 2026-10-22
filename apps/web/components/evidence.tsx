'use client';
import { useState, useEffect, useRef } from 'react';
import { api, ApiError } from '../lib/api';
import { useSession } from './session';
import type { Incident, Camera } from '../lib/models';

const states: Record<string, string> = {
  DISABLED: 'Imagem desabilitada para este evento.',
  AWAITING: 'Imagem ausente ou aguardando envio do worker.',
  AVAILABLE: 'Imagem disponível.',
  DELETED: 'Imagem excluída.',
  EXPIRED: 'Imagem expirada.',
};
export function Snapshot({ incident, onChange }: { incident: Incident; onChange(): void }) {
  const { user, expired } = useSession();
  const [url, setUrl] = useState<string | null>(null);
  const [message, setMessage] = useState('');
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const controller = useRef<AbortController | null>(null);
  const currentUrl = useRef<string | null>(null);
  const [deadlinePassed, setDeadlinePassed] = useState(false);
  const snapshotState = incident.snapshot?.state ?? 'DISABLED';
  const state =
    deadlinePassed && !['DELETED', 'DISABLED'].includes(snapshotState) ? 'EXPIRED' : snapshotState;
  useEffect(() => {
    const expiresAt = incident.snapshot?.expiresAt;
    if (!expiresAt) return;
    const delay = Date.parse(expiresAt) - Date.now();
    if (!Number.isFinite(delay)) return;
    const timer = setTimeout(
      () => {
        controller.current?.abort();
        if (currentUrl.current) URL.revokeObjectURL(currentUrl.current);
        currentUrl.current = null;
        setUrl(null);
        setDeadlinePassed(true);
      },
      Math.max(0, delay),
    );
    return () => clearTimeout(timer);
  }, [incident.snapshot?.expiresAt]);
  useEffect(
    () => () => {
      controller.current?.abort();
      if (currentUrl.current) URL.revokeObjectURL(currentUrl.current);
    },
    [],
  );
  useEffect(() => {
    if (expired || state !== 'AVAILABLE') {
      controller.current?.abort();
      if (currentUrl.current) URL.revokeObjectURL(currentUrl.current);
      currentUrl.current = null;
    }
  }, [expired, state]);
  async function load() {
    if (busy || expired) return;
    setBusy(true);
    setMessage('');
    const c = new AbortController();
    controller.current = c;
    try {
      const r = await fetch(`/api/incidents/${incident.id}/snapshot`, {
        credentials: 'same-origin',
        cache: 'no-store',
        signal: AbortSignal.any([c.signal, AbortSignal.timeout(10000)]),
      });
      if (r.status === 401) window.dispatchEvent(new Event('radar:unauthorized'));
      if (r.status === 404 || r.status === 410) {
        setMessage(
          r.status === 410 ? 'Imagem expirada ou excluída.' : 'Imagem ainda não disponível.',
        );
        onChange();
        return;
      }
      if (!r.ok) throw new Error();
      const blob = await r.blob();
      if (blob.type !== 'image/jpeg' || blob.size > 2 * 1024 * 1024) throw new Error();
      if (c.signal.aborted) return;
      if (currentUrl.current) URL.revokeObjectURL(currentUrl.current);
      currentUrl.current = URL.createObjectURL(blob);
      setUrl(currentUrl.current);
    } catch {
      if (!c.signal.aborted)
        setMessage(
          'Leitura temporariamente indisponível. Tente novamente; isso não significa que a imagem foi excluída.',
        );
    } finally {
      setBusy(false);
    }
  }
  async function remove() {
    setBusy(true);
    setMessage('');
    try {
      await api(`/incidents/${incident.id}/snapshot`, { method: 'DELETE' });
      if (currentUrl.current) URL.revokeObjectURL(currentUrl.current);
      currentUrl.current = null;
      setUrl(null);
      setConfirm(false);
      setMessage('Imagem excluída. O incidente continua disponível para revisão.');
      onChange();
    } catch (e) {
      setMessage(
        e instanceof ApiError
          ? e.message
          : 'Exclusão não confirmada. Recarregue para conferir o estado.',
      );
      onChange();
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="stack" aria-label="Imagem de evidência">
      <p>{states[state] ?? 'Estado da evidência indisponível.'}</p>
      {state === 'AVAILABLE' && !expired && (
        <>
          <button onClick={load} disabled={busy}>
            Abrir imagem
          </button>
          {url && (
            <div>
              {/* Authenticated blob; never sent to the Next image optimizer. */}
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={url}
                alt="Evidência pontual do evento"
                style={{ maxWidth: '100%', height: 'auto' }}
              />
            </div>
          )}
        </>
      )}
      {user?.role === 'OWNER' && ['AVAILABLE', 'AWAITING'].includes(state) && !expired && (
        <>
          <button onClick={() => setConfirm(true)} disabled={busy}>
            Excluir imagem
          </button>
          {confirm && (
            <div role="group" aria-label="Confirmar exclusão">
              <p>
                A imagem será removida e reenvios não poderão restaurá-la. Esta ação não encerra nem
                descarta o incidente.
              </p>
              <button onClick={remove} disabled={busy}>
                Confirmar exclusão da imagem
              </button>
              <button onClick={() => setConfirm(false)} disabled={busy}>
                Cancelar exclusão
              </button>
            </div>
          )}
        </>
      )}
      {message && <p role="status">{message}</p>}
    </div>
  );
}
export function EvidencePreference({ camera, onSaved }: { camera: Camera; onSaved(): void }) {
  const [mode, setMode] = useState(camera.evidenceMode ?? 'skeleton');
  const [authorized, setAuthorized] = useState(false);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  async function save() {
    setBusy(true);
    setMessage('');
    try {
      await api(`/cameras/${camera.id}/evidence-preference`, {
        method: 'PATCH',
        body: { mode, authorized: mode === 'snapshot' && authorized },
      });
      setMessage('Preferência registrada. A configuração do worker também precisa ser compatível.');
      setAuthorized(false);
      onSaved();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : 'Não foi possível salvar.');
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="stack">
      <h4>Evidência dos próximos eventos</h4>
      <p>
        Preferência atual: {camera.evidenceMode ?? 'skeleton'}. Não altera evidências já recebidas.
      </p>
      <label>
        Modo de evidência
        <select
          value={mode}
          onChange={(e) => {
            setMode(e.target.value as typeof mode);
            setAuthorized(false);
          }}
        >
          <option value="none">Somente sinais e metadados</option>
          <option value="skeleton">Esqueleto, sem imagem</option>
          <option value="snapshot">Esqueleto e imagem pontual</option>
        </select>
      </label>
      {mode === 'snapshot' && (
        <label>
          <input
            type="checkbox"
            checked={authorized}
            onChange={(e) => setAuthorized(e.target.checked)}
          />
          Confirmo que a captura de imagem desta fonte está autorizada.
        </label>
      )}
      <button disabled={busy || (mode === 'snapshot' && !authorized)} onClick={save}>
        Salvar preferência de evidência
      </button>
      {message && <p role="status">{message}</p>}
    </div>
  );
}

export function RetentionPreference() {
  const { expired } = useSession();
  const [enabled, setEnabled] = useState<boolean | null>(null);
  const [confirm, setConfirm] = useState(false);
  const [message, setMessage] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    api<{ enabled: boolean }>('/retention-preference', { signal: controller.signal })
      .then((r) => {
        if (!controller.signal.aborted) setEnabled(r.enabled);
      })
      .catch(() => {
        if (!controller.signal.aborted) setMessage('Preferência de retenção indisponível.');
      });
    return () => controller.abort();
  }, []);
  async function save() {
    try {
      const r = await api<{ enabled: boolean }>('/retention-preference', {
        method: 'PATCH',
        body: { enabled: !enabled },
      });
      setEnabled(r.enabled);
      setConfirm(false);
      setMessage(
        'Preferência de purga registrada. O agendamento de limpeza é configurado separadamente.',
      );
    } catch (e) {
      setMessage(e instanceof Error ? e.message : 'Não foi possível salvar.');
    }
  }
  return (
    <section className="panel stack">
      <h2>Retenção de metadados</h2>
      <p>
        Purga de incidentes e auditoria com mais de 30 dias:{' '}
        {enabled === null ? 'consultando' : enabled ? 'habilitada' : 'desabilitada'}.
      </p>
      <p>
        Imagens e poses têm prazos menores. Excluir metadados preserva recibos mínimos de
        deduplicação por 90 dias.
      </p>
      <button disabled={enabled === null || expired} onClick={() => setConfirm(true)}>
        {enabled ? 'Desabilitar purga de metadados' : 'Configurar purga de metadados'}
      </button>
      {confirm && (
        <div role="group" aria-label="Confirmar preferência de retenção">
          <p>
            {enabled
              ? 'Desabilitar futuras purgas?'
              : 'Autoriza remover incidentes e auditoria com mais de 30 dias quando a rotina de limpeza executar? A remoção é definitiva no banco atual.'}
          </p>
          <button onClick={save} disabled={expired}>
            Confirmar preferência de retenção
          </button>
          <button onClick={() => setConfirm(false)}>Cancelar</button>
        </div>
      )}
      {message && <p role="status">{message}</p>}
    </section>
  );
}
