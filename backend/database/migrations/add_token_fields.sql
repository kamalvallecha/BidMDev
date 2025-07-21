
-- Add token fields to partner_responses table if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'partner_responses' 
        AND column_name = 'token'
    ) THEN
        ALTER TABLE partner_responses
        ADD COLUMN token VARCHAR(255),
        ADD COLUMN expires_at TIMESTAMP,
        ADD COLUMN submitted_at TIMESTAMP;

        -- Add unique constraint to token
        ALTER TABLE partner_responses
        ADD CONSTRAINT partner_responses_token_key UNIQUE (token);
    END IF;
END $$;
