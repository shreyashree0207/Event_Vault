import React from 'react';
import './Seat.css';

export const Seat = ({ seat, isSelected, onSelect }) => {
  const seatNumber = seat.seatNumber || seat.code;
  const normalizedStatus = seat.status?.toLowerCase();
  const isBooked = ['booked', 'unavailable'].includes(normalizedStatus);
  const isLocked = normalizedStatus === 'locked' && !seat.lockedByCurrentUser;
  const isUnavailable = isBooked || isLocked;

  const handleClick = () => {
    if (!isUnavailable) {
      onSelect(seat);
    }
  };

  let seatClass = 'available';
  if (isUnavailable) seatClass = 'unavailable';
  else if (isSelected) seatClass = 'selected';

  return (
    <button
      className={`ev-seat ev-seat--${seatClass}`}
      disabled={isUnavailable}
      onClick={handleClick}
      aria-label={`Seat ${seatNumber}: ${normalizedStatus || 'available'}`}
      title={`Seat ${seatNumber} (${normalizedStatus || 'available'})`}
    >
      {seatNumber}
    </button>
  );
};
