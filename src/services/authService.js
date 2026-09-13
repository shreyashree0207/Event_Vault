import { apiClient, USE_REAL_BACKEND } from './api';
import { MOCK_USER } from '../data/mockUser';

/**
 * Isolated Authentication Service
 * Target endpoints:
 *  - POST /auth/register
 *  - POST /auth/login
 */

let currentUser = MOCK_USER;

export const authService = {
  async login(email, password) {
    if (USE_REAL_BACKEND) {
      return apiClient.post('/auth/login', { email, password });
    }
    
    // Simulated Authentication Delay
    await new Promise(resolve => setTimeout(resolve, 600));

    if (!email || !password) {
      throw new Error("Email and password are required.");
    }

    currentUser = {
      ...MOCK_USER,
      email: email,
      name: email.split('@')[0].replace('.', ' ')
    };
    localStorage.setItem('ev_user', JSON.stringify(currentUser));
    return currentUser;
  },

  async register(name, email, password) {
    if (USE_REAL_BACKEND) {
      return apiClient.post('/auth/register', { name, email, password });
    }

    await new Promise(resolve => setTimeout(resolve, 700));

    currentUser = {
      id: `usr-${Math.floor(100000 + Math.random() * 900000)}`,
      name,
      email,
      avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=250&q=80",
      createdAt: new Date().toISOString().split('T')[0]
    };
    localStorage.setItem('ev_user', JSON.stringify(currentUser));
    return currentUser;
  },

  getCurrentUser() {
    const stored = localStorage.getItem('ev_user');
    if (stored) {
      try { return JSON.parse(stored); } catch { return MOCK_USER; }
    }
    return currentUser;
  },

  logout() {
    localStorage.removeItem('ev_user');
    currentUser = null;
    return Promise.resolve(true);
  }
};
