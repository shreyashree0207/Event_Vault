import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, Mail, UserRound } from 'lucide-react';
import { PageContainer } from '../components/layout/PageContainer';
import { Button } from '../components/common/Button';
import { authService } from '../services/authService';
import './AuthPages.css';

const GuestLoginForm = () => {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await authService.login(name, email);
      navigate('/events');
    } catch (err) {
      setError(err.message || 'Could not save your profile.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageContainer>
      <div className="ev-auth-card-container">
        <div className="ev-auth-card">
          <div className="ev-auth-brand-head">
            <ShieldCheck size={28} className="ev-auth-icon" />
            <h2>Welcome to Event Vault</h2>
            <p>Enter your full name and email address to continue.</p>
          </div>

          <div className="ev-guest-notice" role="note">
            This is guest/demo identification only. Your email is not verified,
            and this does not provide account security.
          </div>
          {error && <div className="ev-auth-error">{error}</div>}

          <form onSubmit={handleSubmit} className="ev-auth-form">
            <div className="ev-form-group">
              <label htmlFor="guest-name">Your Name</label>
              <div className="ev-input-icon-wrap">
                <UserRound size={16} className="ev-input-icon" />
                <input
                  id="guest-name"
                  type="text"
                  autoComplete="name"
                  maxLength={120}
                  required
                  placeholder="Alex Mercer"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
            </div>
            <div className="ev-form-group">
              <label htmlFor="guest-email">Email Address</label>
              <div className="ev-input-icon-wrap">
                <Mail size={16} className="ev-input-icon" />
                <input
                  id="guest-email"
                  type="email"
                  autoComplete="email"
                  maxLength={254}
                  required
                  placeholder="alex@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>

            <Button variant="primary" size="lg" isLoading={loading} className="ev-auth-submit-btn">
              Continue
            </Button>
          </form>

          <div className="ev-auth-footer-link">
            <span>Your guest session stays in this browser until you log out.</span>
          </div>
        </div>
      </div>
    </PageContainer>
  );
};

export const Login = () => <GuestLoginForm />;
export const Register = Login;
