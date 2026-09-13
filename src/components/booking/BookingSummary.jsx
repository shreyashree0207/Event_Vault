import React from 'react';
import { Ticket, ArrowRight, Shield } from 'lucide-react';
import { Button } from '../common/Button';
import './BookingSummary.css';

export const BookingSummary = ({ event, selectedSeats, onContinue, isLoading }) => {
  const ticketCount = selectedSeats.length;
  const basePrice = event.startingPrice || 0;
  const subtotal = ticketCount * basePrice;
  const serviceFee = Math.round(subtotal * 0.12 * 100) / 100;
  const total = Math.round((subtotal + serviceFee) * 100) / 100;

  return (
    <div className="ev-booking-summary-card">
      <h3 className="ev-summary-title">Order Summary</h3>

      <div className="ev-summary-event">
        <h4>{event.name}</h4>
        <p>{event.venue} • {event.date}</p>
      </div>

      <div className="ev-selected-seats-box">
        <div className="ev-selected-label">
          <Ticket size={16} />
          <span>Selected Seats ({ticketCount})</span>
        </div>
        {ticketCount > 0 ? (
          <div className="ev-seat-pills">
            {selectedSeats.map(code => (
              <span key={code} className="ev-seat-pill">{code}</span>
            ))}
          </div>
        ) : (
          <p className="ev-no-seats-text">Please click on available seats in the map above to proceed.</p>
        )}
      </div>

      <div className="ev-price-breakdown">
        <div className="ev-price-row">
          <span>Tickets ({ticketCount} × ${basePrice.toFixed(2)})</span>
          <span>${subtotal.toFixed(2)}</span>
        </div>
        <div className="ev-price-row">
          <span>Service & Protection Fee</span>
          <span>${serviceFee.toFixed(2)}</span>
        </div>
        <div className="ev-price-row ev-price-row--total">
          <span>Total Amount</span>
          <span>${total.toFixed(2)}</span>
        </div>
      </div>

      <div className="ev-redis-notice">
        <Shield size={14} />
        <span>Atomic Seat Reservation Target: Redis 10-Minute Lock Engine</span>
      </div>

      <Button
        variant="primary"
        size="lg"
        disabled={ticketCount === 0}
        isLoading={isLoading}
        onClick={onContinue}
        className="ev-checkout-btn"
      >
        <span>Proceed to Checkout</span>
        <ArrowRight size={18} />
      </Button>
    </div>
  );
};
