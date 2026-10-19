import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { PageContainer } from '../components/layout/PageContainer';
import { SeatMap } from '../components/booking/SeatMap';
import { BookingSummary } from '../components/booking/BookingSummary';
import { Loader, ErrorState } from '../components/common/Loader';
import { eventService } from '../services/eventService';
import { bookingService } from '../services/bookingService';
import './Booking.css';

export const Booking = () => {
  const { eventId } = useParams();
  const navigate = useNavigate();
  const sessionIdRef = useRef(window.crypto.randomUUID());
  const heldLocksRef = useRef(new Set());
  const pendingLocksRef = useRef(new Set());
  const activeEventIdRef = useRef(null);

  const [event, setEvent] = useState(null);
  const [seats, setSeats] = useState([]);
  const [selectedSeats, setSelectedSeats] = useState([]);
  const [step, setStep] = useState('SELECTION'); // SELECTION or CHECKOUT
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    activeEventIdRef.current = eventId;
    const heldLocks = heldLocksRef.current;
    const sessionId = sessionIdRef.current;

    const initBookingData = async () => {
      setLoading(true);
      try {
        const evData = await eventService.getEventById(eventId);
        setEvent(evData);

        const seatData = await bookingService.getEventSeats(eventId);
        setSeats(seatData);
      } catch (err) {
        setError(err.message || 'Seat map initialization failed.');
      } finally {
        setLoading(false);
      }
    };
    initBookingData();

    return () => {
      activeEventIdRef.current = null;

      for (const seatCode of heldLocks) {
        bookingService
          .releaseSeatLock(eventId, seatCode, sessionId)
          .catch(err => {
            console.warn(`Could not release lock for seat ${seatCode}:`, err);
          });
      }

      heldLocks.clear();
    };
  }, [eventId]);

  const handleToggleSeat = async (seatCode) => {
    setError(null);

    if (pendingLocksRef.current.has(seatCode)) {
      return;
    }

    if (heldLocksRef.current.has(seatCode)) {
      pendingLocksRef.current.add(seatCode);
      try {
        await bookingService.releaseSeatLock(
          eventId,
          seatCode,
          sessionIdRef.current
        );

        if (activeEventIdRef.current === eventId) {
          heldLocksRef.current.delete(seatCode);
          setSelectedSeats(prev => prev.filter(code => code !== seatCode));
        }
      } catch (err) {
        if (activeEventIdRef.current === eventId) {
          setError(err.message || `Could not release seat ${seatCode}.`);
        }
      } finally {
        pendingLocksRef.current.delete(seatCode);
      }

      return;
    }

    pendingLocksRef.current.add(seatCode);

    try {
      const lock = await bookingService.acquireSeatLock(
        eventId,
        seatCode,
        sessionIdRef.current
      );
      const lockSessionId = lock.session_id || sessionIdRef.current;
      sessionIdRef.current = lockSessionId;

      if (activeEventIdRef.current !== eventId) {
        try {
          await bookingService.releaseSeatLock(
            eventId,
            seatCode,
            lockSessionId
          );
        } catch (err) {
          console.warn(`Could not release lock for seat ${seatCode}:`, err);
        }
        return;
      }

      heldLocksRef.current.add(seatCode);
      setSelectedSeats(prev =>
        prev.includes(seatCode) ? prev : [...prev, seatCode]
      );
    } catch (err) {
      if (activeEventIdRef.current === eventId) {
        setError(
          err.response?.data?.detail ||
          err.message ||
          `Seat ${seatCode} could not be locked.`
        );
      }
    } finally {
      pendingLocksRef.current.delete(seatCode);
    }
  };

  const handleProceedToCheckout = () => {
    setStep('CHECKOUT');
  };

  const handleConfirmSimulatedPayment = async () => {
    setSubmitting(true);
    try {
      const newBooking = await bookingService.createBooking(
        eventId,
        event,
        selectedSeats,
        event.startingPrice,
        sessionIdRef.current
      );

      await Promise.all(
        [...heldLocksRef.current].map(seatCode =>
          bookingService
            .releaseSeatLock(eventId, seatCode, sessionIdRef.current)
            .catch(err => {
              console.warn(`Could not release lock for seat ${seatCode}:`, err);
            })
        )
      );
      heldLocksRef.current.clear();

      navigate(`/booking-confirmation/${newBooking.id}`);
    } catch (err) {
      setError(err.message || 'Payment simulation failed.');
      setSubmitting(false);
    }
  };

  if (loading) return <PageContainer><Loader message="Loading venue seat layout & locking state..." /></PageContainer>;
  if (error || !event) return <PageContainer><ErrorState title="Booking Session Error" message={error} /></PageContainer>;

  const subtotal = selectedSeats.length * event.startingPrice;
  const serviceFee = Math.round(subtotal * 0.12 * 100) / 100;
  const total = Math.round((subtotal + serviceFee) * 100) / 100;

  return (
    <PageContainer>
      <div className="ev-booking-page-header">
        <h1 className="ev-page-title">{event.name} - Seat Selection</h1>
        <p className="ev-page-subtitle">{event.venue} • {event.date} at {event.time}</p>
      </div>

      {step === 'SELECTION' ? (
        <div className="ev-booking-layout">
          <div className="ev-seatmap-section">
            <SeatMap
              seats={seats}
              selectedSeats={selectedSeats}
              onToggleSeat={handleToggleSeat}
            />
          </div>

          <div className="ev-summary-section">
            <BookingSummary
              event={event}
              selectedSeats={selectedSeats}
              onContinue={handleProceedToCheckout}
              isLoading={submitting}
            />
          </div>
        </div>
      ) : (
        <div className="ev-checkout-modal-container">
          <div className="ev-checkout-card">
            <h2>Review & Complete Booking</h2>
            <p className="ev-checkout-sub">Simulated Order Verification</p>

            <div className="ev-checkout-details">
              <div className="ev-chk-row">
                <span>Event:</span>
                <strong>{event.name}</strong>
              </div>
              <div className="ev-chk-row">
                <span>Venue & Date:</span>
                <strong>{event.venue} ({event.date})</strong>
              </div>
              <div className="ev-chk-row">
                <span>Selected Seats:</span>
                <strong>{selectedSeats.join(', ')}</strong>
              </div>
              <div className="ev-chk-row">
                <span>Tickets Subtotal:</span>
                <strong>${subtotal.toFixed(2)}</strong>
              </div>
              <div className="ev-chk-row">
                <span>Service Fee (12%):</span>
                <strong>${serviceFee.toFixed(2)}</strong>
              </div>
              <div className="ev-chk-row ev-chk-row--total">
                <span>Total Payment Required:</span>
                <strong>${total.toFixed(2)}</strong>
              </div>
            </div>

            <div className="ev-sim-payment-notice">
              ✓ Simulated Gateway Mode Active (No real funds will be charged)
            </div>

            <div className="ev-checkout-actions">
              <button 
                onClick={() => setStep('SELECTION')} 
                className="ev-btn-back-step"
                disabled={submitting}
              >
                Back to Seats
              </button>

              <button 
                onClick={handleConfirmSimulatedPayment} 
                className="ev-btn-pay-now"
                disabled={submitting}
              >
                {submitting ? 'Processing Booking...' : `Pay $${total.toFixed(2)} & Lock Seats`}
              </button>
            </div>
          </div>
        </div>
      )}
    </PageContainer>
  );
};
