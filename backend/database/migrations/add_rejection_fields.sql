-- First, create a new enum type with all values
CREATE TYPE bid_status_new AS ENUM ('draft', 'infield', 'closure', 'ready_for_invoice', 'invoiced', 'completed', 'rejected');

-- Add rejection fields to bids table
ALTER TABLE bids
ADD COLUMN rejection_reason VARCHAR(100),
ADD COLUMN rejection_comments TEXT;

-- Update the status column to use the new enum type
ALTER TABLE bids 
ALTER COLUMN status TYPE bid_status_new 
USING status::text::bid_status_new; 