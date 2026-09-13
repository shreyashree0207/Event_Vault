import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { CheckCircle2, Ticket as TicketIcon, Calendar, MapPin, ArrowRight } from 'lucide-react';
import { PageContainer } from '../components/layout/PageContainer';
import { TicketStatus } from '../components/tickets/TicketStatus';
import { Button } from '../components/common/Button';
import { Loader, ErrorState } from '../components/common/Loader';
import { bookingService } from '../services/bookingService';
import { ticketService } from '../services/ticketService';
import './BookingConfirmation.css';

export const BookingConfirmation = () => {
  const { bookingId } = useParams();

  const [booking, setBooking] = useState(null);
  const [ticketStatusData, setTicketStatusData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStatus = async () => {
    try {
      const status = await ticketService.getTicketStatusForBooking(bookingId);
      setTicketStatusData(status);

      // Once ticket generation finishes, record generated tickets
      if (status.status === 'READY' && booking) {
        ticketService.addTicketsFromBooking(booking);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    let intervalId;

    const initConfirmation = async () => {
      setLoading(true);
      try {
        const bkData = await bookingService.getBookingById(bookingId);
        setBooking(bkData);

        const initialStatus = await ticketService.getTicketStatusForBooking(bookingId);
        setTicketStatusData(initialStatus);

        // Poll async ticket worker status until READY
        intervalId = setInterval(fetchStatus, 2500);
      } catch (err) {
        setError(err.message || 'Booking confirmation record missing.');
      } finally {
        setLoading(false);
      }
    };

    initConfirmation();

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [bookingId]);

  if (loading) return <PageContainer><Loader message="Verifying booking confirmation receipt..." /></PageContainer>;
  if (error || !booking) return <PageContainer><ErrorState title="Booking Record Error" message={error} /></PageContainer>;

  return (
    <PageContainer>
      <div className="ev-confirmation-page">
        <div className="ev-confirmation-hero">
          <CheckCircle2 size={56} className="ev-confirm-success-icon" />
          <h1 className="ev-confirm-title">✓ Booking Confirmed</h1>
          <p className="ev-confirm-id-tag">Reference ID: <strong>{booking.id}</strong></p>
        </div>

        {/* Async Ticket Status Component */}
        <TicketStatus ticketStatusData={ticketStatusData} onRetry={fetchStatus} />

        <div className="ev-receipt-card">
          <h3>Booking Summary Details</h3>

          <div className="ev-receipt-grid">
            <div className="ev-rcpt-item">
              <span className="ev-rcpt-label">Event</span>
              <strong className="ev-rcpt-val">{booking.eventName}</strong>
            </div>

            <div className="ev-rcpt-item">
              <span className="ev-rcpt-label">Date & Venue</span>
              <span className="ev-rcpt-val">{booking.eventDate} at {booking.venue}</span>
            </div>

            <div className="ev-rcpt-item">
              <span className="ev-rcpt-label">Reserved Seats</span>
              <span className="ev-rcpt-val">{booking.seats.join(', ')}</span>
            </div>

            <div className="ev-rcpt-item">
              <span className="ev-rcpt-label">Amount Paid</span>
              <strong className="ev-rcpt-val">${booking.totalAmount.toFixed(2)}</strong>
            </div>
          </div>
        </div>

        <div className="ev-confirm-actions">
          <Link to="/my-tickets">
            <Button variant="primary" size="lg">
              <TicketIcon size={18} />
              <span>View My Tickets</span>
              <ArrowRight size={18} />
            </Button>
          </Link>
        </div>
      </div>
    </PageContainer>
  );
};
