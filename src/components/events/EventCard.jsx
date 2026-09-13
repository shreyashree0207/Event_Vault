import React from 'react';
import { Link } from 'react-router-dom';
import { Calendar, MapPin, Ticket, ShieldAlert } from 'lucide-react';
import { StatusBadge } from '../common/StatusBadge';
import { Button } from '../common/Button';
import './EventCard.css';

export const EventCard = ({ event }) => {
  return (
    <div className="ev-event-card">
      <div className="ev-event-card__media">
        <img src={event.image} alt={event.name} className="ev-event-card__img" />
        <div className="ev-event-card__badge">
          <StatusBadge status={event.status} />
        </div>
        {event.isHighDemand && (
          <div className="ev-event-card__high-demand">
            <ShieldAlert size={14} />
            <span>High Demand Event</span>
          </div>
        )}
      </div>

      <div className="ev-event-card__content">
        <div className="ev-event-card__category">{event.category}</div>
        <h3 className="ev-event-card__title">{event.name}</h3>

        <div className="ev-event-card__details">
          <div className="ev-detail-item">
            <Calendar size={14} />
            <span>{event.date} • {event.time}</span>
          </div>
          <div className="ev-detail-item">
            <MapPin size={14} />
            <span>{event.venue}, {event.location}</span>
          </div>
        </div>

        <div className="ev-event-card__footer">
          <div className="ev-event-card__price-box">
            <span className="ev-price-label">From</span>
            <span className="ev-price-val">${event.startingPrice.toFixed(2)}</span>
          </div>
          <Link to={`/events/${event.id}`}>
            <Button variant="primary" size="sm">
              View Event
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
};
