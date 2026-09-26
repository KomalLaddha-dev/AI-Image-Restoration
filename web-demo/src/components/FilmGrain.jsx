import React from 'react';

export default function FilmGrain() {
  return (
    <div 
      className="pointer-events-none fixed inset-0 z-[9999] mix-blend-overlay"
      style={{
        backgroundImage: `url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAYAAADDPmHLAAACJ0lEQVR4nO3dy27bMBBF0X//oxf9gC5E+gG9EBAgQIAAAQIEcIqP9wD/4tA6rOq4HAAzR6L8Y5QAAAABJRU5ErkJggg==")`,
        backgroundRepeat: 'repeat',
        opacity: 0.1,
      }}
    />
  );
}
