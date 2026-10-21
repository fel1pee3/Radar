import { Suspense } from 'react';
import { IncidentDetail } from '../../../../components/detail';
export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <Suspense fallback={<p>Carregando incidente…</p>}>
      <IncidentDetail id={id} />
    </Suspense>
  );
}
