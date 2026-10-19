import { apiClient, USE_REAL_BACKEND } from './api';
import { generateMockSeats } from '../data/seats';
import { MOCK_INITIAL_BOOKINGS } from '../data/mockUser';

/**
 * Booking & Seat Service
 * Target endpoints:
 *  - GET /events/{event_id}/seats
 *  - POST /bookings
 *  - GET /bookings/{booking_id}
 */

const eventSeatsMap = new Map();
const userBookings = [...MOCK_INITIAL_BOOKINGS];

export const bookingService = {
  async getEventSeats(eventId) {
    if (USE_REAL_BACKEND) {
      return apiClient.get(`/events/${eventId}/seats`);
    }

    await new Promise(resolve => setTimeout(resolve, 400));

    if (!eventSeatsMap.has(eventId)) {
      eventSeatsMap.set(eventId, generateMockSeats(eventId));
    }
    return eventSeatsMap.get(eventId);
  },

  async acquireSeatLock(eventId, seatCode, sessionId = null) {
    if (!USE_REAL_BACKEND) {
      return { event_id: eventId, seat_code: seatCode, session_id: sessionId };
    }

    return apiClient.post('/seat-locks', {
      event_id: eventId,
      seat_code: seatCode,
      ...(sessionId ? { session_id: sessionId } : {})
    });
  },

  async releaseSeatLock(eventId, seatCode, sessionId) {
    if (!USE_REAL_BACKEND || !sessionId) {
      return;
    }

    return apiClient.delete('/seat-locks', {
      data: {
        event_id: eventId,
        seat_code: seatCode,
        session_id: sessionId
      }
    });
  },

  async createBooking(
    eventId,
    eventDetails,
    selectedSeatCodes,
    basePrice,
    sessionId = null
  ) {
    if (USE_REAL_BACKEND) {
      return apiClient.post('/bookings', {
        eventId,
        seatCodes: selectedSeatCodes,
        ...(sessionId ? { sessionId } : {})
      });
    }

    // Simulate backend payment verification and seat reservation validation
    await new Promise(resolve => setTimeout(resolve, 1200));

    const totalSeatsPrice = selectedSeatCodes.length * basePrice;
    const serviceFee = Math.round(totalSeatsPrice * 0.12 * 100) / 100;
    const totalAmount = Math.round((totalSeatsPrice + serviceFee) * 100) / 100;

    const newBooking = {
      id: `bk-${Math.floor(1000000 + Math.random() * 9000000)}`,
      userId: "usr-892341",
      eventId,
      eventName: eventDetails.name,
      eventDate: eventDetails.date,
      venue: eventDetails.venue,
      seats: selectedSeatCodes,
      ticketPrice: basePrice,
      serviceFee: serviceFee,
      totalAmount: totalAmount,
      paymentStatus: "PAID",
      bookingStatus: "CONFIRMED",
      createdAt: new Date().toISOString()
    };

    userBookings.unshift(newBooking);

    // Update seat status to UNAVAILABLE
    const currentSeats = eventSeatsMap.get(eventId) || [];
    const updatedSeats = currentSeats.map(seat => {
      if (selectedSeatCodes.includes(seat.code)) {
        return { ...seat, status: 'UNAVAILABLE' };
      }
      return seat;
    });
    eventSeatsMap.set(eventId, updatedSeats);

    return newBooking;
  },

  async getBookingById(bookingId) {
    if (USE_REAL_BACKEND) {
      return apiClient.get(`/bookings/${bookingId}`);
    }

    await new Promise(resolve => setTimeout(resolve, 300));
    const booking = userBookings.find(b => b.id === bookingId);
    if (!booking) {
      throw new Error(`Booking ID '${bookingId}' not found.`);
    }
    return booking;
  },

  async getUserBookings() {
    if (USE_REAL_BACKEND) {
      return apiClient.get('/user/bookings');
    }
    await new Promise(resolve => setTimeout(resolve, 300));
    return [...userBookings];
  }
};
