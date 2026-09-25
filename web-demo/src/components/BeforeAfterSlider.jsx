import React, { useCallback, useRef, useState, useEffect } from 'react';

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

  return (
    <div
      ref={containerRef}
      className="before-after-container"
      onMouseDown={handleMouseDown}
      onTouchMove={handleTouchMove}
      onTouchStart={() => setIsDragging(true)}
      onTouchEnd={() => setIsDragging(false)}
      style={{ aspectRatio: 'auto' }}
    >
      {/* After image (full width, background) */}
      <img src={afterSrc} alt="Restored" style={{ width: '100%' }} />

      {/* Before image (clipped) */}
      <div
        className="before-image-wrapper"
        style={{ width: `${position}%` }}
      >
        <img
          src={beforeSrc}
          alt="Original"
          style={{
            width: `${containerRef.current ? containerRef.current.offsetWidth : 800}px`,
            maxWidth: 'none',
          }}
        />
      </div>

      {/* Slider handle */}
      <div className="slider-handle" style={{ left: `${position}%` }}>
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '36px',
          height: '36px',
          borderRadius: '50%',
          background: 'var(--color-accent-gold)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '14px',
          color: '#0a0a0f',
          fontWeight: 'bold',
          boxShadow: '0 0 16px rgba(212, 168, 83, 0.6)',
        }}>
          ⟷
        </div>
      </div>

      {/* Labels */}
      <span className="slider-label before">Before</span>
      <span className="slider-label after">After</span>
    </div>
  );
}
