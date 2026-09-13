import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, Users, Lock, Cpu, RefreshCw, ArrowRight } from 'lucide-react';
import { PageContainer } from '../components/layout/PageContainer';
import { Button } from '../components/common/Button';
import './Home.css';

export const Home = () => {
  return (
    <PageContainer>
      {/* Hero Section */}
      <section className="ev-hero-section">
        <div className="ev-hero-badge">
          <ShieldCheck size={16} />
          <span>RESILIENT CLOUD-NATIVE TICKETING INFRASTRUCTURE</span>
        </div>

        <h1 className="ev-hero-title">
          Control the Crowd. <br />
          <span className="ev-gradient-text">Protect the Booking.</span> <br />
          Recover from Failure.
        </h1>

        <p className="ev-hero-subtitle">
          Event Vault provides controlled admission, reliable seat locking, and resilient ticket processing during high-demand events.
        </p>

        <div className="ev-hero-actions">
          <Link to="/events">
            <Button variant="primary" size="lg">
              <span>Explore Events</span>
              <ArrowRight size={18} />
            </Button>
          </Link>

          <a href="#how-it-works">
            <Button variant="secondary" size="lg">
              How It Works
            </Button>
          </a>
        </div>
      </section>

      {/* Value Proposition Grid */}
      <section id="how-it-works" className="ev-features-section">
        <div className="ev-section-header">
          <h2>Platform Resilience Architecture</h2>
          <p>Engineered to withstand massive traffic spikes and downstream system failures.</p>
        </div>

        <div className="ev-features-grid">
          <div className="ev-feature-card">
            <div className="ev-feature-icon">
              <Users size={24} />
            </div>
            <h3>High-Demand Ready</h3>
            <p>The platform is designed for sudden traffic spikes during major ticket drops without degrading core services.</p>
          </div>

          <div className="ev-feature-card">
            <div className="ev-feature-icon">
              <RefreshCw size={24} />
            </div>
            <h3>Controlled Admission</h3>
            <p>Users enter a virtual waiting room before accessing the booking system to ensure stable throughput.</p>
          </div>

          <div className="ev-feature-card">
            <div className="ev-feature-icon">
              <Lock size={24} />
            </div>
            <h3>Protected Booking</h3>
            <p>Seat locking prevents multiple users from successfully booking the exact same seat simultaneously.</p>
          </div>

          <div className="ev-feature-card">
            <div className="ev-feature-icon">
              <Cpu size={24} />
            </div>
            <h3>Reliable Processing</h3>
            <p>Ticket generation and notifications are processed asynchronously, decoupled from the core transaction.</p>
          </div>

          <div className="ev-feature-card ev-feature-card--wide">
            <div className="ev-feature-icon">
              <ShieldCheck size={24} />
            </div>
            <h3>Failure Recovery</h3>
            <p>The platform is designed so that failure of a downstream service does not automatically destroy a successful booking.</p>
          </div>
        </div>
      </section>
    </PageContainer>
  );
};
