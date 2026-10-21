import React from 'react';
import { Seat } from './Seat';
import './SeatMap.css';

export const SeatMap = ({ seats, selectedSeats, onToggleSeat }) => {

  // Group seats by row
  const rows = seats.reduce((acc, seat) => {

    const seatNumber = seat.seatNumber || seat.code;
    const row = seatNumber.charAt(0);

    if (!acc[row]) {
      acc[row] = [];
    }

    acc[row].push(seat);

    return acc;

  }, {});


  return (
    <div className="ev-seatmap-container">

      <div className="ev-stage">
        <div className="ev-stage-screen">
          MAIN STAGE / PERFORMANCE AREA
        </div>
      </div>


      <div className="ev-seats-grid">

        {Object.entries(rows).map(([rowLabel, rowSeats]) => (

          <div key={rowLabel} className="ev-seat-row">

            <span className="ev-row-label">
              {rowLabel}
            </span>

            <div className="ev-row-seats">

              {rowSeats.map((seat) => (

                <Seat
                  key={seat.id}
                  seat={seat}

                  isSelected={
                    selectedSeats.includes(seat.seatNumber || seat.code)
                  }

                  onSelect={() =>
                    onToggleSeat(seat.seatNumber || seat.code)
                  }
                />

              ))}

            </div>

            <span className="ev-row-label">
              {rowLabel}
            </span>

          </div>

        ))}

      </div>


      <div className="ev-seat-legend">

        <div className="ev-legend-item">
          <span className="ev-legend-dot available"></span>
          <span>Available</span>
        </div>

        <div className="ev-legend-item">
          <span className="ev-legend-dot selected"></span>
          <span>Selected</span>
        </div>

        <div className="ev-legend-item">
          <span className="ev-legend-dot unavailable"></span>
          <span>Booked / Locked</span>
        </div>

      </div>

    </div>
  );
};