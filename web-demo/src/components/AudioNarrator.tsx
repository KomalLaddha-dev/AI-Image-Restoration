import React, { useState, useEffect, useRef } from 'react';
import { 
  SpeakerHigh, 
  SpeakerSlash, 
  Play, 
  Pause, 
  Stop, 
  ArrowsClockwise,
  Waveform,
  Gauge
} from '@phosphor-icons/react';

interface AudioNarratorProps {
  title: string;
  subtitle?: string | null;
  text: string;
  className?: string;
  variant?: 'hero' | 'card' | 'inline';
}

export default function AudioNarrator({
  title,
  subtitle,
  text,
  className = '',
  variant = 'hero',
}: AudioNarratorProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [rate, setRate] = useState<number>(1.0);
  const [supported, setSupported] = useState(true);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  // Check speech synthesis support on mount
  useEffect(() => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      setSupported(false);
    }

    return () => {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const fullTextToRead = subtitle ? `${title}. ${subtitle}. ${text}` : `${title}. ${text}`;

  const handlePlayPause = () => {
    if (!supported) return;

    const synth = window.speechSynthesis;

    if (isPlaying && !isPaused) {
      synth.pause();
      setIsPaused(true);
      return;
    }

    if (isPaused) {
      synth.resume();
      setIsPaused(false);
      return;
    }

    // Cancel any previous speech
    synth.cancel();

    const utterance = new SpeechSynthesisUtterance(fullTextToRead);
    utterance.rate = rate;
    utterance.pitch = 1.0;

    // Pick English or default voice
    const voices = synth.getVoices();
    const naturalVoice = voices.find(
      (v) => v.lang.startsWith('en') && (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Premium'))
    ) || voices.find((v) => v.lang.startsWith('en')) || voices[0];

    if (naturalVoice) {
      utterance.voice = naturalVoice;
    }

    utterance.onstart = () => {
      setIsPlaying(true);
      setIsPaused(false);
    };

    utterance.onend = () => {
      setIsPlaying(false);
      setIsPaused(false);
    };

    utterance.onerror = () => {
      setIsPlaying(false);
      setIsPaused(false);
    };

    utteranceRef.current = utterance;
    synth.speak(utterance);
  };

  const handleStop = () => {
    if (!supported) return;
    window.speechSynthesis.cancel();
    setIsPlaying(false);
    setIsPaused(false);
  };

  const cycleRate = () => {
    const nextRates = [1.0, 1.2, 0.85];
    const nextIdx = (nextRates.indexOf(rate) + 1) % nextRates.length;
    const newRate = nextRates[nextIdx];
    setRate(newRate);

    // If currently playing, restart with new rate
    if (isPlaying) {
      window.speechSynthesis.cancel();
      setIsPlaying(false);
      setIsPaused(false);
      setTimeout(() => {
        const synth = window.speechSynthesis;
        const utterance = new SpeechSynthesisUtterance(fullTextToRead);
        utterance.rate = newRate;
        const voices = synth.getVoices();
        const v = voices.find((v) => v.lang.startsWith('en')) || voices[0];
        if (v) utterance.voice = v;
        utterance.onend = () => setIsPlaying(false);
        utterance.onerror = () => setIsPlaying(false);
        synth.speak(utterance);
        setIsPlaying(true);
      }, 50);
    }
  };

  if (!supported) {
    return null;
  }

  // Inline / Minimal variant
  if (variant === 'inline') {
    return (
      <button
        type="button"
        onClick={handlePlayPause}
        title={isPlaying && !isPaused ? "Pause audio narration" : "Listen to description"}
        className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wider transition-all ${
          isPlaying
            ? 'bg-accent-sepia text-black shadow-md shadow-accent-sepia/30'
            : 'bg-surface dark:bg-surface-dark border border-border-theme text-ink dark:text-ink-dark hover:border-accent-sepia'
        } ${className}`}
      >
        {isPlaying && !isPaused ? (
          <>
            <Pause weight="fill" className="text-sm" />
            <span>Pause Audio</span>
          </>
        ) : (
          <>
            <SpeakerHigh weight="fill" className="text-sm text-accent-sepia" />
            <span>Listen</span>
          </>
        )}
      </button>
    );
  }

  // Hero / Card variant (Full interactive audio player bar)
  return (
    <div
      className={`rounded-2xl p-4 transition-all duration-300 ${
        variant === 'hero'
          ? 'glass-panel border border-white/20 text-white backdrop-blur-md bg-black/40'
          : 'bg-surface dark:bg-surface-dark border border-border-theme text-ink dark:text-ink-dark shadow-sm'
      } ${className}`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        {/* Left: Speaker icon & Waveform visualizer */}
        <div className="flex items-center gap-3">
          <div
            className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 transition-colors ${
              isPlaying && !isPaused
                ? 'bg-accent-sepia text-black shadow-md shadow-accent-sepia/40'
                : variant === 'hero'
                ? 'bg-white/10 text-accent-sepia-light'
                : 'bg-accent-sepia-faint text-accent-sepia'
            }`}
          >
            {isPlaying && !isPaused ? (
              <SpeakerHigh weight="fill" className="text-xl animate-pulse" />
            ) : (
              <Waveform weight="duotone" className="text-xl" />
            )}
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono uppercase tracking-widest text-accent-sepia font-semibold">
                Audio Narration Guide
              </span>
              {isPlaying && !isPaused && (
                <span className="flex items-center gap-1">
                  <span className="w-1.5 h-3 bg-accent-sepia animate-[bounce_0.8s_infinite] rounded-full inline-block" />
                  <span className="w-1.5 h-4 bg-accent-sepia animate-[bounce_0.8s_infinite_0.2s] rounded-full inline-block" />
                  <span className="w-1.5 h-2.5 bg-accent-sepia animate-[bounce_0.8s_infinite_0.4s] rounded-full inline-block" />
                </span>
              )}
            </div>
            <p className="text-xs font-medium opacity-90 line-clamp-1">
              {isPlaying ? (isPaused ? 'Paused — click play to continue' : `Narrating: ${title}`) : 'Listen to verified historical significance'}
            </p>
          </div>
        </div>

        {/* Right: Controls (Play/Pause, Stop, Speed Rate) */}
        <div className="flex items-center gap-2 self-end sm:self-auto shrink-0">
          {/* Rate Selector */}
          <button
            type="button"
            onClick={cycleRate}
            title="Speech rate"
            className={`px-2.5 py-1.5 rounded-lg text-[11px] font-mono font-bold tracking-wider transition-colors ${
              variant === 'hero'
                ? 'bg-white/10 hover:bg-white/20 text-white'
                : 'bg-surface-subtle dark:bg-surface-dark/70 border border-border-theme hover:border-accent-sepia text-ink dark:text-ink-dark'
            }`}
          >
            {rate}x
          </button>

          {/* Stop Button (visible when playing or paused) */}
          {(isPlaying || isPaused) && (
            <button
              type="button"
              onClick={handleStop}
              title="Stop speech"
              className={`p-2 rounded-lg transition-colors ${
                variant === 'hero'
                  ? 'bg-white/10 hover:bg-red-500/30 text-white hover:text-red-300'
                  : 'bg-surface-subtle hover:bg-red-500/10 text-ink dark:text-ink-dark hover:text-red-500 border border-border-theme'
              }`}
            >
              <Stop weight="fill" className="text-sm" />
            </button>
          )}

          {/* Primary Play / Pause Action Button */}
          <button
            type="button"
            onClick={handlePlayPause}
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold uppercase tracking-wider transition-all shadow-md ${
              isPlaying && !isPaused
                ? 'bg-accent-sepia text-black hover:bg-accent-sepia-hover shadow-accent-sepia/30'
                : variant === 'hero'
                ? 'bg-accent-sepia text-black hover:bg-accent-sepia-hover shadow-accent-sepia/30'
                : 'bg-accent-sepia text-black hover:bg-accent-sepia-hover shadow-accent-sepia/20'
            }`}
          >
            {isPlaying && !isPaused ? (
              <>
                <Pause weight="fill" className="text-sm" />
                <span>Pause</span>
              </>
            ) : isPaused ? (
              <>
                <Play weight="fill" className="text-sm" />
                <span>Resume</span>
              </>
            ) : (
              <>
                <Play weight="fill" className="text-sm" />
                <span>Play Audio</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
