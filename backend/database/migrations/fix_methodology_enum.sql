
<old_str>-- Fix methodology enum by adding missing values
ALTER TYPE methodology ADD VALUE IF NOT EXISTS 'online';
ALTER TYPE methodology ADD VALUE IF NOT EXISTS 'offline'; 
ALTER TYPE methodology ADD VALUE IF NOT EXISTS 'mixed';

-- Also add 'quant' if it doesn't exist (from your existing add_methodology.py)
ALTER TYPE methodology ADD VALUE IF NOT EXISTS 'quant';</old_str>
<new_str>-- Create a new methodology enum with only the desired values
CREATE TYPE methodology_new AS ENUM ('online', 'offline', 'mixed');

-- Update the bids table to use the new enum
ALTER TABLE bids ALTER COLUMN methodology TYPE methodology_new USING methodology::text::methodology_new;

-- Drop the old enum and rename the new one
DROP TYPE methodology;
ALTER TYPE methodology_new RENAME TO methodology;</new_str>
