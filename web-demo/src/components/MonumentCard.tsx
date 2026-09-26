import React from 'react';
import { Link } from 'react-router-dom';
import { MapPin, Clock, ArrowRight } from '@phosphor-icons/react';

interface MonumentCardProps {
  id: string;
  name: string;
  location?: string | null;
  era?: string | null;
  imageUrl?: string | null;
  confidence?: number;
}

export default function MonumentCard({
  id,
  name,
  location,
  era,
  imageUrl,
  confidence,
}: MonumentCardProps) {
  return (
    <Link
      to={`/history/${id}`}
      className="group block rounded-2xl overflow-hidden border border-border-theme bg-surface dark:bg-surface-dark hover:border-accent-sepia/50 transition-all duration-300 hover:-translate-y-1 shadow-sm hover:shadow-xl"
    >
      {/* Standard Card Thumbnail (Section 4.c: standard thumbnails for grid scannability) */}
      <div className="relative aspect-[16/10] w-full overflow-hidden bg-black/10 dark:bg-white/5">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 ease-out"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-ink-faint">
            No archival image
          </div>
        )}

        {typeof confidence === 'number' && (
          <div className="absolute top-3 right-3 px-2.5 py-1 rounded-full glass-panel text-[11px] font-semibold text-white tracking-wider uppercase">
            {Math.round(confidence * 100)}% Match
          </div>
        )}
      </div>

      {/* Card Content */}
      <div className="p-6">
        <h3 className="font-heading text-xl font-semibold text-ink dark:text-ink-dark group-hover:text-accent-sepia transition-colors mb-2">
          {name}
        </h3>

        <div className="flex flex-wrap gap-3 text-xs text-ink-muted dark:text-ink-muted-dark mb-4">
          {location && (
            <span className="flex items-center gap-1.5">
              <MapPin weight="duotone" className="text-accent-sepia" />
              {location}
            </span>
          )}
          {era && (
            <span className="flex items-center gap-1.5">
              <Clock weight="duotone" className="text-accent-brown" />
              {era}
            </span>
          )}
        </div>

        <div className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-accent-sepia group-hover:gap-2.5 transition-all">
          Explore Record <ArrowRight weight="bold" />
        </div>
      </div>
    </Link>
  );
}
