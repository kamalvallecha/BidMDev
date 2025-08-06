-- Add quality_rejects column to partner_responses table if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'partner_responses' 
        AND column_name = 'quality_rejects'
    ) THEN
        ALTER TABLE partner_responses 
        ADD COLUMN quality_rejects integer DEFAULT 0;
    END IF;
END $$;

-- Add comment to explain the column
COMMENT ON COLUMN partner_responses.quality_rejects IS 'Sum of quality rejects from all audiences for this partner and LOI'; 