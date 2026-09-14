/**
 * Typed API client — thin wrappers over fetch.
 * Base URL proxied via Vite dev server → /api/v1
 */
import type {
  Artifact,
  ChatResponse,
  Message,
  Session,
} from '@/types';

const BASE = '/api/v1';

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(body.error ?? body.detail ?? `HTTP ${res.status}`);
  }

  return res.json() as Promise<T>;
}

// ── Sessions ──────────────────────────────────────────────────────────────────

export const api = {
  sessions: {
    list: () =>
      request<{ sessions: Session[]; total: number }>('/sessions'),

    create: (title?: string) =>
      request<Session>('/sessions', {
        method: 'POST',
        body: JSON.stringify({ title: title ?? null }),
      }),

    get: (id: string) => request<Session>(`/sessions/${id}`),

    delete: (id: string) =>
      fetch(`${BASE}/sessions/${id}`, { method: 'DELETE' }),
  },

  // ── Chat ────────────────────────────────────────────────────────────────────

  chat: {
    send: (sessionId: string, message: string, skill?: string) =>
      request<ChatResponse>('/chat', {
        method: 'POST',
        body: JSON.stringify({
          session_id: sessionId,
          message,
          skill: skill === 'rag' ? null : skill ?? null,
        }),
      }),

    messages: (sessionId: string) =>
      request<Message[]>(`/chat/${sessionId}/messages`),
  },

  // ── Artifacts ───────────────────────────────────────────────────────────────

  artifacts: {
    generate: (
      sessionId: string,
      artifactType: 'markdown' | 'html',
      title: string,
      instructions: string
    ) =>
      request<Artifact>('/artifacts', {
        method: 'POST',
        body: JSON.stringify({
          session_id: sessionId,
          artifact_type: artifactType,
          title,
          instructions,
        }),
      }),

    get: (id: string) => request<Artifact>(`/artifacts/${id}`),

    listForSession: (sessionId: string) =>
      request<Artifact[]>(`/artifacts/session/${sessionId}`),
  },

  // ── Ingestion ────────────────────────────────────────────────────────────────

  ingest: {
    run: () => request<{ status: string; chunks_indexed: number }>('/ingest', { method: 'POST' }),
    status: () => request<{ chunk_count: number; collection: string }>('/ingest/status'),
  },

  // ── Health ───────────────────────────────────────────────────────────────────

  health: {
    ready: () =>
      request<{
        status: string;
        llm_provider: string;
        active_model: string;
        database: string;
      }>('/ready'),
  },
};
