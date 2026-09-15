import React from 'react';
import type { Skill } from '@/types';

interface SkillOption {
  value: Skill;
  label: string;
  icon: string;
  description: string;
  color: string;
  glow: string;
}

const SKILLS: SkillOption[] = [
  {
    value: 'rag',
    label: 'Ask Lenny',
    icon: '💬',
    description: 'Grounded Q&A from transcripts',
    color: 'linear-gradient(135deg, #38bdf8, #6366f1)',
    glow: 'rgba(56,189,248,0.3)',
  },
  {
    value: 'ship30',
    label: 'Ship 30 Essay',
    icon: '✍️',
    description: '~1,250-word essay in Ship 30 style',
    color: 'linear-gradient(135deg, #a78bfa, #ec4899)',
    glow: 'rgba(167,139,250,0.3)',
  },
  {
    value: 'artifact_md',
    label: 'Markdown Doc',
    icon: '📄',
    description: 'Generate a Markdown artifact',
    color: 'linear-gradient(135deg, #34d399, #059669)',
    glow: 'rgba(52,211,153,0.3)',
  },
  {
    value: 'artifact_html',
    label: 'HTML Page',
    icon: '🌐',
    description: 'Generate a sandboxed HTML artifact',
    color: 'linear-gradient(135deg, #fbbf24, #f97316)',
    glow: 'rgba(251,191,36,0.3)',
  },
];

interface SkillSelectorProps {
  selected: Skill;
  onChange: (skill: Skill) => void;
}

export const SkillSelector: React.FC<SkillSelectorProps> = ({ selected, onChange }) => {
  return (
    <div
      role="radiogroup"
      aria-label="Select skill"
      style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}
    >
      {SKILLS.map(skill => {
        const isSelected = selected === skill.value;
        return (
          <button
            key={skill.value}
            role="radio"
            aria-checked={isSelected}
            onClick={() => onChange(skill.value)}
            title={skill.description}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 5,
              padding: '5px 13px',
              borderRadius: 20,
              border: isSelected ? '1px solid transparent' : '1px solid var(--border)',
              background: isSelected ? skill.color : 'var(--bg-elevated)',
              color: isSelected ? '#fff' : 'var(--text-secondary)',
              cursor: 'pointer',
              fontSize: 12,
              fontWeight: isSelected ? 700 : 400,
              transition: 'all 0.15s',
              whiteSpace: 'nowrap',
              boxShadow: isSelected ? `0 4px 14px ${skill.glow}` : 'none',
              transform: isSelected ? 'translateY(-1px)' : 'none',
            }}
          >
            <span aria-hidden="true">{skill.icon}</span>
            {skill.label}
          </button>
        );
      })}
    </div>
  );
};
