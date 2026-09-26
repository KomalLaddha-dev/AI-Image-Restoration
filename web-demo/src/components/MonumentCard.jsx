import React from 'react';
import { Link } from 'react-router-dom';
import { CheckCircle, WarningCircle, MapPin, Clock, ArrowRight } from '@phosphor-icons/react';

export default function MonumentCard({ data }) {
  if (!data) return null;

  const isHighConfidence = data.confidence >= 0.8;
  const confidencePct = Math.round(data.confidence * 100);

  return (
    <div className="glass-card p-8 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-gold-500/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none" />

      <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold tracking-wide border
        ${isHighConfidence 
          ? 'bg-green-500/10 text-green-400 border-green-500/20' 
          : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
        }
      `}>
        {isHighConfidence ? <CheckCircle weight="bold" /> : <WarningCircle weight="bold" />}
        {confidencePct}% Match
      </div>

      <h2 className="font-serif text-3xl font-bold my-4 text-white">
        {data.monument_name || data.name}
      </h2>

      <div className="flex flex-wrap gap-4 text-sm text-dark-300 mb-6">
        {data.location && (
          <span className="flex items-center gap-1.5 bg-white/5 px-3 py-1.5 rounded-lg border border-white/5">
            <MapPin weight="duotone" className="text-gold-500" />
            {data.location}
          </span>
        )}
        {data.era && (
          <span className="flex items-center gap-1.5 bg-white/5 px-3 py-1.5 rounded-lg border border-white/5">
            <Clock weight="duotone" className="text-gold-500" />
            {data.era}
          </span>
        )}
      </div>

      {data.monument_id && (
        <Link
          to={`/history/${data.monument_id}`}
          className="btn-primary inline-flex mt-2"
        >
          Read History <ArrowRight weight="bold" />
        </Link>
      )}
    </div>
  );
}
