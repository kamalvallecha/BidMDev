

-- Drop and recreate methodology enum with correct values
DROP TYPE IF EXISTS methodology CASCADE;
CREATE TYPE methodology AS ENUM ('online', 'offline', 'mixed');

-- Add the methodology column back to bids table
ALTER TABLE bids ADD COLUMN methodology methodology NOT NULL DEFAULT 'online';
