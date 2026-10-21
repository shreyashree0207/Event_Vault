import { apiClient, USE_REAL_BACKEND } from './api';
import { MOCK_INITIAL_TICKETS } from '../data/mockUser';

/**
 * Ticket Service (Simulates background generation queue: RabbitMQ + Ticket Worker)
 * Target endpoints:
 *  - GET /tickets
 *  - GET /tickets/{ticket_id}
 *  - GET /bookings/{booking_id}/ticket-status
 */

const userTickets = [...MOCK_INITIAL_TICKETS];
const ticketGenerationProgress = new Map();

export const ticketService = {
  async getTicketStatusForBooking(bookingId) {
    if (USE_REAL_BACKEND) {
      return apiClient.get(`/bookings/${bookingId}/ticket-status`);
    }

    await new Promise(resolve => setTimeout(resolve, 300));

    let state = ticketGenerationProgress.get(bookingId);
    if (!state) {
      // Simulate RabbitMQ worker picking up the task
      state = {
        bookingId,
        status: "PROCESSING", // PROCESSING -> READY
        progress: 25,
        stepMessage: "Dispatched to worker queue (RabbitMQ)...",
        generatedAt: null
      };
      ticketGenerationProgress.set(bookingId, state);
    } else if (state.status === "PROCESSING") {
      state.progress += 35;
      if (state.progress >= 60 && state.progress < 90) {
        state.stepMessage = "Generating secure ticket payload & cryptographic signature...";
      } else if (state.progress >= 90) {
        state.progress = 100;
        state.status = "READY";
        state.stepMessage = "Ticket generated and notification queued.";
        state.generatedAt = new Date().toISOString();
      }
      ticketGenerationProgress.set(bookingId, state);
    }

    return { ...state };
  },

  async getTicketsForUser() {
    if (USE_REAL_BACKEND) {
      return apiClient.get('/tickets');
    }

    await new Promise(resolve => setTimeout(resolve, 400));
    return [...userTickets];
  },

  async downloadTicket(ticketId) {
    const blob = await apiClient.download(`/tickets/${ticketId}/download`);
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `event-vault-ticket-${ticketId}.pdf`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  },

  async retryTicketGeneration(bookingId) {
    return apiClient.post(`/tickets/bookings/${bookingId}/retry`, {});
  },

  addTicketsFromBooking(booking) {
    const createdTickets = booking.seats.map(seatCode => ({
      id: `tkt-${booking.id.replace('bk-', '')}-${seatCode}`,
      bookingId: booking.id,
      eventId: booking.eventId,
      eventName: booking.eventName,
      eventDate: booking.eventDate,
      venue: booking.venue,
      seat: seatCode,
      category: "Standard Reserved",
      ticketStatus: "READY",
      ticketUrl: `#`,
      qrCode: `EV-VAULT-AUTHENTICATED-SECURE-${booking.id}-${seatCode}`
    }));

    userTickets.unshift(...createdTickets);
    return createdTickets;
  }
};
