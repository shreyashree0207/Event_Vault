import React from 'react';
import './QueueProgress.css';

export const QueueProgress = ({ queueData }) => {
  const usersAhead = queueData.usersAhead || 0;
  const progressPercent = queueData.status === 'ADMITTED'
    ? 100
    : queueData.status === 'WAITING'
      ? Math.max(5, Math.round(100 / (usersAhead + 1)))
      : 0;

  return (
    <div className="ev-queue-progress-wrapper">
      <div className="ev-queue-progress-info">
        <span className="ev-progress-label">Admission Queue Processing</span>
        <span className="ev-progress-value">{progressPercent}%</span>
      </div>
      <div className="ev-progress-track">
        <div 
          className={`ev-progress-bar ${queueData.status === 'ADMITTED' ? 'completed' : ''}`}
          style={{ width: `${progressPercent}%` }}
        ></div>
      </div>
    </div>
  );
};
