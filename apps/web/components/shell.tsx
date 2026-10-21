'use client';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useState } from 'react';
import type { ReactNode } from 'react';
import { useSession } from './session';
export function Shell({ children }: { children: ReactNode }) {
  const { user, logout } = useSession();
  const path = usePathname();
  const router = useRouter();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const nav = [
    ['/', '◫', 'Visão geral'],
    ['/incidentes', '◎', 'Incidentes'],
    ['/fontes', '▣', 'Fontes'],
    ['/avisos', '♧', 'Avisos locais'],
    ...(user?.role === 'OWNER' ? [['/configuracao', '⚙', 'Configuração']] : []),
  ];
  async function exit() {
    setBusy(true);
    try {
      await logout();
      router.replace('/login');
    } catch {
      setError('Não foi possível encerrar a sessão. Tente novamente.');
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link className="brand" href="/" aria-label="Radar, visão geral">
          <span className="brand-mark">
            r<span>◌</span>
          </span>
          <span>
            radar<small>ACONTECIMENTOS</small>
          </span>
        </Link>
        <p className="nav-caption">ESPAÇO DE OPERAÇÃO</p>
        <nav aria-label="Navegação principal">
          {nav.map(([href, icon, name]) => (
            <Link
              key={href}
              href={href!}
              aria-current={
                path === href || (href !== '/' && path.startsWith(href!)) ? 'page' : undefined
              }
            >
              <span aria-hidden="true">{icon}</span>
              {name}
            </Link>
          ))}
        </nav>
        <div className="sidebar-note">
          <span className="pulse-dot" />
          Bancada local
          <p>
            Observe os sinais.
            <br />
            Registre a revisão humana.
          </p>
        </div>
        <div className="account">
          <span className="avatar">{user?.role === 'OWNER' ? 'P' : 'O'}</span>
          <div>
            <strong>{user?.role === 'OWNER' ? 'Proprietário' : 'Operador'}</strong>
            <small>{user?.email}</small>
          </div>
        </div>
        <button className="logout" onClick={exit} disabled={busy}>
          Sair da conta ↗
        </button>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
      </aside>
      <div className="workspace">
        <div className="demo-bar">
          <span>
            <span className="tiny-square" /> MVP de demonstração
          </span>
          <span>Revisão humana · Sem envio externo</span>
        </div>
        <main className="content">{children}</main>
        <footer>
          Radar de Acontecimentos <span>Um alerta é uma suspeita a verificar.</span>
        </footer>
      </div>
    </div>
  );
}
