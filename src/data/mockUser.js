export const MOCK_USER = {
  id: "usr-892341",
  name: "Alex Mercer",
  email: "alex.mercer@vault-resilience.io",
  avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=250&q=80",
  createdAt: "2026-01-15"
};

export const MOCK_INITIAL_BOOKINGS = [
  {
    id: "bk-8829104",
    userId: "usr-892341",
    eventId: "evt-cyber-fest-2026",
    eventName: "Neon Horizon Cyber Music Festival",
    eventDate: "2026-10-15",
    venue: "Apex Arena",
    seats: ["A5", "A6"],
    totalAmount: 476.80,
    paymentStatus: "PAID",
    bookingStatus: "CONFIRMED",
    ticketStatus: "READY",
    createdAt: "2026-09-10T14:32:00Z"
  }
];

export const MOCK_INITIAL_TICKETS = [
  {
    id: "tkt-994102-A5",
    bookingId: "bk-8829104",
    eventId: "evt-cyber-fest-2026",
    eventName: "Neon Horizon Cyber Music Festival",
    eventDate: "2026-10-15",
    venue: "Apex Arena",
    seat: "A5",
    category: "VIP Front Row",
    ticketStatus: "READY",
    ticketUrl: "/tickets/tkt-994102-A5.pdf",
    qrCode: "EV-VAULT-AUTHENTICATED-SECURE-994102-A5"
  },
  {
    id: "tkt-994102-A6",
    bookingId: "bk-8829104",
    eventId: "evt-cyber-fest-2026",
    eventName: "Neon Horizon Cyber Music Festival",
    eventDate: "2026-10-15",
    venue: "Apex Arena",
    seat: "A6",
    category: "VIP Front Row",
    ticketStatus: "READY",
    ticketUrl: "/tickets/tkt-994102-A6.pdf",
    qrCode: "EV-VAULT-AUTHENTICATED-SECURE-994102-A6"
  }
];
