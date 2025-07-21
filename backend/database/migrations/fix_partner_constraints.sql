
-- Ensure unique constraints exist for ON CONFLICT operations
DO $$
BEGIN
    -- Check if unique constraint exists on partner_responses
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'partner_responses_bid_partner_loi_key' 
        AND table_name = 'partner_responses'
    ) THEN
        ALTER TABLE partner_responses 
        ADD CONSTRAINT partner_responses_bid_partner_loi_key 
        UNIQUE (bid_id, partner_id, loi);
    END IF;

    -- Check if unique constraint exists on partner_audience_responses
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'partner_audience_responses_unique_key' 
        AND table_name = 'partner_audience_responses'
    ) THEN
        ALTER TABLE partner_audience_responses 
        ADD CONSTRAINT partner_audience_responses_unique_key 
        UNIQUE (bid_id, partner_response_id, audience_id, country);
    END IF;
END $$;
