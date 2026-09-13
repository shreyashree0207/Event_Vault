import React from 'react';
import './StatusBadge.css';

export const StatusBadge = ({ status, label }) => {
  const getBadgeStyle = (stat) => {
    switch (stat?.toUpperCase()) {
      case 'AVAILABLE':
      case 'READY':
      case 'PAID':
      case 'CONFIRMED':
      case 'UPCOMING':
      case 'ADMITTED':
        return 'success';
      case 'SELLING_FAST':
      case 'WAITING':
      case 'PROCESSING':
        return 'warning';
      case 'ALMOST_SOLD_OUT':
      case 'SOLD_OUT':
      case 'EXPIRED':
      case 'FAILED':
      case 'CANCELLED':
        return 'danger';
      default:
        return 'neutral';
    }
  };

  const styleClass = getBadgeStyle(status);
  const displayLabel = label || status?.replace('_', ' ');

  return (
    <span className={`ev-status-badge ev-status-badge--${styleClass}`}>
      <span className="ev-status-badge__dot"></span>
      <span className="ev-status-badge__text">{displayLabel}</span>
    </span>
  );
};
