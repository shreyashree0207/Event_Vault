-- Add database-level protections after reviewing duplicate legacy rows.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM seats
        GROUP BY event_id, seat_number
        HAVING count(*) > 1
    ) THEN
        RAISE EXCEPTION
            'Duplicate seat numbers exist within an event; resolve them before applying this migration.';
    END IF;

    IF EXISTS (
        SELECT seat_id
        FROM bookings
        WHERE lower(status) = 'confirmed'
        GROUP BY seat_id
        HAVING count(*) > 1
    ) THEN
        RAISE EXCEPTION
            'Multiple confirmed bookings exist for a seat; resolve them before applying this migration.';
    END IF;
END
$$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_seats_event_number
    ON seats (event_id, seat_number);
CREATE UNIQUE INDEX IF NOT EXISTS uq_bookings_confirmed_seat
    ON bookings (seat_id)
    WHERE lower(status) = 'confirmed';
