// ── Domain types mirroring backend Pydantic schemas ──────────────────────────

export interface Session {
  id: string;
  title: string | null;
  user_metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface Source {
  title: string;
  episode: string | null;
  chunk_index: number | null;
  relevance_score: number | null;
  excerpt: string | null;
}

export interface ArtifactPayload {
  artifact_type: 'markdown' | 'html';
  title: string;
  content: string;
}

export interface Message {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  sources: Source[];
  skill_used: string | null;
  model_used: string | null;
  created_at: string;
}

export interface ChatResponse {
  message: Message;
  sources: Source[];
  artifact: ArtifactPayload | null;
}

export interface Artifact {
  id: string;
  session_id: string;
  artifact_type: 'markdown' | 'html';
  title: string;
  content: string;
  created_at: string;
}

// ── UI-only types ─────────────────────────────────────────────────────────────

export type Skill = 'rag' | 'ship30' | 'artifact_md' | 'artifact_html';

export interface UIMessage extends Message {
  isStreaming?: boolean;
  error?: string;
}
