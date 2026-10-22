import React, { useState } from 'react';
import { Ticket, QrCode, Calendar, MapPin, Download } from 'lucide-react';
import { StatusBadge } from '../common/StatusBadge';
import { Button } from '../common/Button';
import './TicketCard.css';

export const TicketCard = ({ ticket, onRetry }) => {
  const [error, setError] = useState(null);

  const handleDownload = async () => {
    setError(null);
    try {
      await ticket.onDownload();
    } catch (err) {
      setError(err.message || 'Ticket download failed.');
    }
  };

  return (
    <div className="ev-ticket-card">
      <div className="ev-ticket-stub">
        <div className="ev-ticket-header">
          <span className="ev-ticket-id">{ticket.id}</span>
          <StatusBadge status={ticket.ticketStatus} />
        </div>

        <h3 className="ev-ticket-event-name">{ticket.eventName}</h3>

        <div className="ev-ticket-details-grid">
          <div className="ev-tkt-info">
            <Calendar size={14} />
            <span>{ticket.eventDate}</span>
          </div>
          <div className="ev-tkt-info">
            <MapPin size={14} />
            <span>{ticket.venue}</span>
          </div>
          <div className="ev-tkt-info ev-tkt-info--seat">
            <Ticket size={14} />
            <span>Seat <strong>{ticket.seat}</strong> ({ticket.category || 'Standard'})</span>
          </div>
        </div>
      </div>

      <div className="ev-ticket-qr-section">
        <div className="ev-qr-box">
          <QrCode size={70} className="ev-qr-icon" />
        </div>
        <span className="ev-qr-subtext">{ticket.ticketCode || 'Ticket processing'}</span>
        {ticket.ticketStatus === 'READY' && (
          <Button
            variant="outline"
            size="sm"
            className="ev-download-btn"
            onClick={handleDownload}
          >
            <Download size={14} />
            <span>Download PDF</span>
          </Button>
        )}
        {ticket.ticketStatus === 'FAILED' && onRetry && (
          <Button variant="secondary" size="sm" onClick={() => onRetry(ticket)}>
            Retry ticket
          </Button>
        )}
        {ticket.ticketStatus !== 'READY' && ticket.ticketStatus !== 'FAILED' && (
          <span className="ev-qr-subtext">Ticket is being generated</span>
        )}
        {error && <span role="alert" className="ev-ticket-error">{error}</span>}
      </div>
    </div>
  );
};
