import React from 'react';
import { Ticket, QrCode, Calendar, MapPin, Download } from 'lucide-react';
import { StatusBadge } from '../common/StatusBadge';
import { Button } from '../common/Button';
import './TicketCard.css';

export const TicketCard = ({ ticket }) => {
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
        <span className="ev-qr-subtext">Scan at Entrance</span>
        <Button variant="outline" size="sm" className="ev-download-btn">
          <Download size={14} />
          <span>Download PDF</span>
        </Button>
      </div>
    </div>
  );
};
