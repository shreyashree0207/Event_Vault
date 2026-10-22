-- Add missing columns to tickets table matching models.Ticket
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS object_key VARCHAR;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS error_message VARCHAR;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS generation_started_at VARCHAR;
CREATE UNIQUE INDEX IF NOT EXISTS uq_tickets_booking_id ON tickets (booking_id);
