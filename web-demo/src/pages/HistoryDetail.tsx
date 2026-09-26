import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  ArrowLeft, 
  MapPin, 
  Clock, 
  Bank, 
  Certificate, 
  Compass, 
  ArrowUpRight, 
  Sparkle,
  Sliders
} from '@phosphor-icons/react';
import { getHistory } from '../utils/api';
import BeforeAfterSlider from '../components/BeforeAfterSlider';
import type { HistoryResponse } from '../types';

export default function HistoryDetail() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<HistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showArchivalComparison, setShowArchivalComparison] = useState(false);

  useEffect(() => {
    async function loadData() {
      if (!id) return;
      try {
        setLoading(true);
        const result = await getHistory(id);
        setData(result);
      } catch (err: any) {
        setError(err.message || 'Failed to load historical record.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [id]);

  // Determine curated authoritative reference image (Section 4.b: not the user's capture, authoritative record)
  const getReferenceImage = () => {
    if (id === 'taj_mahal') return '/samples/taj_mahal.jpg';
    if (id === 'qutub_minar') return '/samples/qutub_minar.jpg';
    if (id === 'colosseum') return '/samples/detroit_1915.jpg';
    if (data?.related_images && data.related_images.length > 0) {
      const first = data.related_images[0];
      return typeof first === 'string' ? first : first.url;
    }
    return '/samples/taj_mahal.jpg';
  };

  if (loading) {
    return (
      <div className="w-full min-h-[70vh] flex flex-col items-center justify-center">
        <div className="w-12 h-12 rounded-full border-2 border-accent-sepia-faint border-t-accent-sepia animate-spin mb-4" />
        <p className="text-xs uppercase tracking-widest text-ink-muted font-mono">
          Retrieving Archival Record
        </p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="w-full max-w-xl mx-auto px-6 py-24 text-center">
        <h2 className="font-heading text-3xl font-bold mb-4 text-ink dark:text-ink-dark">
          Archival Record Unavailable
        </h2>
        <p className="text-sm text-ink-muted dark:text-ink-muted-dark leading-relaxed mb-8">
          {error || 'The requested monument record could not be located in the current corpus.'}
        </p>
        <Link
          to="/identify"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-accent-sepia text-black font-semibold text-xs uppercase tracking-wider shadow-md"
        >
          <ArrowLeft weight="bold" /> Return to Scanner
        </Link>
      </div>
    );
  }

  const referenceImage = getReferenceImage();

  return (
    <div className="w-full flex flex-col">
      {/* ── 1. Authoritative Record Hero (Section 4.b) ───────────────────── */}
      <section className="relative w-full h-[65vh] md:h-[75vh] min-h-[500px] flex flex-col justify-end overflow-hidden bg-black">
        {/* Curated Reference Image with subtle Ken Burns pan/zoom CSS animation */}
        <div className="absolute inset-0 z-0 overflow-hidden">
          <img
            src={referenceImage}
            alt={data.name}
            className="w-full h-full object-cover object-center animate-ken-burns brightness-[0.92]"
          />
          {/* Bottom-Up Gradient Scrim for perfect text legibility */}
          <div className="absolute inset-0 bg-gradient-to-t from-canvas via-canvas/60 via-40% to-transparent dark:from-canvas-dark dark:via-canvas-dark/60 pointer-events-none transition-colors duration-300" />
          <div className="absolute inset-x-0 top-0 h-28 bg-gradient-to-b from-black/50 to-transparent pointer-events-none" />
        </div>

        {/* Hero Title & Meta Overlay */}
        <div className="relative z-10 w-full max-w-5xl mx-auto px-6 md:px-12 pb-12 md:pb-16 pt-24">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <Link
              to="/identify"
              className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-ink-muted dark:text-ink-muted-dark hover:text-accent-sepia mb-6 transition-colors"
            >
              <ArrowLeft weight="bold" /> Back to Scanner
            </Link>

            {/* Monument Name in Serif Heading Font */}
            <h1 className="font-heading text-4xl sm:text-6xl md:text-7xl font-bold tracking-tight text-ink dark:text-ink-dark leading-[1.08] mb-6">
              {data.name}
            </h1>

            {/* Quick Architectural Badges */}
            <div className="flex flex-wrap items-center gap-3 text-xs font-medium">
              {data.location && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-surface/80 dark:bg-surface-dark/80 border border-border-theme backdrop-blur-sm">
                  <MapPin weight="duotone" className="text-accent-sepia" />
                  {data.location}
                </span>
              )}
              {data.era && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-surface/80 dark:bg-surface-dark/80 border border-border-theme backdrop-blur-sm">
                  <Clock weight="duotone" className="text-accent-brown" />
                  {data.era}
                </span>
              )}
              {data.unesco_status && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-accent-green-faint border border-accent-green/30 text-accent-green-light">
                  <Certificate weight="duotone" className="text-accent-green" />
                  {data.unesco_status}
                </span>
              )}
            </div>
          </motion.div>
        </div>
      </section>

      {/* ── 2. Editorial Summary & Architectural Record ─────────────────── */}
      <section className="w-full max-w-4xl mx-auto px-6 md:px-12 py-16 md:py-24">
        {/* Historical Summary with Archival Drop Cap */}
        <div className="mb-16">
          <h2 className="text-xs font-semibold uppercase tracking-[0.2em] text-accent-sepia mb-6 font-mono">
            Historical Provenance
          </h2>
          <p className="font-body text-base sm:text-lg md:text-xl text-ink/90 dark:text-ink-dark/90 leading-relaxed font-normal first-letter:font-heading first-letter:text-6xl md:first-letter:text-7xl first-letter:float-left first-letter:pr-4 first-letter:font-bold first-letter:text-accent-sepia first-letter:leading-none">
            {data.summary}
          </p>
        </div>

        {/* Archival Before/After Restoration Module (Section 4.b) */}
        <div className="my-16 p-6 md:p-8 rounded-3xl border border-border-theme bg-surface-subtle/50 dark:bg-surface-dark/40 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
            <div>
              <h3 className="font-heading text-xl font-bold text-ink dark:text-ink-dark flex items-center gap-2">
                <Sparkle weight="fill" className="text-accent-sepia" /> Archival Restoration Study
              </h3>
              <p className="text-xs text-ink-muted dark:text-ink-muted-dark mt-1">
                Interactive comparison of the 19th-century photographic plate vs neural restoration.
              </p>
            </div>

            <button
              type="button"
              onClick={() => setShowArchivalComparison(!showArchivalComparison)}
              className="px-4 py-2 rounded-lg border border-border-theme bg-surface dark:bg-surface-dark text-xs font-semibold uppercase tracking-wider hover:border-accent-sepia transition-colors flex items-center gap-1.5 self-start sm:self-auto"
            >
              <Sliders weight="bold" /> {showArchivalComparison ? 'Hide Slider' : 'View Slider'}
            </button>
          </div>

          {showArchivalComparison ? (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}>
              <BeforeAfterSlider
                beforeSrc="/samples/sample_portrait_before.png"
                afterSrc="/samples/sample_portrait_after.png"
                beforeLabel="Archival Plate"
                afterLabel="Neural Restored"
                aspectRatio="aspect-[4/3] md:aspect-[16/10]"
              />
            </motion.div>
          ) : (
            <div
              onClick={() => setShowArchivalComparison(true)}
              className="cursor-pointer group relative aspect-[16/9] w-full rounded-2xl overflow-hidden bg-black border border-border-theme flex items-center justify-center"
            >
              <img
                src={referenceImage}
                alt="Preview"
                className="w-full h-full object-cover opacity-60 group-hover:scale-105 transition-transform duration-500"
              />
              <div className="absolute inset-0 bg-black/40 group-hover:bg-black/20 transition-colors" />
              <div className="relative px-6 py-3 rounded-full glass-panel text-xs font-semibold uppercase tracking-wider text-white flex items-center gap-2 shadow-xl">
                <Sliders weight="bold" /> Click to Open Comparison Slider
              </div>
            </div>
          )}
        </div>

        {/* Architectural Specifications Grid */}
        <div className="my-16 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 pt-12 border-t border-border-theme">
          {data.builder && (
            <div className="p-5 rounded-2xl bg-surface dark:bg-surface-dark border border-border-theme">
              <span className="text-[11px] font-mono uppercase tracking-wider text-ink-muted dark:text-ink-muted-dark block mb-1">
                Builder / Patron
              </span>
              <p className="font-heading font-semibold text-base text-ink dark:text-ink-dark">
                {data.builder}
              </p>
            </div>
          )}

          {data.architectural_style && (
            <div className="p-5 rounded-2xl bg-surface dark:bg-surface-dark border border-border-theme">
              <span className="text-[11px] font-mono uppercase tracking-wider text-ink-muted dark:text-ink-muted-dark block mb-1">
                Architectural Style
              </span>
              <p className="font-heading font-semibold text-base text-ink dark:text-ink-dark">
                {data.architectural_style}
              </p>
            </div>
          )}

          {data.coordinates && (
            <div className="p-5 rounded-2xl bg-surface dark:bg-surface-dark border border-border-theme">
              <span className="text-[11px] font-mono uppercase tracking-wider text-ink-muted dark:text-ink-muted-dark block mb-1">
                Coordinates
              </span>
              <p className="font-mono text-sm text-ink dark:text-ink-dark flex items-center gap-1.5">
                <Compass weight="duotone" className="text-accent-sepia" />
                {data.coordinates[0].toFixed(4)}° N, {data.coordinates[1].toFixed(4)}° E
              </p>
            </div>
          )}
        </div>

        {/* ── 3. Chronological Historical Timeline ───────────────────────── */}
        {data.timeline && data.timeline.length > 0 && (
          <div className="my-20 pt-12 border-t border-border-theme">
            <h3 className="font-heading text-2xl md:text-3xl font-bold text-ink dark:text-ink-dark mb-12">
              Historical Timeline
            </h3>

            <div className="relative border-l-2 border-accent-sepia/30 ml-3 sm:ml-6 space-y-12">
              {data.timeline.map((event, idx) => (
                <div key={idx} className="relative pl-8 sm:pl-10 group">
                  {/* Timeline Node Marker */}
                  <div className="absolute -left-[9px] top-1.5 w-4 h-4 rounded-full bg-canvas dark:bg-canvas-dark border-2 border-accent-sepia group-hover:bg-accent-sepia transition-colors duration-200" />

                  {/* Year Tag with accent-sepia */}
                  <span className="inline-block px-3 py-1 rounded-md bg-accent-sepia-faint border border-accent-sepia/25 text-accent-sepia font-mono text-xs font-semibold tracking-wider mb-2">
                    {event.year}
                  </span>

                  <p className="text-sm sm:text-base text-ink-muted dark:text-ink-muted-dark leading-relaxed font-normal">
                    {event.event}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── 4. Grounded Academic Sources & Citations ───────────────────── */}
        {data.sources && data.sources.length > 0 && (
          <div className="my-16 pt-12 border-t border-border-theme">
            <h3 className="text-xs font-semibold uppercase tracking-[0.2em] text-accent-sepia mb-6 font-mono">
              Academic Citations & Archival Sources
            </h3>

            <div className="space-y-3">
              {data.sources.map((src, idx) => (
                <div key={idx} className="flex items-center gap-2 text-sm">
                  {src.url ? (
                    <a
                      href={src.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 text-accent-sepia hover:text-accent-sepia-hover font-medium underline underline-offset-4 decoration-accent-sepia/30 hover:decoration-accent-sepia transition-colors group"
                    >
                      <span>{src.name}</span>
                      <ArrowUpRight weight="bold" className="text-xs group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                    </a>
                  ) : (
                    <span className="text-ink-muted dark:text-ink-muted-dark">{src.name}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
