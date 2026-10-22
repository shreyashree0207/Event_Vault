import { apiClient, USE_REAL_BACKEND } from './api';
import { authService } from './authService';

/**
 * Waiting Room Service (Stateful queue simulation for high-demand events)
 * Target endpoints:
 *  - POST /waiting-room/{event_id}/join
 *  - GET /waiting-room/{event_id}/status
 */

const sessionQueueMap = new Map();
const ADMISSION_STORAGE_PREFIX = 'ev_admission:';

function admissionStorageKey(eventId) {
  const sessionId = authService.getCurrentUser()?.sessionId;
  return sessionId
    ? `${ADMISSION_STORAGE_PREFIX}${eventId}:${sessionId}`
    : null;
}

function rememberAdmission(eventId, queueState) {
  const key = admissionStorageKey(eventId);
  if (!key) return queueState;

  if (queueState.status === 'ADMITTED' && queueState.admittedToken) {
    sessionStorage.setItem(key, queueState.admittedToken);
  } else if (['EXPIRED', 'COMPLETED'].includes(queueState.status)) {
    sessionStorage.removeItem(key);
  }
  return queueState;
}

export const waitingRoomService = {
  async joinWaitingRoom(eventId) {
    if (USE_REAL_BACKEND) {
      const status = await apiClient.post(`/waiting-room/${eventId}/join`, {});
      return rememberAdmission(eventId, status);
    }

    await new Promise(resolve => setTimeout(resolve, 500));

    if (!sessionQueueMap.has(eventId)) {
      const initialUsersAhead = Math.floor(180 + Math.random() * 250);
      sessionQueueMap.set(eventId, {
        eventId,
        usersAhead: initialUsersAhead,
        position: initialUsersAhead + 1,
        estimatedWaitSeconds: Math.ceil(initialUsersAhead * 0.4),
        status: "WAITING", // WAITING, ADMITTED, EXPIRED
        joinedAt: Date.now()
      });
    }

    return sessionQueueMap.get(eventId);
  },

  async getQueueStatus(eventId) {
    if (USE_REAL_BACKEND) {
      const status = await apiClient.get(`/waiting-room/${eventId}/status`);
      return rememberAdmission(eventId, status);
    }

    await new Promise(resolve => setTimeout(resolve, 200));

    let queue = sessionQueueMap.get(eventId);
    if (!queue) {
      return this.joinWaitingRoom(eventId);
    }

    // Simulate steady queue advancement
    if (queue.status === "WAITING") {
      const decrement = Math.floor(15 + Math.random() * 25);
      queue.usersAhead = Math.max(0, queue.usersAhead - decrement);
      queue.position = queue.usersAhead + 1;
      queue.estimatedWaitSeconds = Math.ceil(queue.usersAhead * 0.35);

      if (queue.usersAhead === 0) {
        queue.status = "ADMITTED";
        queue.admittedToken = `ADMIT-TOKEN-${eventId}-${Math.random().toString(36).substring(2, 9).toUpperCase()}`;
        queue.expiresAt = Date.now() + 10 * 60 * 1000; // 10 min window
      }
    }

    sessionQueueMap.set(eventId, queue);
    return { ...queue };
  },

  resetQueue(eventId) {
    sessionQueueMap.delete(eventId);
  },

  getAdmissionToken(eventId) {
    const key = admissionStorageKey(eventId);
    return key ? sessionStorage.getItem(key) : null;
  },

  clearAdmissionToken(eventId) {
    const key = admissionStorageKey(eventId);
    if (key) sessionStorage.removeItem(key);
  }
};
