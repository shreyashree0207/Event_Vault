import React from 'react';
import './Seat.css';

export const Seat = ({ seat, isSelected, onSelect }) => {
  const isBooked = seat.status === 'UNAVAILABLE';

  const handleClick = () => {
    if (!isBooked) {
      onSelect(seat);
    }
  };

  let seatClass = 'available';
  if (isBooked) seatClass = 'unavailable';
  else if (isSelected) seatClass = 'selected';

  return (
    <button
      className={`ev-seat ev-seat--${seatClass}`}
      disabled={isBooked}
      onClick={handleClick}
      title={`Seat ${seat.code} (${seat.category})`}
    >
      {seat.number}
    </button>
  );
};
