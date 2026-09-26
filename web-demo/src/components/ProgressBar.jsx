import React from 'react';

export default function ProgressBar({ progress, label }) {
  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between mb-2 text-sm text-dark-300 font-medium">
          <span>{label}</span>
          <span>{Math.round(progress)}%</span>
        </div>
      )}
      <div className="w-full bg-white/5 rounded-full h-2 overflow-hidden border border-white/5">
        <div
          className="h-full bg-gradient-to-r from-gold-500 to-amber-500 rounded-full transition-all duration-300 ease-out shadow-[0_0_10px_rgba(212,168,83,0.5)]"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
