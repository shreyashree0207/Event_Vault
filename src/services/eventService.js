import { apiClient, USE_REAL_BACKEND } from './api';
import { MOCK_EVENTS } from '../data/events';

/**
 * Event Service
 * Target endpoints:
 *  - GET /events
 *  - GET /events/{event_id}
 */

export const eventService = {
  async getEvents({ search = '', category = '', date = '', location = '' } = {}) {
    if (USE_REAL_BACKEND) {
      const query = new URLSearchParams({ search, category, date, location }).toString();
      return apiClient.get(`/events?${query}`);
    }

    // Simulate network response latency
    await new Promise(resolve => setTimeout(resolve, 400));

    let events = [...MOCK_EVENTS];

    if (search) {
      const q = search.toLowerCase();
      events = events.filter(e => e.name.toLowerCase().includes(q) || e.description.toLowerCase().includes(q) || e.venue.toLowerCase().includes(q));
    }

    if (category && category !== 'All') {
      events = events.filter(e => e.category.toLowerCase() === category.toLowerCase());
    }

    if (location) {
      events = events.filter(e => e.location.toLowerCase().includes(location.toLowerCase()));
    }

    if (date) {
      events = events.filter(e => e.date >= date);
    }

    return events;
  },

  async getEventById(eventId) {
    if (USE_REAL_BACKEND) {
      return apiClient.get(`/events/${eventId}`);
    }

    await new Promise(resolve => setTimeout(resolve, 300));
    const event = MOCK_EVENTS.find(e => e.id === eventId);
    if (!event) {
      throw new Error(`Event with ID '${eventId}' not found.`);
    }
    return event;
  }
};
