import React from 'react';

export default function ProgressBar({ progress, label }) {
  return (
    <div style={{ width: '100%' }}>
      {label && (
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginBottom: '0.5rem',
          fontSize: 'var(--text-sm)',
          color: 'var(--color-text-secondary)',
        }}>
          <span>{label}</span>
          <span>{Math.round(progress)}%</span>
        </div>
      )}
      <div className="progress-bar-container">
        <div
          className="progress-bar-fill"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
