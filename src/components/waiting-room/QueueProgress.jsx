import React from 'react';
import './QueueProgress.css';

export const QueueProgress = ({ queueData }) => {
  // Compute artificial percentage based on users ahead
  const initialEstimateMax = 350;
  const usersAhead = queueData.usersAhead || 0;
  const progressPercent = queueData.status === 'ADMITTED' 
    ? 100 
    : Math.min(95, Math.max(5, Math.round(((initialEstimateMax - usersAhead) / initialEstimateMax) * 100)));

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
