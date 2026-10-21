import { apiClient } from './api';
import { clearSession, readSession, saveSession } from './sessionStorage';

export const authService = {
  async login(name, email) {
    const normalizedName = name.trim().replace(/\s+/g, ' ');
    const normalizedEmail = email.trim().toLowerCase();

    if (normalizedName.length < 2 || normalizedName.length > 120) {
      throw new Error('Enter your full name (2 to 120 characters).');
    }
    if (
      normalizedEmail.length > 254 ||
      !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(normalizedEmail)
    ) {
      throw new Error('Enter a valid email address.');
    }

    const result = await apiClient.post('/auth/login', {
      name: normalizedName,
      email: normalizedEmail,
    });
    saveSession({
      id: result.user.id,
      name: result.user.name,
      email: result.user.email,
      sessionId: result.user.sessionId,
      accessToken: result.accessToken,
    });
    return this.getCurrentUser();
  },

  getCurrentUser() {
    const session = readSession();
    if (!session) return null;
    return {
      id: session.id,
      name: session.name,
      email: session.email,
      sessionId: session.sessionId,
    };
  },

  logout() {
    clearSession();
    return Promise.resolve(true);
  },
};
