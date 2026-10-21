import React from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { ShieldCheck, Ticket, User, LogIn, LogOut } from 'lucide-react';
import { authService } from '../../services/authService';
import './Navbar.css';

export const Navbar = () => {
  const navigate = useNavigate();
  const user = authService.getCurrentUser();

  const handleLogout = () => {
    authService.logout();
    navigate('/');
  };

  return (
    <header className="ev-navbar-header">
      <div className="ev-navbar-container">
        <Link to="/" className="ev-brand">
          <div className="ev-brand__logo">
            <ShieldCheck className="ev-brand__icon" size={24} />
          </div>
          <div className="ev-brand__text">
            <span className="ev-brand__title">EVENT VAULT</span>
            <span className="ev-brand__tag">RESILIENT TICKETING</span>
          </div>
        </Link>

        <nav className="ev-nav-links">
          <NavLink to="/" end className={({ isActive }) => `ev-nav-item ${isActive ? 'active' : ''}`}>
            Home
          </NavLink>
          <NavLink to="/events" className={({ isActive }) => `ev-nav-item ${isActive ? 'active' : ''}`}>
            Events
          </NavLink>
          {user && (
            <NavLink to="/my-tickets" className={({ isActive }) => `ev-nav-item ${isActive ? 'active' : ''}`}>
              <Ticket size={16} />
              <span>My Tickets</span>
            </NavLink>
          )}
        </nav>

        <div className="ev-auth-actions">
          {user ? (
            <div className="ev-user-menu">
              <Link to="/profile" className="ev-user-profile-link">
                <User size={18} />
                <span className="ev-user-name">{user.name}</span>
              </Link>
              <button onClick={handleLogout} className="ev-logout-btn" title="Logout">
                <LogOut size={16} />
              </button>
            </div>
          ) : (
            <div className="ev-auth-btns">
              <Link to="/login" className="ev-btn-text">
                <LogIn size={16} />
                <span>Continue</span>
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
