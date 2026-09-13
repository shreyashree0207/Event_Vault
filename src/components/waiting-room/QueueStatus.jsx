import React from 'react';
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

  return (
    <div className={`ev-queue-card ${isAdmitted ? 'ev-queue-card--admitted' : ''}`}>
      <div className="ev-queue-header">
        <div className="ev-queue-badge">
          <span className={`ev-queue-dot ${isAdmitted ? 'admitted' : 'waiting'}`}></span>
          <span>{isAdmitted ? 'ADMISSION GRANTED' : 'VIRTUAL WAITING ROOM'}</span>
        </div>
        <button onClick={onRefresh} className="ev-queue-refresh-btn" title="Check Latest Queue Status">
          <RefreshCw size={14} />
          <span>Sync Status</span>
        </button>
      </div>

      <div className="ev-queue-main-title">
        {isAdmitted ? "You're cleared for seat booking!" : "You are in the queue"}
      </div>

      {!isAdmitted ? (
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
      ) : (
        <div className="ev-admitted-box">
          <ShieldCheck size={40} className="ev-admitted-icon" />
          <p>Admission slot verified. You have <strong>10 minutes</strong> to complete seat selection before your reservation window expires.</p>
        </div>
      )}
    </div>
  );
};
