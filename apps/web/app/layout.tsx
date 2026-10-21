import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import './globals.css';
import { SessionProvider } from '../components/session';

export const metadata: Metadata = {
  title: 'Radar de Acontecimentos',
  description: 'MVP de demonstração local: acompanhamento e revisão humana de acontecimentos.',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  );
}
