import type { Page } from './models';
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
  ) {
    super(
      status === 401
        ? 'Sessão inválida ou expirada.'
        : status === 403
          ? 'Seu acesso não permite esta operação.'
          : status === 404
            ? 'Registro não encontrado.'
            : status === 409
              ? 'Este registro mudou. Confira os dados atuais antes de tentar novamente.'
              : status === 400 || status === 422
                ? 'Confira os campos e tente novamente.'
                : 'Não foi possível consultar a API. Verifique a conexão e os serviços locais.',
    );
  }
}
export async function api<T>(
  path: string,
  options: { method?: string; body?: unknown; signal?: AbortSignal; notifyAuth?: boolean } = {},
): Promise<T> {
  const response = await fetch(`/api${path}`, {
    method: options.method ?? 'GET',
    credentials: 'same-origin',
    cache: 'no-store',
    headers: options.body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    signal: options.signal
      ? AbortSignal.any([options.signal, AbortSignal.timeout(10000)])
      : AbortSignal.timeout(10000),
  });
  if (!response.ok) {
    if (response.status === 401 && options.notifyAuth !== false)
      window.dispatchEvent(new Event('radar:unauthorized'));
    const payload = (await response.json().catch(() => ({}))) as { code?: string };
    throw new ApiError(response.status, payload.code ?? 'HTTP_ERROR');
  }
  return response.status === 204 ? (undefined as T) : ((await response.json()) as T);
}
export async function allPages<T>(path: string, signal: AbortSignal): Promise<Page<T>> {
  const items: T[] = [];
  let cursor: string | null = null;
  do {
    const page: Page<T> = await api(
      `${path}${path.includes('?') ? '&' : '?'}limit=100${cursor ? `&cursor=${encodeURIComponent(cursor)}` : ''}`,
      { signal },
    );
    items.push(...page.items);
    cursor = page.nextCursor;
  } while (cursor);
  return { items, nextCursor: null };
}
