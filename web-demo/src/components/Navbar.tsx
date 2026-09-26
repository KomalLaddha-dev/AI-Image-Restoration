import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Bank, Sun, Moon, List, X, Sparkle } from '@phosphor-icons/react';
import { useTheme } from '../context/ThemeContext';

export default function Navbar() {
  const location = useLocation();
  const { theme, toggleTheme } = useTheme();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { name: 'Gallery', path: '/' },
    { name: 'Restore', path: '/restore' },
    { name: 'Identify', path: '/identify' },
  ];

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-16 bg-canvas/85 dark:bg-canvas-dark/85 backdrop-blur-md border-b border-border-theme transition-colors duration-300">
      <div className="max-w-7xl mx-auto h-full px-6 md:px-12 flex items-center justify-between">
        {/* Brand Logo */}
        <Link
          to="/"
          className="flex items-center gap-2.5 font-heading text-lg md:text-xl font-bold tracking-tight text-ink dark:text-ink-dark hover:text-accent-sepia transition-colors"
        >
          <div className="w-8 h-8 rounded-lg bg-accent-sepia-faint border border-accent-sepia/25 flex items-center justify-center text-accent-sepia">
            <Bank weight="duotone" className="text-lg" />
          </div>
          <span>Heritage Restore</span>
        </Link>

        {/* Desktop Nav Items */}
        <nav className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => {
            const isActive = location.pathname === link.path;
            return (
              <Link
                key={link.path}
                to={link.path}
                className={`text-xs font-semibold uppercase tracking-widest transition-colors duration-200 relative py-1 ${
                  isActive
                    ? 'text-accent-sepia'
                    : 'text-ink-muted dark:text-ink-muted-dark hover:text-ink dark:hover:text-ink-dark'
                }`}
              >
                {link.name}
                {isActive && (
                  <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-accent-sepia rounded-full" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Right Action & Theme Toggle */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            className="w-9 h-9 rounded-lg border border-border-theme flex items-center justify-center text-ink-muted dark:text-ink-muted-dark hover:text-accent-sepia hover:border-accent-sepia/40 transition-colors"
          >
            {theme === 'dark' ? (
              <Sun weight="duotone" className="text-lg" />
            ) : (
              <Moon weight="duotone" className="text-lg" />
            )}
          </button>

          {/* Mobile Menu Button */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle navigation menu"
            className="md:hidden w-9 h-9 rounded-lg border border-border-theme flex items-center justify-center text-ink-muted dark:text-ink-muted-dark"
          >
            {mobileMenuOpen ? <X weight="bold" /> : <List weight="bold" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-canvas dark:bg-canvas-dark border-b border-border-theme px-6 py-4 flex flex-col gap-3 shadow-xl">
          {navLinks.map((link) => {
            const isActive = location.pathname === link.path;
            return (
              <Link
                key={link.path}
                to={link.path}
                onClick={() => setMobileMenuOpen(false)}
                className={`text-sm font-semibold uppercase tracking-wider py-2 transition-colors ${
                  isActive
                    ? 'text-accent-sepia'
                    : 'text-ink-muted dark:text-ink-muted-dark'
                }`}
              >
                {link.name}
              </Link>
            );
          })}
        </div>
      )}
    </header>
  );
}
