import React, { useState } from 'react';
import type { Session } from '@/types';
import { Spinner } from '@/components/ui/Spinner';

interface SidebarProps {
  sessions: Session[];
  activeSessionId: string | null;
  loading: boolean;
  onSelectSession: (id: string) => void;
  onNewSession: () => void;
  onDeleteSession: (id: string) => void;
  chunkCount: number;
  onIngest: () => void;
  ingesting: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  activeSessionId,
  loading,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  chunkCount,
  onIngest,
  ingesting,
}) => {
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);

  const handleDelete = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (confirmDelete === id) {
      onDeleteSession(id);
      setConfirmDelete(null);
    } else {
      setConfirmDelete(id);
      setTimeout(() => setConfirmDelete(null), 3000);
    }
  };

  return (
    <aside
      style={{
        width: 'var(--sidebar-w)',
        minWidth: 'var(--sidebar-w)',
        background: 'var(--bg-surface)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        overflow: 'hidden',
      }}
      aria-label="Chat sessions sidebar"
    >
      {/* Header */}
      <div
        style={{
          padding: '16px 14px 12px',
          borderBottom: '1px solid var(--border-subtle)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <span style={{ fontSize: 20 }} aria-hidden="true">🎙️</span>
          <span style={{
            fontWeight: 700, fontSize: 14, letterSpacing: 0.2,
            background: 'linear-gradient(135deg, #a78bfa, #f472b6)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}>
            Lenny Growth
          </span>
        </div>
        <button
          onClick={onNewSession}
          style={{
            width: '100%',
            padding: '8px 12px',
            background: 'linear-gradient(135deg, #7c3aed, #ec4899)',
            color: '#fff',
            border: 'none',
            borderRadius: 'var(--radius-md)',
            cursor: 'pointer',
            fontWeight: 600,
            fontSize: 13,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
            transition: 'opacity 0.15s',
            boxShadow: '0 4px 15px rgba(124,58,237,0.4)',
          }}
          onMouseEnter={e => (e.currentTarget.style.opacity = '0.88')}
          onMouseLeave={e => (e.currentTarget.style.opacity = '1')}
          aria-label="Start new chat session"
        >
          <span aria-hidden="true">＋</span> New Chat
        </button>
      </div>

      {/* Session list */}
      <nav
        style={{ flex: 1, overflowY: 'auto', padding: '8px 6px' }}
        aria-label="Chat history"
      >
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: 24 }}>
            <Spinner size={18} />
          </div>
        ) : sessions.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', fontSize: 12, textAlign: 'center', padding: '20px 8px' }}>
            No sessions yet. Start a new chat.
          </p>
        ) : (
          sessions.map(session => (
            <div
              key={session.id}
              onClick={() => onSelectSession(session.id)}
              role="button"
              tabIndex={0}
              onKeyDown={e => e.key === 'Enter' && onSelectSession(session.id)}
              aria-current={activeSessionId === session.id ? 'page' : undefined}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '8px 10px',
                borderRadius: 'var(--radius-sm)',
                cursor: 'pointer',
                background: activeSessionId === session.id ? 'var(--accent-subtle)' : 'transparent',
                border: activeSessionId === session.id
                  ? '1px solid rgba(245,166,35,0.25)'
                  : '1px solid transparent',
                marginBottom: 2,
                transition: 'background 0.12s',
              }}
              onMouseEnter={e => {
                if (activeSessionId !== session.id)
                  (e.currentTarget as HTMLElement).style.background = 'var(--bg-hover)';
              }}
              onMouseLeave={e => {
                if (activeSessionId !== session.id)
                  (e.currentTarget as HTMLElement).style.background = 'transparent';
              }}
            >
              <div style={{ minWidth: 0, flex: 1 }}>
                <div
                  style={{
                    fontSize: 12.5,
                    fontWeight: 500,
                    color: 'var(--text-primary)',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {session.title || 'Untitled Chat'}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 1 }}>
                  {session.message_count} msg{session.message_count !== 1 ? 's' : ''}
                </div>
              </div>
              <button
                onClick={e => handleDelete(e, session.id)}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: confirmDelete === session.id ? 'var(--error)' : 'var(--text-muted)',
                  fontSize: 13,
                  padding: '2px 4px',
                  borderRadius: 4,
                  flexShrink: 0,
                  transition: 'color 0.15s',
                }}
                title={confirmDelete === session.id ? 'Click again to confirm delete' : 'Delete session'}
                aria-label={`Delete session: ${session.title || 'Untitled Chat'}`}
              >
                {confirmDelete === session.id ? '✓?' : '✕'}
              </button>
            </div>
          ))
        )}
      </nav>

      {/* Knowledge base status */}
      <div
        style={{
          padding: '12px 14px',
          borderTop: '1px solid var(--border-subtle)',
          background: 'var(--bg-elevated)',
        }}
      >
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 8 }}>
          <span style={{ color: chunkCount > 0 ? 'var(--success)' : 'var(--text-muted)' }}>●</span>
          {' '}Knowledge base: {chunkCount.toLocaleString()} chunks
        </div>
        <button
          onClick={onIngest}
          disabled={ingesting}
          style={{
            width: '100%',
            padding: '6px',
            background: 'var(--bg-hover)',
            color: 'var(--text-secondary)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-sm)',
            cursor: ingesting ? 'not-allowed' : 'pointer',
            fontSize: 11,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
            opacity: ingesting ? 0.7 : 1,
          }}
          aria-label="Re-index transcripts"
        >
          {ingesting ? <Spinner size={11} /> : '⟳'} Index Transcripts
        </button>
      </div>
    </aside>
  );
};
