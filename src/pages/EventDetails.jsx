import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Calendar, MapPin, ShieldAlert, Ticket, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { PageContainer } from '../components/layout/PageContainer';
import { Button } from '../components/common/Button';
import { StatusBadge } from '../components/common/StatusBadge';
import { Loader, ErrorState } from '../components/common/Loader';
import { eventService } from '../services/eventService';
import './EventDetails.css';

export const EventDetails = () => {
  const { eventId } = useParams();
  const navigate = useNavigate();

  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchEvent = async () => {
      setLoading(true);
      try {
        const data = await eventService.getEventById(eventId);
        setEvent(data);
      } catch (err) {
        setError(err.message || 'Event details not found.');
      } finally {
        setLoading(false);
      }
    };
    fetchEvent();
  }, [eventId]);

  const handleBookTickets = () => {
    if (event.isHighDemand) {
      navigate(`/waiting-room/${event.id}`);
    } else {
      navigate(`/booking/${event.id}`);
    }
  };

  if (loading) return <PageContainer><Loader message="Fetching event details..." /></PageContainer>;
  if (error || !event) return <PageContainer><ErrorState title="Event Not Found" message={error} /></PageContainer>;

  return (
    <PageContainer>
      <Link to="/events" className="ev-back-link">
        <ArrowLeft size={16} />
        <span>Back to Events</span>
      </Link>

      <div className="ev-event-details-hero">
        <div className="ev-event-banner-container">
          <img src={event.image} alt={event.name} className="ev-event-banner-img" />
          <div className="ev-banner-overlay"></div>
          <div className="ev-banner-badge">
            <StatusBadge status={event.status} />
          </div>
        </div>

        <div className="ev-details-header">
          <div className="ev-details-meta-cat">{event.category}</div>
          <h1 className="ev-details-title">{event.name}</h1>

          <div className="ev-details-meta-grid">
            <div className="ev-meta-block">
              <Calendar size={18} className="ev-meta-icon" />
              <div>
                <span className="ev-meta-label">Date & Time</span>
                <span className="ev-meta-value">{event.date} • {event.time}</span>
              </div>
            </div>

            <div className="ev-meta-block">
              <MapPin size={18} className="ev-meta-icon" />
              <div>
                <span className="ev-meta-label">Venue</span>
                <span className="ev-meta-value">{event.venue}, {event.location}</span>
              </div>
            </div>

            <div className="ev-meta-block">
              <Ticket size={18} className="ev-meta-icon" />
              <div>
                <span className="ev-meta-label">Starting Price</span>
                <span className="ev-meta-value">${event.startingPrice.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="ev-details-content-grid">
        <div className="ev-details-main">
          <h3>About the Event</h3>
          <p className="ev-event-desc">{event.description}</p>

          {/* High Demand Warning Notice */}
          <div className="ev-high-demand-alert-box">
            <div className="ev-hd-alert-icon">
              <ShieldAlert size={24} />
            </div>
            <div>
              <h4>Controlled High Demand Admission Enabled</h4>
              <p>
                To protect system stability and ensure fair access, this event utilizes Event Vault Virtual Waiting Rooms during peak demand traffic.
              </p>
            </div>
          </div>
        </div>

        <div className="ev-details-sidebar">
          <div className="ev-booking-action-card">
            <div className="ev-price-tag">
              <span className="ev-price-sub">Starting from</span>
              <span className="ev-price-main">${event.startingPrice.toFixed(2)}</span>
            </div>

            <div className="ev-avail-info">
              <CheckCircle2 size={14} className="ev-check-icon" />
              <span>{event.availableSeats} seats remaining in allocation</span>
            </div>

            <Button variant="primary" size="lg" onClick={handleBookTickets} className="ev-book-now-btn">
              {event.isHighDemand ? "Enter Waiting Room & Book" : "Select Seats & Book"}
            </Button>
          </div>
        </div>
      </div>
    </PageContainer>
  );
};
