'use client';

import React from 'react';
import ScoreRing from '@/components/ScoreRing';
import RecommendationBadge from '@/components/StockHelpers';
import type { StockSummary } from '@/lib/api';

interface ScoreLayerPanelProps {
  stock: StockSummary;
}

export default function ScoreLayerPanel({ stock }: ScoreLayerPanelProps) {
  return (
    <div
      className="card"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 20,
        flexWrap: 'wrap',
        marginBottom: 16,
        padding: '16px 20px',
      }}
    >
      {/* Overall score — larger ring */}
      <ScoreRing score={stock.overall_score} size={72} strokeWidth={6} showLabel label="Genel" />

      {/* Vertical divider */}
      <div style={{ width: 1, height: 52, background: 'var(--border-primary, rgba(148,163,184,0.1))', flexShrink: 0 }} />

      {/* 3-layer scores: Temel, Teknik, Algi */}
      <ScoreRing score={stock.fundamental_score} size={52} strokeWidth={4} showLabel label="Temel" />
      <ScoreRing score={stock.technical_score} size={52} strokeWidth={4} showLabel label="Teknik" />
      <ScoreRing score={stock.sentiment_score} size={52} strokeWidth={4} showLabel label="Algı" />

      {/* Recommendation badge pushed right */}
      <div style={{ marginLeft: 'auto' }}>
        <RecommendationBadge recommendation={stock.recommendation} />
      </div>
    </div>
  );
}
