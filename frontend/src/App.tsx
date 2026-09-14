import { useCallback, useEffect, useState } from 'react';
import type { Session } from '@/types';
import { api } from '@/api/client';
import { Sidebar } from '@/components/sidebar/Sidebar';
import { ChatWindow } from '@/components/chat/ChatWindow';
import { ModelBadge } from '@/components/ui/ModelBadge';
import '@/styles/globals.css';
import '@/styles/markdown.css';

export default function App() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [chunkCount, setChunkCount] = useState(0);
  const [ingesting, setIngesting] = useState(false);
  const [modelInfo, setModelInfo] = useState({ provider: 'ollama', model: 'llama3.2' });

  // Load sessions and system status on mount
  useEffect(() => {
    Promise.all([
      api.sessions.list().then(r => setSessions(r.sessions)),
      api.ingest.status().then(r => setChunkCount(r.chunk_count)).catch(() => {}),
      api.health.ready().then(r => {
        const [provider, ...modelParts] = r.active_model.split('/');
        setModelInfo({ provider, model: modelParts.join('/') });
      }).catch(() => {}),
    ]).finally(() => setLoadingSessions(false));
  }, []);

  const handleNewSession = useCallback(async () => {
    try {
      const session = await api.sessions.create();
      setSessions(prev => [session, ...prev]);
      setActiveSessionId(session.id);
    } catch (err) {
      console.error('Failed to create session:', err);
    }
  }, []);

  const handleSelectSession = useCallback((id: string) => {
    setActiveSessionId(id);
  }, []);

  const handleDeleteSession = useCallback(async (id: string) => {
    try {
      await api.sessions.delete(id);
      setSessions(prev => prev.filter(s => s.id !== id));
      if (activeSessionId === id) setActiveSessionId(null);
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
  }, [activeSessionId]);

  const handleIngest = useCallback(async () => {
    setIngesting(true);
    try {
      const result = await api.ingest.run();
      if ('chunks_indexed' in result) setChunkCount(result.chunks_indexed);
    } catch (err) {
      console.error('Ingestion failed:', err);
    } finally {
      setIngesting(false);
    }
  }, []);

  // Update session list when message count changes (refresh after chat)
  const refreshSessions = useCallback(async () => {
    try {
      const r = await api.sessions.list();
      setSessions(r.sessions);
    } catch (_) {}
  }, []);

  useEffect(() => {
    if (activeSessionId) {
      const timer = setTimeout(refreshSessions, 2000);
      return () => clearTimeout(timer);
    }
  }, [activeSessionId, refreshSessions]);

  const modelLabel = `${modelInfo.provider}/${modelInfo.model}`;

  return (
    <div
      style={{
        display: 'flex',
        height: '100vh',
        overflow: 'hidden',
        background: 'var(--bg-base)',
      }}
    >
      {/* Sidebar */}
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        loading={loadingSessions}
        onSelectSession={handleSelectSession}
        onNewSession={handleNewSession}
        onDeleteSession={handleDeleteSession}
        chunkCount={chunkCount}
        onIngest={handleIngest}
        ingesting={ingesting}
      />

      {/* Main area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {/* Header */}
        <header
          style={{
            height: 'var(--header-h)',
            borderBottom: '1px solid var(--border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 20px',
            background: 'var(--bg-surface)',
            flexShrink: 0,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <h1
              style={{
                fontSize: 15,
                fontWeight: 700,
                color: 'var(--text-primary)',
                letterSpacing: 0.2,
              }}
            >
              Lenny Growth Assistant
            </h1>
            {activeSessionId && (
              <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                · {sessions.find(s => s.id === activeSessionId)?.title ?? 'Untitled'}
              </span>
            )}
          </div>
          <ModelBadge provider={modelInfo.provider} model={modelInfo.model} />
        </header>

        {/* Chat window fills remaining height */}
        <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          <ChatWindow sessionId={activeSessionId} modelLabel={modelLabel} />
        </div>
      </div>
    </div>
  );
}
