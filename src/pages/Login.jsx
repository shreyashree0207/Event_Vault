import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ShieldCheck, Mail, Lock } from 'lucide-react';
import { PageContainer } from '../components/layout/PageContainer';
import { Button } from '../components/common/Button';
import { authService } from '../services/authService';
import './AuthPages.css';

export const Login = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('alex.mercer@vault-resilience.io');
  const [password, setPassword] = useState('password123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await authService.login(email, password);
      navigate('/events');
    } catch (err) {
      setError(err.message || 'Invalid credentials.');
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
            <h2>Sign In to Event Vault</h2>
            <p>Access your ticket wallet and reserve seats</p>
          </div>

          {error && <div className="ev-auth-error">{error}</div>}

          <form onSubmit={handleSubmit} className="ev-auth-form">
            <div className="ev-form-group">
              <label>Email Address</label>
              <div className="ev-input-icon-wrap">
                <Mail size={16} className="ev-input-icon" />
                <input
                  type="email"
                  required
                  placeholder="name@domain.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>

            <div className="ev-form-group">
              <label>Password</label>
              <div className="ev-input-icon-wrap">
                <Lock size={16} className="ev-input-icon" />
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>

            <Button variant="primary" size="lg" isLoading={loading} className="ev-auth-submit-btn">
              Sign In
            </Button>
          </form>

          <div className="ev-auth-footer-link">
            <span>Don't have an account?</span>
            <Link to="/register">Create an account</Link>
          </div>
        </div>
      </div>
    </PageContainer>
  );
};

export const Register = () => {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await authService.register(name, email, password);
      navigate('/events');
    } catch (err) {
      setError(err.message || 'Registration failed.');
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
            <h2>Create Event Vault Account</h2>
            <p>Register for high-demand ticket drops</p>
          </div>

          {error && <div className="ev-auth-error">{error}</div>}

          <form onSubmit={handleSubmit} className="ev-auth-form">
            <div className="ev-form-group">
              <label>Full Name</label>
              <input
                type="text"
                required
                placeholder="Alex Mercer"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="ev-plain-input"
              />
            </div>

            <div className="ev-form-group">
              <label>Email Address</label>
              <input
                type="email"
                required
                placeholder="name@domain.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="ev-plain-input"
              />
            </div>

            <div className="ev-form-group">
              <label>Password</label>
              <input
                type="password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="ev-plain-input"
              />
            </div>

            <div className="ev-form-group">
              <label>Confirm Password</label>
              <input
                type="password"
                required
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="ev-plain-input"
              />
            </div>

            <Button variant="primary" size="lg" isLoading={loading} className="ev-auth-submit-btn">
              Register Account
            </Button>
          </form>

          <div className="ev-auth-footer-link">
            <span>Already have an account?</span>
            <Link to="/login">Sign in</Link>
          </div>
        </div>
      </div>
    </PageContainer>
  );
};
