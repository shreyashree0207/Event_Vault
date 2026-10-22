const SESSION_STORAGE_KEY = 'ev_user';

export function readSession() {
  try {
    const session = JSON.parse(localStorage.getItem(SESSION_STORAGE_KEY) || 'null');
    return session && typeof session.accessToken === 'string' &&
      typeof session.id === 'number' &&
      typeof session.name === 'string' &&
      typeof session.email === 'string' &&
      typeof session.sessionId === 'string'
      ? session
      : null;
  } catch {
    return null;
  }
}

export function saveSession(session) {
  localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
}

export function clearSession() {
  localStorage.removeItem(SESSION_STORAGE_KEY);
}
