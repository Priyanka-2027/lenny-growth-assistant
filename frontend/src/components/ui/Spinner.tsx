import React from 'react';

interface SpinnerProps {
  size?: number;
  color?: string;
  label?: string;
}

export const Spinner: React.FC<SpinnerProps> = ({
  size = 20,
  color = 'var(--accent)',
  label = 'Loading…',
}) => (
  <span
    role="status"
    aria-label={label}
    style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}
  >
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color}
      strokeWidth="2.5"
      strokeLinecap="round"
      style={{ animation: 'spin 0.8s linear infinite' }}
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="10" strokeOpacity="0.25" />
      <path d="M12 2 A10 10 0 0 1 22 12" />
    </svg>
    <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
  </span>
);
