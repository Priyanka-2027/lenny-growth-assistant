import React from 'react';
import type { Skill } from '@/types';

interface SkillOption {
  value: Skill;
  label: string;
  icon: string;
  description: string;
}

const SKILLS: SkillOption[] = [
  {
    value: 'rag',
    label: 'Ask Lenny',
    icon: '💬',
    description: 'Grounded Q&A from transcripts',
  },
  {
    value: 'ship30',
    label: 'Ship 30 Essay',
    icon: '✍️',
    description: '~1,250-word essay in Ship 30 style',
  },
  {
    value: 'artifact_md',
    label: 'Markdown Doc',
    icon: '📄',
    description: 'Generate a Markdown artifact',
  },
  {
    value: 'artifact_html',
    label: 'HTML Page',
    icon: '🌐',
    description: 'Generate a sandboxed HTML artifact',
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
      {SKILLS.map(skill => (
        <button
          key={skill.value}
          role="radio"
          aria-checked={selected === skill.value}
          onClick={() => onChange(skill.value)}
          title={skill.description}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 5,
            padding: '5px 11px',
            borderRadius: 20,
            border: selected === skill.value
              ? '1px solid var(--accent)'
              : '1px solid var(--border)',
            background: selected === skill.value ? 'var(--accent-subtle)' : 'var(--bg-elevated)',
            color: selected === skill.value ? 'var(--accent)' : 'var(--text-secondary)',
            cursor: 'pointer',
            fontSize: 12,
            fontWeight: selected === skill.value ? 600 : 400,
            transition: 'all 0.12s',
            whiteSpace: 'nowrap',
          }}
        >
          <span aria-hidden="true">{skill.icon}</span>
          {skill.label}
        </button>
      ))}
    </div>
  );
};
