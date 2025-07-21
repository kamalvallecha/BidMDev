
-- Add created_by and team columns to bids table
ALTER TABLE bids 
ADD COLUMN IF NOT EXISTS created_by INTEGER,
ADD COLUMN IF NOT EXISTS team VARCHAR(100);

-- Add foreign key constraint for created_by
ALTER TABLE bids 
ADD CONSTRAINT bids_created_by_fkey 
FOREIGN KEY (created_by) REFERENCES users(id);

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_bids_created_by ON bids(created_by);
CREATE INDEX IF NOT EXISTS idx_bids_team ON bids(team);
