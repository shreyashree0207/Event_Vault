import React from 'react';
import { ShieldCheck, Server, Cpu } from 'lucide-react';
import './Footer.css';

export const Footer = () => {
  return (
    <footer className="ev-footer">
      <div className="ev-footer-container">
        <div className="ev-footer-brand">
          <div className="ev-footer-title">
            <ShieldCheck size={20} className="ev-footer-icon" />
            <span>EVENT VAULT</span>
          </div>
          <p className="ev-footer-tagline">
            Control the Crowd. Protect the Booking. Recover from Failure.
          </p>
          <div className="ev-arch-badge">
            <Server size={14} />
            <span>Cloud-Native Event Infrastructure Target: FastAPI • PostgreSQL • Redis • RabbitMQ</span>
          </div>
        </div>

        <div className="ev-footer-col">
          <h4>Architecture</h4>
          <ul>
            <li>Controlled Admission Queue</li>
            <li>Atomic Seat Locking</li>
            <li>Async Ticket Generation</li>
            <li>Distributed Resilience</li>
          </ul>
        </div>

        <div className="ev-footer-col">
          <h4>Platform</h4>
          <ul>
            <li><a href="/events">Explore Events</a></li>
            <li><a href="/my-tickets">My Tickets</a></li>
            <li><a href="/login">User Access</a></li>
          </ul>
        </div>
      </div>
      <div className="ev-footer-bottom">
        <p>© 2026 Event Vault Inc. Resilient High-Demand Event Ticketing Architecture.</p>
      </div>
    </footer>
  );
};
