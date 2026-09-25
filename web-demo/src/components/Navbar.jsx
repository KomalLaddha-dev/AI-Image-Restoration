import React from 'react';
import { Link, useLocation } from 'react-router-dom';

export default function Navbar() {
  const location = useLocation();

  const isActive = (path) => location.pathname === path ? 'active' : '';

  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand">
        <span className="icon">🏛️</span>
        Heritage Restore
      </Link>
      <ul className="navbar-links">
        <li><Link to="/" className={isActive('/')}>Home</Link></li>
        <li><Link to="/restore" className={isActive('/restore')}>Restore</Link></li>
        <li><Link to="/identify" className={isActive('/identify')}>Identify</Link></li>
      </ul>
    </nav>
  );
}
