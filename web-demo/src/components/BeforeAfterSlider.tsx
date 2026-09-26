import React, { useCallback, useEffect, useRef, useState } from 'react';
import { ArrowsLeftRight } from '@phosphor-icons/react';
import type { BeforeAfterSliderProps } from '../types';

export default function BeforeAfterSlider({
  beforeSrc,
  afterSrc,
  beforeLabel = 'Original',
  afterLabel = 'Restored',
  className = '',
  aspectRatio = 'aspect-[4/3] md:aspect-[16/10]',
  autoAnimate = false,
}: BeforeAfterSliderProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState(50);
  const [isDragging, setIsDragging] = useState(false);
  const isInteractedRef = useRef(false);
  const animFrameRef = useRef<number | null>(null);

  // Auto-animation invite mode for landing page
  useEffect(() => {
    if (!autoAnimate || isInteractedRef.current) return;

    let startTime: number | null = null;
    const duration = 6000; // 6 seconds gentle oscillation

    const animate = (timestamp: number) => {
      if (isInteractedRef.current) return;
      if (!startTime) startTime = timestamp;
      const elapsed = timestamp - startTime;

      if (elapsed < duration) {
        // Gentle sinusoidal drift between 42% and 58%
        const drift = Math.sin((elapsed / duration) * Math.PI * 3) * 8;
        setPosition(50 + drift);
        animFrameRef.current = requestAnimationFrame(animate);
      } else {
        // Smoothly settle back to 50%
        setPosition(50);
      }
    };

    animFrameRef.current = requestAnimationFrame(animate);

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [autoAnimate]);

  const stopAutoAnimate = useCallback(() => {
    isInteractedRef.current = true;
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }
  }, []);

  const updatePosition = useCallback((clientX: number) => {
    const container = containerRef.current;
    if (!container) return;
    const rect = container.getBoundingClientRect();
    const x = clientX - rect.left;
    const pct = Math.max(0, Math.min(100, (x / rect.width) * 100));
    setPosition(pct);
  }, []);

  // Pointer event handlers (mouse + touch unified via Pointer Events API)
  const handlePointerDown = (e: React.PointerEvent) => {
    stopAutoAnimate();
    setIsDragging(true);
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
    updatePosition(e.clientX);
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isDragging) return;
    updatePosition(e.clientX);
  };

  const handlePointerUp = (e: React.PointerEvent) => {
    if (isDragging) {
      setIsDragging(false);
      try {
        (e.target as HTMLElement).releasePointerCapture(e.pointerId);
      } catch {
        // Ignored if capture already released
      }
    }
  };

  // Keyboard accessibility
  const handleKeyDown = (e: React.KeyboardEvent) => {
    stopAutoAnimate();
    if (e.key === 'ArrowLeft') {
      e.preventDefault();
      setPosition((p) => Math.max(0, p - 2));
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      setPosition((p) => Math.min(100, p + 2));
    } else if (e.key === 'Home') {
      e.preventDefault();
      setPosition(0);
    } else if (e.key === 'End') {
      e.preventDefault();
      setPosition(100);
    }
  };

  // Label opacity fades smoothly as handle approaches either side
  const originalOpacity = Math.max(0, Math.min(1, (position - 12) / 10));
  const restoredOpacity = Math.max(0, Math.min(1, (88 - position) / 10));

  return (
    <div
      ref={containerRef}
      role="slider"
      aria-label="Before and after image comparison slider"
      aria-valuenow={Math.round(position)}
      aria-valuemin={0}
      aria-valuemax={100}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
      className={`relative w-full ${aspectRatio} rounded-2xl overflow-hidden cursor-ew-resize select-none border border-black/10 dark:border-white/10 shadow-2xl bg-surface-subtle dark:bg-surface-dark group outline-none focus-visible:ring-2 focus-visible:ring-accent-sepia ${className}`}
    >
      {/* After Image (Restored) — Full Background */}
      <img
        src={afterSrc}
        alt={afterLabel}
        className="absolute inset-0 w-full h-full object-cover pointer-events-none select-none"
        loading="eager"
      />

      {/* Before Image (Original) — Clipped Polygon Overlay */}
      <div
        className="absolute inset-0 pointer-events-none select-none"
        style={{
          clipPath: `polygon(0 0, ${position}% 0, ${position}% 100%, 0 100%)`,
        }}
      >
        <img
          src={beforeSrc}
          alt={beforeLabel}
          className="absolute inset-0 w-full h-full object-cover pointer-events-none select-none"
          loading="eager"
        />
      </div>

      {/* Slider Divider Line */}
      <div
        className="absolute top-0 bottom-0 w-[2px] bg-white/70 dark:bg-white/40 shadow-[0_0_8px_rgba(0,0,0,0.4)] pointer-events-none z-20"
        style={{ left: `${position}%`, transform: 'translateX(-50%)' }}
      >
        {/* Handle Knob with Glassmorphism Treatment */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-10 h-10 rounded-full glass-panel flex items-center justify-center text-ink dark:text-white shadow-xl group-hover:scale-105 active:scale-95 transition-transform duration-150">
          <ArrowsLeftRight weight="bold" className="text-lg" />
        </div>
      </div>

      {/* Floating Original Label (Fades when handle nears left edge) */}
      <div
        className="absolute top-4 left-4 px-3 py-1.5 rounded-full glass-panel text-[11px] font-medium tracking-wider uppercase text-white shadow-sm pointer-events-none transition-opacity duration-200 z-10"
        style={{ opacity: originalOpacity }}
      >
        {beforeLabel}
      </div>

      {/* Floating Restored Label (Fades when handle nears right edge) */}
      <div
        className="absolute top-4 right-4 px-3 py-1.5 rounded-full glass-panel text-[11px] font-medium tracking-wider uppercase text-accent-sepia-light shadow-sm pointer-events-none transition-opacity duration-200 z-10"
        style={{ opacity: restoredOpacity }}
      >
        {afterLabel}
      </div>
    </div>
  );
}
