import React from 'react';

interface ModelBadgeProps {
  provider: string;
  model: string;
}

const PROVIDER_GRADIENTS: Record<string, { gradient: string; dot: string }> = {
  anthropic: { gradient: 'linear-gradient(135deg, #f59e0b, #ef4444)', dot: '#f59e0b' },
  ollama:    { gradient: 'linear-gradient(135deg, #34d399, #059669)', dot: '#34d399' },
  openai:    { gradient: 'linear-gradient(135deg, #38bdf8, #6366f1)', dot: '#38bdf8' },
};

export const ModelBadge: React.FC<ModelBadgeProps> = ({ provider, model }) => {
  const style = PROVIDER_GRADIENTS[provider.toLowerCase()] ?? {
    gradient: 'linear-gradient(135deg, #a78bfa, #ec4899)',
    dot: '#a78bfa',
  };

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        padding: '4px 12px',
        borderRadius: 20,
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border)',
        fontSize: 11,
        fontFamily: 'var(--font-mono)',
        letterSpacing: 0.3,
        userSelect: 'none',
        boxShadow: `0 0 12px rgba(167,139,250,0.15)`,
      }}
      title={`Active model: ${provider}/${model}`}
    >
      {/* Animated dot */}
      <span
        style={{
          width: 7,
          height: 7,
          borderRadius: '50%',
          background: style.dot,
          flexShrink: 0,
          boxShadow: `0 0 6px ${style.dot}`,
          animation: 'pulse-dot 2s infinite',
        }}
        aria-hidden="true"
      />
      <span style={{
        background: style.gradient,
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        backgroundClip: 'text',
        fontWeight: 600,
      }}>
        {provider}/{model}
      </span>
      <style>{`
        @keyframes pulse-dot {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.6; transform: scale(0.85); }
        }
      `}</style>
    </span>
  );
};
