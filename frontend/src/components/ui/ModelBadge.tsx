import React from 'react';

interface ModelBadgeProps {
  provider: string;
  model: string;
}

const PROVIDER_COLORS: Record<string, string> = {
  anthropic: '#d4a574',
  ollama:    '#7eb8a8',
  openai:    '#74a9d4',
};

export const ModelBadge: React.FC<ModelBadgeProps> = ({ provider, model }) => {
  const color = PROVIDER_COLORS[provider.toLowerCase()] ?? 'var(--text-secondary)';
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 5,
        padding: '3px 9px',
        borderRadius: 20,
        background: 'var(--bg-elevated)',
        border: `1px solid var(--border)`,
        fontSize: 11,
        fontFamily: 'var(--font-mono)',
        color,
        letterSpacing: 0.3,
        userSelect: 'none',
      }}
      title={`Active model: ${provider}/${model}`}
    >
      <span
        style={{ width: 6, height: 6, borderRadius: '50%', background: color, flexShrink: 0 }}
        aria-hidden="true"
      />
      {provider}/{model}
    </span>
  );
};
