import React, { useState } from 'react';
import type { Source } from '@/types';

interface SourceListProps {
  sources: Source[];
}

export const SourceList: React.FC<SourceListProps> = ({ sources }) => {
  const [expanded, setExpanded] = useState(false);

  if (!sources.length) return null;

  return (
    <div style={{ marginTop: 10 }}>
      <button
        onClick={() => setExpanded(e => !e)}
        style={{
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          color: 'var(--text-muted)',
          fontSize: 11,
          display: 'flex',
          alignItems: 'center',
          gap: 5,
          padding: 0,
        }}
        aria-expanded={expanded}
        aria-controls="source-list"
      >
        <span aria-hidden="true">{expanded ? '▾' : '▸'}</span>
        {sources.length} source{sources.length !== 1 ? 's' : ''}
      </button>

      {expanded && (
        <ul
          id="source-list"
          style={{
            marginTop: 8,
            listStyle: 'none',
            display: 'flex',
            flexDirection: 'column',
            gap: 6,
          }}
        >
          {sources.map((src, i) => (
            <li
              key={i}
              style={{
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-sm)',
                padding: '8px 10px',
                fontSize: 11.5,
              }}
            >
              <div style={{ fontWeight: 600, color: 'var(--accent)', marginBottom: 2 }}>
                {src.episode || src.title}
              </div>
              {src.relevance_score != null && (
                <div style={{ color: 'var(--text-muted)', marginBottom: 4 }}>
                  Relevance: {(src.relevance_score * 100).toFixed(0)}%
                </div>
              )}
              {src.excerpt && (
                <div
                  style={{
                    color: 'var(--text-secondary)',
                    fontStyle: 'italic',
                    borderLeft: '2px solid var(--border)',
                    paddingLeft: 8,
                    lineHeight: 1.5,
                  }}
                >
                  "{src.excerpt}"
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
