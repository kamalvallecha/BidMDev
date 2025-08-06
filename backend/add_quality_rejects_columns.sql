
-- Add quality_rejects_sum column to bid_target_audiences table
ALTER TABLE bid_target_audiences ADD COLUMN quality_rejects_sum integer DEFAULT 0;

-- Add quality_rejects column to partner_audience_responses table  
ALTER TABLE partner_audience_responses ADD COLUMN quality_rejects integer DEFAULT 0;

-- Add quality_rejects column to partner_responses table
ALTER TABLE partner_responses ADD COLUMN quality_rejects integer DEFAULT 0;

-- Add comments to explain the columns
COMMENT ON COLUMN bid_target_audiences.quality_rejects_sum IS 'Sum of quality rejects from all partner responses for this audience';
COMMENT ON COLUMN partner_audience_responses.quality_rejects IS 'Number of quality rejects for this partner audience response';
COMMENT ON COLUMN partner_responses.quality_rejects IS 'Number of quality rejects for this partner response';
