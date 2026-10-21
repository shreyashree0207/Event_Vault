import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, Phone, UserRound } from 'lucide-react';
import { PageContainer } from '../components/layout/PageContainer';
import { Button } from '../components/common/Button';
import { authService } from '../services/authService';
import './AuthPages.css';

const GuestLoginForm = () => {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [mobile, setMobile] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const normalizedMobile = mobile.trim().replace(/[\s().-]/g, '');
    if (
      name.trim().replace(/\s+/g, ' ').length < 2 ||
      !/^\+?\d{7,15}$/.test(normalizedMobile)
    ) {
      setError('Enter your full name and a valid mobile number (7–15 digits).');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await authService.login(name, normalizedMobile);
      navigate('/');
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
            <p>Enter your name and mobile number to continue.</p>
          </div>

          <div className="ev-guest-notice" role="note">
            This saves a simple guest profile in this browser. Your mobile
            number is not verified and this is not account authentication.
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
              <label htmlFor="guest-mobile">Mobile Number</label>
              <div className="ev-input-icon-wrap">
                <Phone size={16} className="ev-input-icon" />
                <input
                  id="guest-mobile"
                  type="tel"
                  autoComplete="tel"
                  inputMode="tel"
                  maxLength={24}
                  required
                  placeholder="+91 98765 43210"
                  value={mobile}
                  onChange={(e) => setMobile(e.target.value)}
                />
              </div>
            </div>

            <Button variant="primary" size="lg" isLoading={loading} className="ev-auth-submit-btn">
              Continue
            </Button>
          </form>

          <div className="ev-auth-footer-link">
            <span>Your profile stays in this browser until you log out.</span>
          </div>
        </div>
      </div>
    </PageContainer>
  );
};

export const Login = () => <GuestLoginForm />;
export const Register = Login;
