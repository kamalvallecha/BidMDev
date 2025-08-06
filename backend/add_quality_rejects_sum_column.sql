-- Add quality_rejects_sum column to bid_target_audiences table
ALTER TABLE bid_target_audiences 
ADD COLUMN quality_rejects_sum integer DEFAULT 0;

-- Add comment to explain the column
COMMENT ON COLUMN bid_target_audiences.quality_rejects_sum IS 'Sum of quality rejects from all partner responses for this audience'; 