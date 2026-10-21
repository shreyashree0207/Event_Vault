import React from 'react';
import { Link } from 'react-router-dom';
import { Users, Clock, ShieldCheck, RefreshCw } from 'lucide-react';
import './QueueStatus.css';

export const QueueStatus = ({ queueData, onRefresh }) => {
  const formatTime = (seconds) => {
    if (!seconds) return 'Calculating...';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins} min ${secs} sec`;
  };

  const isAdmitted = queueData.status === 'ADMITTED';
  const isWaiting = queueData.status === 'WAITING';
  const isFull = queueData.status === 'FULL';
  const isExpired = queueData.status === 'EXPIRED';
  const isCompleted = queueData.status === 'COMPLETED';
  const expiryTime = queueData.expiresAt
    ? new Date(queueData.expiresAt).toLocaleTimeString()
    : '';

  return (
    <div className={`ev-queue-card ${isAdmitted ? 'ev-queue-card--admitted' : ''}`}>
      <div className="ev-queue-header">
        <div className="ev-queue-badge">
          <span className={`ev-queue-dot ${isAdmitted ? 'admitted' : 'waiting'}`}></span>
          <span>
            {isAdmitted ? 'ADMISSION GRANTED' : isFull ? 'QUEUE AT CAPACITY' :
              isExpired ? 'ADMISSION EXPIRED' : isCompleted ? 'BOOKING COMPLETE' :
                'VIRTUAL WAITING ROOM'}
          </span>
        </div>
        {!isExpired && !isCompleted && (
          <button onClick={onRefresh} className="ev-queue-refresh-btn" title="Check Latest Queue Status">
            <RefreshCw size={14} />
            <span>{isFull ? 'Retry' : 'Sync Status'}</span>
          </button>
        )}
      </div>

      <div className="ev-queue-main-title">
        {isAdmitted ? "You're cleared for seat booking!" :
          isFull ? 'The waiting queue is currently full.' :
            isExpired ? 'Your admission window expired.' :
              isCompleted ? 'Your booking has been submitted.' :
                'You are in the queue'}
      </div>

      {isWaiting ? (
        <div className="ev-queue-stats-grid">
          <div className="ev-queue-stat">
            <div className="ev-stat-label">Users Ahead</div>
            <div className="ev-stat-value">
              <Users size={20} className="ev-stat-icon" />
              <span>{queueData.usersAhead}</span>
            </div>
          </div>

          <div className="ev-queue-stat">
            <div className="ev-stat-label">Estimated Wait</div>
            <div className="ev-stat-value">
              <Clock size={20} className="ev-stat-icon" />
              <span>{formatTime(queueData.estimatedWaitSeconds)}</span>
            </div>
          </div>
        </div>
      ) : isAdmitted ? (
        <div className="ev-admitted-box">
          <ShieldCheck size={40} className="ev-admitted-icon" />
          <p>
            Admission slot verified until <strong>{expiryTime}</strong>. Complete
            {' '}seat selection before your reservation window expires.
          </p>
        </div>
      ) : isFull ? (
        <p>The system has reached its configured waiting-room queue limit. Retry shortly.</p>
      ) : isExpired ? (
        <p>Your booking slot is no longer active. <Link to="/login">Sign in again</Link> to rejoin.</p>
      ) : (
        <p>Your booking is complete. <Link to="/my-tickets">View your tickets</Link>.</p>
      )}
    </div>
  );
};
