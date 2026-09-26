import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Bank, Image, Target } from '@phosphor-icons/react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) {
  return twMerge(clsx(inputs));
}

export default function Navbar() {
  const location = useLocation();

  const navItems = [
    { name: 'Home', path: '/' },
    { name: 'Restore', path: '/restore' },
    { name: 'Identify', path: '/identify' },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 px-6 py-4 bg-bg-primary/80 backdrop-blur-xl border-b border-white/5 flex items-center justify-between">
      <Link to="/" className="flex items-center gap-3 font-serif text-xl font-bold text-gold-500 tracking-tight hover:text-gold-400 transition-colors">
        <Bank weight="duotone" className="text-2xl" />
        <span>Heritage Restore</span>
      </Link>
      
      <ul className="flex items-center gap-8">
        {navItems.map((item) => (
          <li key={item.name}>
            <Link 
              to={item.path} 
              className={cn(
                "text-sm font-medium tracking-wide uppercase transition-colors duration-200",
                location.pathname === item.path 
                  ? "text-gold-500" 
                  : "text-dark-300 hover:text-gold-400"
              )}
            >
              {item.name}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
