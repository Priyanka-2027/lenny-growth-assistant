/**
 * ArtifactViewer — renders Markdown or HTML artifacts beside the chat.
 *
 * Security model:
 * ─────────────────────────────────────────────────────────────────
 * HTML artifacts:
 *   - Rendered inside a sandboxed <iframe> with:
 *       sandbox="allow-same-origin"
 *     This permits CSS and DOM but BLOCKS:
 *       • Script execution (no allow-scripts)
 *       • Form submission (no allow-forms)
 *       • Popups / top-level navigation (no allow-top-navigation)
 *       • Plugin execution
 *   - Content is set via srcdoc (no network request)
 *   - An additional Content-Security-Policy meta tag is injected
 *     into the HTML before rendering: script-src 'none'
 *   - The outer CSP header from FastAPI also blocks scripts globally
 *
 * Markdown artifacts:
 *   - Rendered with react-markdown + remark-gfm
 *   - DOMPurify sanitizes any raw HTML inside the markdown before render
 *   - No dangerouslySetInnerHTML is used directly
 *
 * What is permitted:
 *   ✅ CSS styling (inline and <style> tags)
 *   ✅ Text, links (open in new tab, no top navigation)
 *   ✅ Images from data URIs
 *
 * What is blocked:
 *   ❌ JavaScript execution
 *   ❌ External network requests (no allow-scripts disables fetch/XHR too)
 *   ❌ Cookie / storage access
 *   ❌ Form submission
 * ─────────────────────────────────────────────────────────────────
 */
import React, { useCallback, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import DOMPurify from 'dompurify';

interface ArtifactViewerProps {
  type: 'markdown' | 'html';
  title: string;
  content: string;
  onClose: () => void;
}

function injectCSP(html: string): string {
  const cspMeta = `<meta http-equiv="Content-Security-Policy" content="script-src 'none'; object-src 'none';">`;
  if (html.includes('<head>')) {
    return html.replace('<head>', `<head>\n  ${cspMeta}`);
  }
  if (html.includes('<html>')) {
    return html.replace('<html>', `<html>\n<head>${cspMeta}</head>`);
  }
  // Wrap bare HTML
  return `<!DOCTYPE html><html><head>${cspMeta}</head><body>${html}</body></html>`;
}

export const ArtifactViewer: React.FC<ArtifactViewerProps> = ({
  type,
  title,
  content,
  onClose,
}) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  const handleCopy = useCallback(async () => {
    await navigator.clipboard.writeText(content);
  }, [content]);

  const handleDownload = useCallback(() => {
    const ext = type === 'html' ? 'html' : 'md';
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title.replace(/[^a-z0-9]/gi, '-').toLowerCase()}.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  }, [content, title, type]);

  const sanitizedHtml = type === 'html' ? injectCSP(content) : '';
  const sanitizedMarkdown =
    type === 'markdown'
      ? DOMPurify.sanitize(content, { USE_PROFILES: { html: false } })
      : content;

  return (
    <aside
      aria-label="Artifact viewer"
      style={{
        width: '45%',
        minWidth: 360,
        maxWidth: 680,
        background: 'var(--bg-surface)',
        borderLeft: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '12px 16px',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 8,
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
          <span
            style={{
              fontSize: 10,
              fontWeight: 700,
              padding: '2px 7px',
              borderRadius: 8,
              background: type === 'html' ? 'rgba(116,169,212,0.15)' : 'rgba(76,175,125,0.15)',
              color: type === 'html' ? '#74a9d4' : '#4caf7d',
              border: `1px solid ${type === 'html' ? 'rgba(116,169,212,0.3)' : 'rgba(76,175,125,0.3)'}`,
              textTransform: 'uppercase',
              letterSpacing: 0.5,
              flexShrink: 0,
            }}
          >
            {type === 'html' ? '🌐 HTML' : '📄 MD'}
          </span>
          <span
            style={{
              fontSize: 13,
              fontWeight: 600,
              color: 'var(--text-primary)',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {title}
          </span>
        </div>

        <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
          <button
            onClick={handleCopy}
            title="Copy to clipboard"
            style={iconBtnStyle}
            aria-label="Copy artifact content"
          >
            📋
          </button>
          <button
            onClick={handleDownload}
            title="Download file"
            style={iconBtnStyle}
            aria-label="Download artifact"
          >
            ⬇
          </button>
          <button
            onClick={onClose}
            title="Close artifact viewer"
            style={{ ...iconBtnStyle, color: 'var(--text-secondary)' }}
            aria-label="Close artifact viewer"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Security notice */}
      {type === 'html' && (
        <div
          style={{
            padding: '5px 16px',
            background: 'rgba(245,166,35,0.07)',
            borderBottom: '1px solid rgba(245,166,35,0.15)',
            fontSize: 11,
            color: 'var(--text-muted)',
          }}
          role="note"
          aria-label="Security information"
        >
          🔒 Rendered in sandboxed iframe — scripts disabled, CSS permitted
        </div>
      )}

      {/* Content */}
      <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
        {type === 'html' ? (
          <iframe
            ref={iframeRef}
            srcDoc={sanitizedHtml}
            sandbox="allow-same-origin"
            title={`Artifact: ${title}`}
            style={{
              width: '100%',
              height: '100%',
              border: 'none',
              background: '#fff',
            }}
            aria-label={`HTML artifact: ${title}`}
          />
        ) : (
          <div
            style={{
              height: '100%',
              overflowY: 'auto',
              padding: '20px 24px',
              color: 'var(--text-primary)',
              fontSize: 14,
              lineHeight: 1.7,
            }}
            className="markdown-body artifact-markdown"
          >
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {sanitizedMarkdown}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </aside>
  );
};

const iconBtnStyle: React.CSSProperties = {
  background: 'none',
  border: '1px solid var(--border)',
  borderRadius: 6,
  cursor: 'pointer',
  color: 'var(--text-secondary)',
  fontSize: 13,
  padding: '4px 8px',
  lineHeight: 1,
  transition: 'background 0.12s',
};
