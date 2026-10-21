import { Notices } from '../../../components/views';
import { Suspense } from 'react';
export default function Page() {
  return (
    <Suspense fallback={<p>Carregando avisos…</p>}>
      <Notices />
    </Suspense>
  );
}
