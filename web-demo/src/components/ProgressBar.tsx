import React from 'react';

interface ProgressBarProps {
  progress: number;
  label?: string;
  stageName?: string;
}

export default function ProgressBar({ progress, label, stageName }: ProgressBarProps) {
  const clampedProgress = Math.min(100, Math.max(0, Math.round(progress)));

  return (
    <div className="w-full max-w-lg mx-auto">
      <div className="flex items-center justify-between mb-2 text-xs font-medium uppercase tracking-wider text-ink-muted dark:text-ink-muted-dark">
        <span>{stageName || label || 'Processing'}</span>
        <span className="font-semibold text-accent-sepia">{clampedProgress}%</span>
      </div>

      <div className="w-full bg-black/10 dark:bg-white/10 rounded-full h-2 overflow-hidden border border-border-theme">
        <div
          className="h-full bg-accent-sepia transition-all duration-300 ease-out rounded-full shadow-[0_0_12px_rgba(196,151,70,0.5)]"
          style={{ width: `${clampedProgress}%` }}
        />
      </div>
    </div>
  );
}
