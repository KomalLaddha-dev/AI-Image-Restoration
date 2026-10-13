import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Target, 
  MapPin, 
  Clock, 
  ArrowRight, 
  ArrowsClockwise, 
  CheckCircle, 
  WarningCircle, 
  Sparkle,
  Sliders
} from '@phosphor-icons/react';
import UploadZone from '../components/UploadZone';
import ProgressBar from '../components/ProgressBar';
import { identifyMonument } from '../utils/api';
import type { IdentifyResultData } from '../types';
import { CONFIDENCE_THRESHOLD, CONFIDENCE_THRESHOLD_PERCENT } from '../constants/thresholds';

export default function IdentifyPage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stageName, setStageName] = useState('Extracting architectural features');
  const [result, setResult] = useState<IdentifyResultData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleIdentify = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setProgress(15);
    setResult(null);

    const stages = [
      { pct: 30, name: 'Normalizing perspective & lighting' },
      { pct: 60, name: 'CLIP visual feature extraction' },
      { pct: 85, name: 'Matching against global heritage gallery' },
      { pct: 98, name: 'Calibrating identification confidence' },
    ];

    let i = 0;
    const interval = setInterval(() => {
      if (i < stages.length) {
        setProgress(stages[i].pct);
        setStageName(stages[i].name);
        i++;
      }
    }, 450);

    try {
      const data = await identifyMonument(file);
      clearInterval(interval);
      setProgress(100);
      setResult(data);
    } catch (err: any) {
      clearInterval(interval);
      setError(err.message || 'Identification failed. Please try a different photo.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setResult(null);
    setError(null);
  };

  const userPhotoUrl = file ? URL.createObjectURL(file) : null;
  const isHighConfidence =
    result?.recognized === true &&
    result.confidence >= CONFIDENCE_THRESHOLD;

  return (
    <div className="w-full min-h-[calc(100dvh-4rem)] flex flex-col justify-center">
      {/* ── 1. Upload & Initial Scan State ──────────────────────────────── */}
      {!result && !loading && (
        <div className="w-full max-w-3xl mx-auto px-6 md:px-12 py-12 md:py-20 flex flex-col items-center">
          <div className="text-center max-w-2xl mx-auto mb-10">
            <h1 className="font-heading text-4xl sm:text-5xl font-bold tracking-tight text-ink dark:text-ink-dark mb-3">
              Monument <span className="italic font-normal text-accent-sepia">Identification</span>
            </h1>
            <p className="text-sm md:text-base text-ink-muted dark:text-ink-muted-dark leading-relaxed">
              Capture or upload any photograph of a historic site. Our computer vision classifier identifies the monument and retrieves its verified record.
            </p>
          </div>

          <UploadZone
            file={file}
            onFileSelect={setFile}
            title="Upload Monument Photograph"
            subtext="Snap a photo or upload an archival picture of any monument"
            actionLabel="Scan & Identify Monument"
            onAction={handleIdentify}
          />

          {error && (
            <div className="w-full mt-6 p-5 rounded-xl border border-red-500/30 bg-red-500/10 text-red-700 dark:text-red-300 flex items-start gap-3">
              <WarningCircle weight="fill" className="text-xl shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold">Identification Failed</h4>
                <p className="text-xs mt-1 leading-relaxed opacity-90">{error}</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── 2. Loading State ────────────────────────────────────────────── */}
      {loading && (
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-xl mx-auto px-6 py-20 flex flex-col items-center text-center"
        >
          <div className="w-16 h-16 rounded-full border-2 border-accent-sepia-faint border-t-accent-sepia animate-spin mb-8" />
          <h2 className="font-heading text-2xl font-bold text-ink dark:text-ink-dark mb-2">
            Analyzing Monument Features
          </h2>
          <p className="text-xs font-mono uppercase tracking-widest text-accent-sepia mb-8">
            {stageName}
          </p>

          <ProgressBar progress={progress} stageName={stageName} />
        </motion.div>
      )}

      {/* ── 3. High-Confidence Photo-as-Hero Result View (>= 70%) ────────── */}
      {result && isHighConfidence && userPhotoUrl && !loading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8 }}
          className="relative w-full min-h-[calc(100dvh-4rem)] flex flex-col justify-end overflow-hidden"
        >
          {/* Full-Bleed User's Own Uploaded Photo Background */}
          <div className="absolute inset-0 z-0 bg-black">
            <img
              src={userPhotoUrl}
              alt={result.monument_name}
              className="w-full h-full object-cover object-center brightness-95"
            />
            {/* Bottom-up gradient scrim: transparent at top -> dark at bottom for legibility */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/95 via-black/55 via-45% to-transparent pointer-events-none" />
            <div className="absolute inset-x-0 top-0 h-32 bg-gradient-to-b from-black/60 to-transparent pointer-events-none" />
          </div>

          {/* Scrim Overlay Content */}
          <div className="relative z-10 w-full max-w-5xl mx-auto px-6 md:px-12 pb-16 md:pb-24 pt-32">
            <motion.div
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="flex flex-col items-start"
            >
              {/* Top Meta Chips & Confidence Badge */}
              <div className="flex flex-wrap items-center gap-3 mb-4">
                {/* Confidence Badge using .glass-panel treatment */}
                <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full glass-panel text-xs font-semibold uppercase tracking-wider text-accent-green-light border border-accent-green/30">
                  <CheckCircle weight="fill" className="text-base text-accent-green-light" />
                  <span>{Math.round(result.confidence * 100)}% Match</span>
                </div>

                {result.location && (
                  <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full glass-panel text-xs font-medium text-white/90">
                    <MapPin weight="duotone" className="text-accent-sepia-light" />
                    <span>{result.location}</span>
                  </div>
                )}

                {result.era && (
                  <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full glass-panel text-xs font-medium text-white/90">
                    <Clock weight="duotone" className="text-accent-brown-light" />
                    <span>{result.era}</span>
                  </div>
                )}
              </div>

              {/* Monument Name in Serif Heading Font */}
              <h1 className="font-heading text-4xl sm:text-6xl md:text-7xl lg:text-8xl font-bold text-white tracking-tight leading-[1.05] mb-8 drop-shadow-md">
                {result.monument_name}
              </h1>

              {/* CTA Row */}
              <div className="flex flex-wrap items-center gap-4">
                <Link
                  to={`/history/${result.monument_id}`}
                  className="px-8 py-4 bg-accent-sepia hover:bg-accent-sepia-hover text-black font-semibold text-xs tracking-wider uppercase rounded-xl transition-all shadow-lg shadow-accent-sepia/30 hover:shadow-accent-sepia/50 flex items-center gap-2"
                >
                  <Sparkle weight="bold" /> Read Verified History <ArrowRight weight="bold" />
                </Link>

                <button
                  type="button"
                  onClick={handleReset}
                  className="px-6 py-4 rounded-xl glass-panel text-white hover:text-white font-semibold text-xs tracking-wider uppercase transition-colors flex items-center gap-2"
                >
                  <ArrowsClockwise weight="bold" /> Scan Another Monument
                </button>
              </div>
            </motion.div>
          </div>
        </motion.div>
      )}

      {/* ── 4. Low-Confidence Fallback View (< 70% or unverified) ─────────── */}
      {result && !isHighConfidence && !loading && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-3xl mx-auto px-6 md:px-12 py-16"
        >
          {/* Subtle softened neutral backdrop card */}
          <div className="rounded-3xl border border-border-theme bg-surface dark:bg-surface-dark p-8 md:p-12 shadow-xl">
            <div className="flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/25 text-amber-600 dark:text-amber-400 text-xs font-semibold uppercase tracking-wider mb-6 w-fit">
              <WarningCircle weight="fill" className="text-base" />
              Low Certainty Identification ({result ? Math.round(result.confidence * 100) : 0}%)
            </div>

            <h2 className="font-heading text-3xl md:text-4xl font-bold text-ink dark:text-ink-dark mb-4">
              {result.recognized ? result.monument_name : 'Monument Unconfirmed'}
            </h2>

            <p className="text-sm md:text-base text-ink-muted dark:text-ink-muted-dark leading-relaxed mb-8">
              The neural classifier detected architectural characteristics of{' '}
              <strong className="text-ink dark:text-ink-dark">{result.recognized ? result.monument_name : 'an unlisted landmark'}</strong>,
              but lighting, perspective, or image degradation kept confidence below our {CONFIDENCE_THRESHOLD_PERCENT}% verification threshold.
            </p>

            {/* Thumbnail comparison preview */}
            {userPhotoUrl && (
              <div className="flex flex-col sm:flex-row gap-6 items-center p-4 rounded-2xl bg-surface-subtle dark:bg-surface-dark/70 border border-border-theme mb-8">
                <div className="aspect-[4/3] w-48 rounded-xl overflow-hidden bg-black shrink-0">
                  <img src={userPhotoUrl} alt="Your capture" className="w-full h-full object-cover" />
                </div>
                <div className="text-left">
                  <span className="text-xs uppercase tracking-wider text-ink-muted font-semibold">Your Uploaded Capture</span>
                  <p className="text-xs text-ink-muted dark:text-ink-muted-dark mt-1 leading-relaxed">
                    Try running neural restoration first to remove noise and restore sharpness, or re-capture from a flatter frontal angle.
                  </p>
                </div>
              </div>
            )}

            {/* Options */}
            <div className="flex flex-wrap gap-4">
              {result.recognized && (
                <Link
                  to={`/history/${result.monument_id}`}
                  className="px-6 py-3.5 bg-accent-sepia hover:bg-accent-sepia-hover text-black font-semibold text-xs tracking-wider uppercase rounded-xl transition-all shadow-md flex items-center gap-2"
                >
                  View Candidate Record <ArrowRight weight="bold" />
                </Link>
              )}

              <Link
                to="/restore"
                className="px-6 py-3.5 bg-surface dark:bg-surface-dark hover:bg-surface-subtle border border-border-theme font-semibold text-xs tracking-wider uppercase rounded-xl transition-colors flex items-center gap-2 text-ink dark:text-ink-dark"
              >
                <Sliders weight="bold" /> Restore Photo First
              </Link>

              <button
                type="button"
                onClick={handleReset}
                className="px-6 py-3.5 text-ink-muted dark:text-ink-muted-dark hover:text-ink font-semibold text-xs tracking-wider uppercase transition-colors"
              >
                Scan Another Photo
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}
