
-- Update methodology enum
ALTER TYPE methodology ADD VALUE IF NOT EXISTS 'online';
ALTER TYPE methodology ADD VALUE IF NOT EXISTS 'offline';
ALTER TYPE methodology ADD VALUE IF NOT EXISTS 'mixed';

-- Add new columns to partner_audience_responses if they don't exist
DO $$ 
BEGIN
    -- Add commitment_type column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'partner_audience_responses' 
                  AND column_name = 'commitment_type') THEN
        ALTER TABLE partner_audience_responses 
        ADD COLUMN commitment_type VARCHAR(10) DEFAULT 'fixed';
        
        ALTER TABLE partner_audience_responses
        ADD CONSTRAINT partner_audience_responses_commitment_type_check 
        CHECK (commitment_type IN ('fixed', 'be_max'));
    END IF;

    -- Add field_close_date column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'partner_audience_responses' 
                  AND column_name = 'field_close_date') THEN
        ALTER TABLE partner_audience_responses 
        ADD COLUMN field_close_date DATE;
    END IF;

    -- Add rating columns
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'partner_audience_responses' 
                  AND column_name = 'communication_rating') THEN
        ALTER TABLE partner_audience_responses 
        ADD COLUMN communication_rating INTEGER;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'partner_audience_responses' 
                  AND column_name = 'engagement_rating') THEN
        ALTER TABLE partner_audience_responses 
        ADD COLUMN engagement_rating INTEGER;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'partner_audience_responses' 
                  AND column_name = 'problem_solving_rating') THEN
        ALTER TABLE partner_audience_responses 
        ADD COLUMN problem_solving_rating INTEGER;
    END IF;
END $$;

-- Update partner_links table
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'partner_links') THEN
        CREATE TABLE partner_links (
            id SERIAL PRIMARY KEY,
            bid_id INTEGER NOT NULL,
            partner_id INTEGER NOT NULL,
            token VARCHAR(255) NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            submitted_at TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (bid_id) REFERENCES bids(id) ON DELETE CASCADE,
            FOREIGN KEY (partner_id) REFERENCES partners(id)
        );
        
        CREATE UNIQUE INDEX ON partner_links(token);
    END IF;
END $$;
