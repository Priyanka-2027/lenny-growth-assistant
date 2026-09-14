import React, { useEffect, useRef, useState } from 'react';
import type { ArtifactPayload, Skill, UIMessage } from '@/types';
import { MessageBubble } from './MessageBubble';
import { SkillSelector } from './SkillSelector';
import { Spinner } from '@/components/ui/Spinner';
import { ArtifactViewer } from '@/components/artifact/ArtifactViewer';
import { api } from '@/api/client';

interface ChatWindowProps {
  sessionId: string | null;
  modelLabel: string;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({ sessionId, modelLabel }) => {
  const [messages, setMessages] = useState<UIMessage[]>([]);
  const [input, setInput] = useState('');
  const [skill, setSkill] = useState<Skill>('rag');
  const [sending, setSending] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [artifact, setArtifact] = useState<ArtifactPayload | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Load message history when session changes
  useEffect(() => {
    if (!sessionId) {
      setMessages([]);
      return;
    }
    setLoadingHistory(true);
    api.chat
      .messages(sessionId)
      .then(msgs =>
        setMessages(
          msgs.map(m => ({
            ...m,
            sources: m.sources ?? [],
            skill_used: m.skill_used ?? null,
            model_used: m.model_used ?? null,
          }))
        )
      )
      .catch(console.error)
      .finally(() => setLoadingHistory(false));
  }, [sessionId]);

  // Scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!sessionId || !input.trim() || sending) return;
    const userText = input.trim();
    setInput('');
    setSending(true);

    const userMsg: UIMessage = {
      id: crypto.randomUUID(),
      session_id: sessionId,
      role: 'user',
      content: userText,
      sources: [],
      skill_used: null,
      model_used: null,
      created_at: new Date().toISOString(),
    };

    const placeholder: UIMessage = {
      id: crypto.randomUUID(),
      session_id: sessionId,
      role: 'assistant',
      content: '',
      sources: [],
      skill_used: skill === 'rag' ? null : skill,
      model_used: null,
      created_at: new Date().toISOString(),
      isStreaming: true,
    };

    setMessages(prev => [...prev, userMsg, placeholder]);

    try {
      const result = await api.chat.send(sessionId, userText, skill);
      setMessages(prev =>
        prev.map(m =>
          m.id === placeholder.id
            ? {
                ...result.message,
                sources: result.sources ?? [],
                skill_used: result.message.skill_used,
                model_used: result.message.model_used,
                isStreaming: false,
              }
            : m
        )
      );
      if (result.artifact) setArtifact(result.artifact);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : 'An error occurred.';
      setMessages(prev =>
        prev.map(m =>
          m.id === placeholder.id
            ? { ...m, isStreaming: false, error: errorMsg }
            : m
        )
      );
    } finally {
      setSending(false);
      textareaRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Auto-resize textarea
  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
  };

  if (!sessionId) {
    return (
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--text-muted)',
          gap: 12,
        }}
      >
        <span style={{ fontSize: 48 }} aria-hidden="true">🎙️</span>
        <h2 style={{ color: 'var(--text-secondary)', fontWeight: 500, fontSize: 18 }}>
          Lenny Growth Assistant
        </h2>
        <p style={{ fontSize: 13, maxWidth: 340, textAlign: 'center', lineHeight: 1.6 }}>
          Start a new chat to ask product and growth questions grounded in Lenny's podcast transcripts.
        </p>
      </div>
    );
  }

  return (
    <div style={{ flex: 1, display: 'flex', minWidth: 0, overflow: 'hidden' }}>
      {/* Chat panel */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          minWidth: 0,
          overflow: 'hidden',
        }}
      >
        {/* Messages */}
        <main
          role="log"
          aria-live="polite"
          aria-label="Chat messages"
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '24px 28px',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {loadingHistory ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: 32 }}>
              <Spinner />
            </div>
          ) : messages.length === 0 ? (
            <div
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 16,
                color: 'var(--text-muted)',
              }}
            >
              <span style={{ fontSize: 36 }} aria-hidden="true">💬</span>
              <p style={{ fontSize: 13, textAlign: 'center', maxWidth: 320 }}>
                Ask a product or growth question — answers are grounded in Lenny's transcript library.
              </p>
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: 8,
                  justifyContent: 'center',
                  maxWidth: 480,
                }}
              >
                {EXAMPLE_QUESTIONS.map(q => (
                  <button
                    key={q}
                    onClick={() => { setInput(q); textareaRef.current?.focus(); }}
                    style={{
                      background: 'var(--bg-elevated)',
                      border: '1px solid var(--border)',
                      borderRadius: 8,
                      color: 'var(--text-secondary)',
                      cursor: 'pointer',
                      fontSize: 12,
                      padding: '6px 12px',
                      textAlign: 'left',
                    }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map(msg => (
              <MessageBubble
                key={msg.id}
                message={msg}
                onOpenArtifact={(content, type, title) =>
                  setArtifact({ content, artifact_type: type, title })
                }
              />
            ))
          )}
          <div ref={bottomRef} aria-hidden="true" />
        </main>

        {/* Input area */}
        <div
          style={{
            padding: '12px 20px 16px',
            borderTop: '1px solid var(--border)',
            background: 'var(--bg-surface)',
            flexShrink: 0,
          }}
        >
          {/* Skill selector */}
          <div style={{ marginBottom: 10 }}>
            <SkillSelector selected={skill} onChange={setSkill} />
          </div>

          <div
            style={{
              display: 'flex',
              gap: 10,
              alignItems: 'flex-end',
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-lg)',
              padding: '10px 12px',
            }}
          >
            <label htmlFor="chat-input" className="sr-only">
              Message
            </label>
            <textarea
              id="chat-input"
              ref={textareaRef}
              value={input}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              placeholder={PLACEHOLDERS[skill]}
              rows={1}
              disabled={sending}
              aria-label="Chat message input"
              style={{
                flex: 1,
                background: 'none',
                border: 'none',
                outline: 'none',
                color: 'var(--text-primary)',
                fontSize: 14,
                resize: 'none',
                lineHeight: 1.6,
                minHeight: 24,
                maxHeight: 160,
                fontFamily: 'var(--font-sans)',
                overflowY: 'auto',
              }}
            />
            <button
              onClick={handleSend}
              disabled={sending || !input.trim()}
              aria-label="Send message"
              style={{
                background: sending || !input.trim() ? 'var(--bg-hover)' : 'var(--accent)',
                border: 'none',
                borderRadius: 8,
                cursor: sending || !input.trim() ? 'not-allowed' : 'pointer',
                color: sending || !input.trim() ? 'var(--text-muted)' : '#000',
                width: 36,
                height: 36,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                transition: 'background 0.15s',
                fontSize: 16,
              }}
            >
              {sending ? <Spinner size={14} color="#fff" /> : '↑'}
            </button>
          </div>

          <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6, textAlign: 'center' }}>
            {modelLabel} · Shift+Enter for new line
          </p>
        </div>
      </div>

      {/* Artifact viewer panel */}
      {artifact && (
        <ArtifactViewer
          type={artifact.artifact_type}
          title={artifact.title}
          content={artifact.content}
          onClose={() => setArtifact(null)}
        />
      )}
    </div>
  );
};

const PLACEHOLDERS: Record<Skill, string> = {
  rag: 'Ask a product or growth question…',
  ship30: 'Enter a topic for your Ship 30 essay…',
  artifact_md: 'Describe the Markdown document to generate…',
  artifact_html: 'Describe the HTML page to generate…',
};

const EXAMPLE_QUESTIONS = [
  'How do you find product-market fit?',
  'What are growth loops vs funnels?',
  'How should I improve user activation?',
  'What is the Sean Ellis test?',
];
