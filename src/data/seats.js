export const generateMockSeats = (eventId) => {
  const rows = ['A', 'B', 'C', 'D', 'E', 'F'];
  const seatsPerRow = 10;
  const seats = [];

  rows.forEach((row, rowIndex) => {
    let category = 'Standard';
    let priceMultiplier = 1;

    if (rowIndex === 0 || rowIndex === 1) {
      category = 'VIP Front Row';
      priceMultiplier = 1.6;
    } else if (rowIndex === 2 || rowIndex === 3) {
      category = 'Premium Tier';
      priceMultiplier = 1.25;
    }

    for (let num = 1; num <= seatsPerRow; num++) {
      const seatId = `${eventId}-${row}${num}`;
      
      // Randomly set ~25% seats as unavailable to look realistic
      const isBooked = (row === 'A' && num % 3 === 0) || (row === 'C' && num % 2 === 1) || (row === 'E' && num > 7);

      seats.push({
        id: seatId,
        eventId,
        row,
        number: num,
        code: `${row}${num}`,
        category,
        priceMultiplier,
        status: isBooked ? 'UNAVAILABLE' : 'AVAILABLE'
      });
    }
  });

  return seats;
};
