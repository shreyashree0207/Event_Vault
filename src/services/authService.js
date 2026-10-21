const USER_STORAGE_KEY = 'ev_user';

function clearSession() {
  localStorage.removeItem(USER_STORAGE_KEY);
}

export const authService = {
  async login(name, mobile) {
    const normalizedName = name.trim().replace(/\s+/g, ' ');
    const normalizedMobile = mobile.trim().replace(/[\s().-]/g, '');

    if (normalizedName.length < 2) {
      throw new Error('Enter your full name.');
    }
    if (!/^\+?\d{7,15}$/.test(normalizedMobile)) {
      throw new Error('Enter a valid mobile number with 7 to 15 digits.');
    }

    const user = {
      id: globalThis.crypto?.randomUUID?.()
        || `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      name: normalizedName,
      mobile: normalizedMobile,
    };
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
    return user;
  },

  getCurrentUser() {
    const stored = localStorage.getItem(USER_STORAGE_KEY);
    if (!stored) {
      return null;
    }

    try {
      const user = JSON.parse(stored);
      return user && user.id && user.name && user.mobile
        ? user
        : null;
    } catch {
      clearSession();
      return null;
    }
  },

  logout() {
    clearSession();
    return Promise.resolve(true);
  },
};
