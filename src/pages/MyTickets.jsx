import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageContainer } from '../components/layout/PageContainer';
import { TicketCard } from '../components/tickets/TicketCard';
import { Loader, ErrorState } from '../components/common/Loader';
import { ticketService } from '../services/ticketService';
import { authService } from '../services/authService';
import './MyTickets.css';

export const MyTickets = () => {
  const navigate = useNavigate();
  const [tickets, setTickets] = useState([]);
  const [filter, setFilter] = useState('ALL'); // ALL, Upcoming, Completed, Cancelled
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchTickets = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await ticketService.getTicketsForUser();
      setTickets(data);
    } catch (err) {
      setError(err.message || 'Unable to retrieve tickets.');
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = async (ticket) => {
    try {
      await ticketService.retryTicketGeneration(ticket.bookingId);
      await fetchTickets();
    } catch (err) {
      setError(err.message || 'Ticket generation retry failed.');
    }
  };

  useEffect(() => {
    if (!authService.getCurrentUser()) {
      navigate('/login');
      return;
    }
    fetchTickets();
  }, [navigate]);

  return (
    <PageContainer>
      <div className="ev-tickets-page-header">
        <h1 className="ev-page-title">My Event Tickets</h1>
        <p className="ev-page-subtitle">Access your digital entry passes and barcode passes.</p>

        <div className="ev-ticket-filter-pills">
          {['ALL', 'Upcoming', 'Completed', 'Cancelled'].map(t => (
            <button
              key={t}
              className={`ev-tkt-filter-btn ${filter === t ? 'active' : ''}`}
              onClick={() => setFilter(t)}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <Loader message="Loading digital tickets..." />
      ) : error ? (
        <ErrorState title="Tickets unavailable" message={error} onRetry={fetchTickets} />
      ) : tickets.length === 0 ? (
        <div className="ev-empty-tickets-box">
          <p>No tickets found under your account.</p>
        </div>
      ) : (
        <div className="ev-tickets-list-grid">
          {tickets.map(ticket => (
            <TicketCard
              key={ticket.id}
              ticket={{
                ...ticket,
                onDownload: () => ticketService.downloadTicket(ticket.id),
              }}
              onRetry={handleRetry}
            />
          ))}
        </div>
      )}
    </PageContainer>
  );
};
