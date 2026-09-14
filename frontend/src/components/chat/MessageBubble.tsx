import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { UIMessage } from '@/types';
import { SourceList } from './SourceList';
import { Spinner } from '@/components/ui/Spinner';

interface MessageBubbleProps {
  message: UIMessage;
  onOpenArtifact?: (content: string, type: 'markdown' | 'html', title: string) => void;
}

const SKILL_LABELS: Record<string, string> = {
  ship30: '✍️ Ship 30 Essay',
  artifact_md: '📄 Markdown',
  artifact_html: '🌐 HTML',
};

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const isStreaming = message.isStreaming;

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        marginBottom: 16,
        gap: 10,
        alignItems: 'flex-start',
      }}
    >
      {/* Avatar */}
      {!isUser && (
        <div
          aria-hidden="true"
          style={{
            width: 32,
            height: 32,
            borderRadius: '50%',
            background: 'var(--accent-subtle)',
            border: '1px solid rgba(245,166,35,0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 15,
            flexShrink: 0,
            marginTop: 2,
          }}
        >
          🎙️
        </div>
      )}

      <div style={{ maxWidth: '75%', minWidth: 0 }}>
        {/* Skill badge */}
        {message.skill_used && SKILL_LABELS[message.skill_used] && (
          <div style={{ marginBottom: 4 }}>
            <span
              style={{
                fontSize: 10,
                fontWeight: 600,
                color: 'var(--accent)',
                background: 'var(--accent-subtle)',
                border: '1px solid rgba(245,166,35,0.2)',
                borderRadius: 10,
                padding: '2px 8px',
                letterSpacing: 0.3,
              }}
            >
              {SKILL_LABELS[message.skill_used]}
            </span>
          </div>
        )}

        {/* Bubble */}
        <div
          style={{
            padding: '10px 14px',
            borderRadius: isUser
              ? 'var(--radius-lg) var(--radius-lg) var(--radius-sm) var(--radius-lg)'
              : 'var(--radius-lg) var(--radius-lg) var(--radius-lg) var(--radius-sm)',
            background: isUser ? 'var(--user-bubble)' : 'var(--asst-bubble)',
            border: `1px solid ${isUser ? 'var(--user-border)' : 'var(--border)'}`,
            color: 'var(--text-primary)',
            fontSize: 14,
            lineHeight: 1.65,
          }}
        >
          {isStreaming ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Spinner size={14} />
              <span style={{ color: 'var(--text-secondary)', fontSize: 13 }}>Thinking…</span>
            </div>
          ) : message.error ? (
            <span style={{ color: 'var(--error)' }}>⚠ {message.error}</span>
          ) : isUser ? (
            <span style={{ whiteSpace: 'pre-wrap' }}>{message.content}</span>
          ) : (
            <div className="markdown-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Sources */}
        {!isUser && !isStreaming && message.sources?.length > 0 && (
          <SourceList sources={message.sources} />
        )}

        {/* Model used */}
        {!isUser && !isStreaming && message.model_used && (
          <div style={{ marginTop: 4, fontSize: 10, color: 'var(--text-muted)' }}>
            via {message.model_used}
          </div>
        )}
      </div>

      {/* User avatar */}
      {isUser && (
        <div
          aria-hidden="true"
          style={{
            width: 32,
            height: 32,
            borderRadius: '50%',
            background: 'var(--user-bubble)',
            border: '1px solid var(--user-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 13,
            flexShrink: 0,
            marginTop: 2,
          }}
        >
          👤
        </div>
      )}
    </div>
  );
};
