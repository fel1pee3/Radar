'use client';
import { useEffect, useState, useCallback } from 'react';
import { api, allPages } from './api';
export function usePolling<T>(path: string, enabled = true, all = false) {
  const [state, setState] = useState<{ path: string; data?: T; error?: string; updatedAt?: Date }>({
    path,
  });
  const [revision, setRevision] = useState(0);
  const refresh = useCallback(() => setRevision((value) => value + 1), []);
  useEffect(() => {
    if (!enabled) return;
    let disposed = false,
      busy = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let controller: AbortController | undefined;
    const schedule = () => {
      if (!disposed && !document.hidden) timer = setTimeout(run, 2000);
    };
    async function run() {
      if (disposed || busy || document.hidden) return;
      busy = true;
      controller = new AbortController();
      try {
        const data = all
          ? ((await allPages(path, controller.signal)) as T)
          : await api<T>(path, { signal: controller.signal });
        if (!disposed && !controller.signal.aborted)
          setState({ path, data, updatedAt: new Date() });
      } catch (error) {
        if (!disposed && !controller.signal.aborted)
          setState((previous) => ({
            ...(previous.path === path ? previous : { path }),
            error: error instanceof Error ? error.message : 'Consulta indisponível.',
          }));
      } finally {
        busy = false;
        schedule();
      }
    }
    const visibility = () => {
      clearTimeout(timer);
      if (document.hidden) controller?.abort();
      else if (!busy) void run();
    };
    document.addEventListener('visibilitychange', visibility);
    void run();
    return () => {
      disposed = true;
      clearTimeout(timer);
      controller?.abort();
      document.removeEventListener('visibilitychange', visibility);
    };
  }, [path, enabled, all, revision]);
  return { ...(state.path === path ? state : { path }), refresh };
}
