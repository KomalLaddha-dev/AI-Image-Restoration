import React from 'react';
import { ReactLenis } from '@studio-freight/react-lenis';
import Navbar from './Navbar';
import { ThemeProvider } from '../context/ThemeContext';

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <ReactLenis root options={{ lerp: 0.08, smoothWheel: true }}>
        <div className="min-h-screen bg-canvas dark:bg-canvas-dark text-ink dark:text-ink-dark flex flex-col font-body transition-colors duration-300">
          <Navbar />
          <main className="flex-1 w-full pt-16 flex flex-col">{children}</main>

          {/* Minimal Gallery Footer */}
          <footer className="w-full border-t border-border-theme py-10 px-6 md:px-12 bg-canvas dark:bg-canvas-dark text-xs text-ink-muted dark:text-ink-muted-dark transition-colors duration-300">
            <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
              <p className="font-heading font-medium tracking-wide">
                Heritage Restore — AI Historical Reconstruction & Monument Provenance
              </p>
              <div className="flex items-center gap-6">
                <span>5-Stage Neural Pipeline</span>
                <span>•</span>
                <span>Grounded RAG Verification</span>
              </div>
            </div>
          </footer>
        </div>
      </ReactLenis>
    </ThemeProvider>
  );
}
