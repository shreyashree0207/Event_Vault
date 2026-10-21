import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ShieldCheck, ArrowRight, Activity } from 'lucide-react';
import { PageContainer } from '../components/layout/PageContainer';
import { QueueStatus } from '../components/waiting-room/QueueStatus';
import { QueueProgress } from '../components/waiting-room/QueueProgress';
import { Button } from '../components/common/Button';
import { Loader, ErrorState } from '../components/common/Loader';
import { waitingRoomService } from '../services/waitingRoomService';
import { eventService } from '../services/eventService';
import { authService } from '../services/authService';
import './WaitingRoom.css';

export const WaitingRoom = () => {
  const { eventId } = useParams();
  const navigate = useNavigate();

  const [event, setEvent] = useState(null);
  const [queueState, setQueueState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const intervalIdRef = useRef(null);

  const syncQueue = useCallback(async () => {
    try {
      const status = await waitingRoomService.getQueueStatus(eventId);
      setQueueState(status);
      if (['ADMITTED', 'EXPIRED', 'COMPLETED', 'FULL'].includes(status.status)) {
        clearInterval(intervalIdRef.current);
        intervalIdRef.current = null;
      }
    } catch (err) {
      setError(err.message || 'Failed to communicate with Waiting Room engine.');
    }
  }, [eventId]);

  useEffect(() => {
    const initWaitingRoom = async () => {
      if (!authService.getCurrentUser()) {
        navigate('/login');
        return;
      }
      setLoading(true);
      try {
        const evData = await eventService.getEventById(eventId);
        setEvent(evData);

        const initialStatus = await waitingRoomService.joinWaitingRoom(eventId);
        setQueueState(initialStatus);

        // Auto polling queue status every 3.5 seconds
        if (!['ADMITTED', 'EXPIRED', 'COMPLETED', 'FULL'].includes(initialStatus.status)) {
          intervalIdRef.current = setInterval(syncQueue, 3500);
        }
      } catch (err) {
        setError(err.message || 'Waiting room initialization failed.');
      } finally {
        setLoading(false);
      }
    };

    initWaitingRoom();

    return () => {
      clearInterval(intervalIdRef.current);
      intervalIdRef.current = null;
    };
  }, [eventId, navigate, syncQueue]);

  const handleProceedToBooking = () => {
    navigate(`/booking/${eventId}`);
  };

  if (loading) return <PageContainer><Loader message="Entering Event Vault Waiting Room..." /></PageContainer>;
  if (error || !event) return <PageContainer><ErrorState title="Waiting Room Error" message={error} /></PageContainer>;

  const isAdmitted = queueState?.status === 'ADMITTED';

  return (
    <PageContainer>
      <div className="ev-waiting-room-page">
        <div className="ev-wr-header-banner">
          <ShieldCheck size={28} className="ev-wr-shield" />
          <div>
            <h1>Event Vault Admission Control</h1>
            <p>Event: <strong>{event.name}</strong> ({event.venue})</p>
          </div>
        </div>

        <QueueStatus queueData={queueState} onRefresh={syncQueue} />

        <QueueProgress queueData={queueState} />

        <div className="ev-wr-explanation-card">
          <h3>Why am I in a waiting room?</h3>
          <p>
            "We're controlling access to the booking system so the event remains stable during high demand."
          </p>
          <div className="ev-wr-arch-note">
            <Activity size={14} />
            <span>Waiting Room Service Target API: GET /waiting-room/{eventId}/status</span>
          </div>
        </div>

        {isAdmitted && (
          <div className="ev-admitted-cta-container">
            <Button variant="primary" size="lg" onClick={handleProceedToBooking} className="ev-admitted-btn">
              <span>Enter Booking System Now</span>
              <ArrowRight size={20} />
            </Button>
          </div>
        )}
      </div>
    </PageContainer>
  );
};
