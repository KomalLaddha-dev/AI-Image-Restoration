import React from 'react';
import { ReactLenis } from '@studio-freight/react-lenis';
import Navbar from './Navbar';
import FilmGrain from './FilmGrain';

export default function Layout({ children }) {
  return (
    <ReactLenis root options={{ lerp: 0.05, smoothWheel: true }}>
      <div className="relative min-h-screen bg-bg-primary text-text-primary selection:bg-gold-500/30 selection:text-gold-100 font-sans">
        <FilmGrain />
        <Navbar />
        <main className="relative z-10 w-full flex flex-col">
          {children}
        </main>
      </div>
    </ReactLenis>
  );
}
