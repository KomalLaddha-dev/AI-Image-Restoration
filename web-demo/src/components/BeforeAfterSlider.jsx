import React, { useCallback, useRef, useState, useEffect } from 'react';
import { ArrowsLeftRight } from '@phosphor-icons/react';

export default function BeforeAfterSlider({ beforeSrc, afterSrc }) {
  const containerRef = useRef(null);
  const [position, setPosition] = useState(50);
  const [isDragging, setIsDragging] = useState(false);

  const updatePosition = useCallback((clientX) => {
    const container = containerRef.current;
    if (!container) return;
    const rect = container.getBoundingClientRect();
    const x = clientX - rect.left;
    const pct = Math.max(0, Math.min(100, (x / rect.width) * 100));
    setPosition(pct);
  }, []);

  const handleMouseDown = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
    updatePosition(e.clientX);
  }, [updatePosition]);

  const handleMouseMove = useCallback((e) => {
    if (!isDragging) return;
    updatePosition(e.clientX);
  }, [isDragging, updatePosition]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleTouchMove = useCallback((e) => {
    if (e.touches.length === 1) {
      updatePosition(e.touches[0].clientX);
    }
  }, [updatePosition]);

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

  // To fix image resizing, we need the natural aspect ratio of the image.
  // Using a container approach where both images overlay perfectly.

  return (
    <div
      ref={containerRef}
      className="relative w-full max-w-4xl mx-auto rounded-2xl overflow-hidden cursor-col-resize select-none shadow-[0_8px_32px_rgba(0,0,0,0.5)] border border-white/10 group"
      onMouseDown={handleMouseDown}
      onTouchMove={handleTouchMove}
      onTouchStart={() => setIsDragging(true)}
      onTouchEnd={() => setIsDragging(false)}
    >
      {/* After image (background) */}
      <img src={afterSrc} alt="Restored" className="w-full h-auto block pointer-events-none" />

      {/* Before image (clipped) */}
      <div
        className="absolute top-0 left-0 h-full overflow-hidden"
        style={{ width: `${position}%` }}
      >
        <img
          src={beforeSrc}
          alt="Original"
          className="absolute top-0 left-0 h-full max-w-none pointer-events-none"
          style={{ width: containerRef.current ? `${containerRef.current.offsetWidth}px` : '100vw' }}
        />
      </div>

      {/* Slider handle */}
      <div 
        className="absolute top-0 bottom-0 w-1 bg-gold-500 shadow-[0_0_12px_rgba(212,168,83,0.8)] z-10" 
        style={{ left: `${position}%`, transform: 'translateX(-50%)' }}
      >
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-10 h-10 bg-gold-500 rounded-full flex items-center justify-center text-black shadow-[0_0_20px_rgba(212,168,83,0.8)] transition-transform duration-200">
          <ArrowsLeftRight weight="bold" className="text-xl" />
        </div>
      </div>

      {/* Labels */}
      <div className="absolute bottom-4 left-4 px-3 py-1 bg-black/60 backdrop-blur-md rounded-md text-xs font-semibold uppercase tracking-wider text-white/70">
        Before
      </div>
      <div className="absolute bottom-4 right-4 px-3 py-1 bg-black/60 backdrop-blur-md rounded-md text-xs font-semibold uppercase tracking-wider text-gold-400">
        After
      </div>
    </div>
  );
}
