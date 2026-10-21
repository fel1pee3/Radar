import { Suspense } from 'react';
import { Incidents } from '../../../components/views';
export default function Page() {
  return (
    <Suspense fallback={<p>Carregando lista…</p>}>
      <Incidents />
    </Suspense>
  );
}
