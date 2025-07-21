
-- Create a new methodology enum with only the desired values
CREATE TYPE methodology_new AS ENUM ('online', 'offline', 'mixed');

-- Update the bids table to use the new enum
ALTER TABLE bids ALTER COLUMN methodology TYPE methodology_new USING methodology::text::methodology_new;

-- Drop the old enum and rename the new one
DROP TYPE methodology CASCADE;
ALTER TYPE methodology_new RENAME TO methodology;
