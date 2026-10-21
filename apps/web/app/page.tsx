export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center gap-6 p-8">
      <p className="text-sm font-semibold uppercase tracking-widest text-teal-800">
        MVP de bancada · Etapa 00
      </p>
      <h1 className="text-4xl font-semibold tracking-tight">Radar de Acontecimentos</h1>
      <p className="text-lg text-slate-700">
        Fundação do ambiente local. Login, incidentes, detector e câmera serão implementados nas
        próximas etapas.
      </p>
      <p className="text-slate-700">Nenhuma fonte de vídeo está em execução.</p>
      <a className="w-fit text-teal-900 underline underline-offset-4" href="/api/health/live">
        Consultar liveness da API
      </a>
    </main>
  );
}
