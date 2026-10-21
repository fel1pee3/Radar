'use client';
import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { ReactNode, FormEvent } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { api, ApiError } from '../lib/api';
import type { User } from '../lib/models';
type Session = {
  user: User | null;
  ready: boolean;
  expired: boolean;
  login(email: string, password: string): Promise<void>;
  logout(): Promise<void>;
};
const Context = createContext<Session | null>(null);
export function SessionProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);
  const [expired, setExpired] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    api<User>('/auth/me', { signal: controller.signal, notifyAuth: false })
      .then((value) => {
        setUser(value);
        setReady(true);
      })
      .catch((error) => {
        if (!controller.signal.aborted) {
          setReady(true);
          if (!(error instanceof ApiError && error.status === 401)) setExpired(true);
        }
      });
    return () => controller.abort();
  }, []);
  useEffect(() => {
    const handler = () => setExpired(true);
    window.addEventListener('radar:unauthorized', handler);
    return () => window.removeEventListener('radar:unauthorized', handler);
  }, []);
  const login = useCallback(async (email: string, password: string) => {
    const value = await api<User>('/auth/login', {
      method: 'POST',
      body: { email, password },
      notifyAuth: false,
    });
    setUser(value);
    setExpired(false);
    setReady(true);
  }, []);
  const logout = useCallback(async () => {
    try {
      await api('/auth/logout', { method: 'POST' });
    } catch (error) {
      if (!(error instanceof ApiError && error.status === 401)) throw error;
    }
    setUser(null);
    setExpired(false);
  }, []);
  return (
    <Context.Provider value={{ user, ready, expired, login, logout }}>{children}</Context.Provider>
  );
}
export function useSession() {
  const value = useContext(Context);
  if (!value) throw new Error('Sessão indisponível.');
  return value;
}
export function LoginForm({ resume = false }: { resume?: boolean }) {
  const { login } = useSession();
  const router = useRouter();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError('');
    const form = event.currentTarget;
    const data = new FormData(form);
    try {
      await login(String(data.get('email')), String(data.get('password')));
      form.reset();
      if (!resume) {
        const next = new URLSearchParams(location.search).get('next');
        router.replace(next?.startsWith('/') && !next.startsWith('//') ? next : '/');
      }
    } catch (error) {
      setError(
        error instanceof ApiError && error.status === 401
          ? 'E-mail ou senha inválidos.'
          : error instanceof Error
            ? error.message
            : 'Não foi possível entrar.',
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="login-card">
      <div className="brand-mark">
        r<span>◌</span>
      </div>
      <p className="eyebrow">RADAR DE ACONTECIMENTOS</p>
      <h1>{resume ? 'Sua sessão expirou' : 'Acompanhe. Verifique. Registre.'}</h1>
      <p className="muted">
        {resume
          ? 'Seu rascunho permanece nesta aba. Entre com a mesma conta para continuar; outra conta inicia uma nova sessão.'
          : 'Entre para acompanhar as fontes e revisar os acontecimentos da bancada.'}
      </p>
      <form onSubmit={submit} className="stack">
        <label>
          E-mail
          <input name="email" type="email" autoComplete="username" required maxLength={254} />
        </label>
        <label>
          Senha
          <input
            name="password"
            type="password"
            autoComplete="current-password"
            required
            maxLength={128}
          />
        </label>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        <button className="primary" disabled={busy}>
          {busy ? 'Entrando…' : 'Entrar'}
        </button>
      </form>
      <p className="fine">MVP de demonstração · Processamento local</p>
    </div>
  );
}
export function SessionGate({ children }: { children: ReactNode }) {
  const { user, ready, expired } = useSession();
  const router = useRouter();
  const pathname = usePathname();
  useEffect(() => {
    if (ready && !user) router.replace(`/login?next=${encodeURIComponent(pathname)}`);
  }, [ready, user, pathname, router]);
  if (!ready || !user)
    return (
      <main className="center-state">
        <p role="status">Verificando sessão…</p>
      </main>
    );
  return (
    <>
      <div key={user.id} hidden={expired} inert={expired}>
        {children}
      </div>
      {expired && (
        <main className="login-screen">
          <LoginForm resume />
        </main>
      )}
    </>
  );
}
