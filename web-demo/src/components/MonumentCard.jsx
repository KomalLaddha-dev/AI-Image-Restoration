import React from 'react';
import { Link } from 'react-router-dom';

export default function MonumentCard({ data }) {
  if (!data) return null;

  const confidenceLevel = data.confidence >= 0.8 ? 'high' : 'medium';
  const confidencePct = Math.round(data.confidence * 100);

  return (
    <div className="glass-card monument-card">
      <span className={`confidence-badge ${confidenceLevel}`}>
        {confidenceLevel === 'high' ? '✓' : '~'} {confidencePct}% match
      </span>

      <h2>{data.monument_name || data.name}</h2>

      <div className="meta">
        {data.location && <span>📍 {data.location}</span>}
        {data.era && <span>🕐 {data.era}</span>}
      </div>

      {data.monument_id && (
        <Link
          to={`/history/${data.monument_id}`}
          className="btn btn-primary"
          style={{ marginTop: 'var(--space-4)' }}
        >
          Read History →
        </Link>
      )}
    </div>
  );
}
