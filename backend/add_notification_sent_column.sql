-- Migration to add notification_sent column to partner_links table
-- This fixes the error: "column pl.notification_sent does not exist"

-- Add the notification_sent column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'partner_links' 
        AND column_name = 'notification_sent'
    ) THEN
        ALTER TABLE partner_links ADD COLUMN notification_sent BOOLEAN DEFAULT FALSE;
        RAISE NOTICE 'Added notification_sent column to partner_links table';
    ELSE
        RAISE NOTICE 'notification_sent column already exists in partner_links table';
    END IF;
END $$;

-- Update existing records to have notification_sent = false
UPDATE partner_links SET notification_sent = false WHERE notification_sent IS NULL; 