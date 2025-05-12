
CREATE TABLE IF NOT EXISTS partner_links (
    id SERIAL PRIMARY KEY,
    bid_id INTEGER REFERENCES bids(id),
    partner_id INTEGER REFERENCES partners(id),
    token TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notification_sent BOOLEAN DEFAULT FALSE,
    UNIQUE(bid_id, partner_id)
);
