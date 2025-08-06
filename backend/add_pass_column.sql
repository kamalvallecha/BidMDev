-- Add pass column to partner_audience_responses table if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'partner_audience_responses' 
        AND column_name = 'pass'
    ) THEN
        ALTER TABLE partner_audience_responses 
        ADD COLUMN pass boolean DEFAULT false;
    END IF;
END $$;

-- Add comment to explain the column
COMMENT ON COLUMN partner_audience_responses.pass IS 'Indicates if partner wants to pass on this country'; 