'use client';

import React from 'react';

interface ScoreRingProps {
  score: number | null;
  size?: number;
  strokeWidth?: number;
  label?: string;
  showLabel?: boolean;
}

export default function ScoreRing({
  score,
  size = 56,
  strokeWidth = 5,
  label,
  showLabel = false,
}: ScoreRingProps) {
  const value = score ?? 0;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  const getColor = (s: number) => {
    if (s >= 75) return '#22c55e';
    if (s >= 60) return '#4ade80';
    if (s >= 45) return '#fbbf24';
    if (s >= 30) return '#f97316';
    return '#ef4444';
  };

  const color = getColor(value);

  if (score === null || score === undefined) {
    return (
      <div style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
        <div
          style={{
            width: size,
            height: size,
            borderRadius: '50%',
            background: 'rgba(100, 116, 139, 0.1)',
            border: '2px dashed rgba(100, 116, 139, 0.2)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: size * 0.22,
            color: 'var(--text-muted)',
            fontFamily: "'JetBrains Mono', monospace",
          }}
        >
          —
        </div>
        {showLabel && label && (
          <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textAlign: 'center' }}>
            {label}
          </span>
        )}
      </div>
    );
  }

  return (
    <div style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
      <div style={{ position: 'relative', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
        <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="rgba(148, 163, 184, 0.08)"
            strokeWidth={strokeWidth}
          />
          {/* Score arc */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{
              transition: 'stroke-dashoffset 0.8s ease, stroke 0.3s ease',
              filter: `drop-shadow(0 0 4px ${color}50)`,
            }}
          />
        </svg>
        {/* Center value */}
        <span
          style={{
            position: 'absolute',
            fontSize: size * 0.28,
            fontWeight: 700,
            fontFamily: "'JetBrains Mono', monospace",
            color: color,
          }}
        >
          {Math.round(value)}
        </span>
      </div>
      {showLabel && label && (
        <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textAlign: 'center' }}>
          {label}
        </span>
      )}
    </div>
  );
}
