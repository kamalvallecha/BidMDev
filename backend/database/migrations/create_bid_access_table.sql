
-- Create bid_access table
CREATE TABLE IF NOT EXISTS bid_access (
    id SERIAL PRIMARY KEY,
    bid_id INTEGER,
    user_id INTEGER,
    team VARCHAR(100),
    granted_by INTEGER,
    granted_on TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT bid_access_bid_id_user_id_team_key UNIQUE (bid_id, user_id, team),
    CONSTRAINT bid_access_bid_id_fkey FOREIGN KEY (bid_id) REFERENCES bids(id) ON DELETE CASCADE,
    CONSTRAINT bid_access_granted_by_fkey FOREIGN KEY (granted_by) REFERENCES users(id),
    CONSTRAINT bid_access_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create bid_access_requests table if it doesn't exist
CREATE TABLE IF NOT EXISTS bid_access_requests (
    id SERIAL PRIMARY KEY,
    bid_id INTEGER,
    user_id INTEGER,
    team VARCHAR(100),
    requested_on TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    CONSTRAINT bid_access_requests_bid_id_user_id_team_key UNIQUE (bid_id, user_id, team),
    CONSTRAINT bid_access_requests_bid_id_fkey FOREIGN KEY (bid_id) REFERENCES bids(id) ON DELETE CASCADE,
    CONSTRAINT bid_access_requests_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_bid_access_bid_id ON bid_access(bid_id);
CREATE INDEX IF NOT EXISTS idx_bid_access_user_id ON bid_access(user_id);
CREATE INDEX IF NOT EXISTS idx_bid_access_team ON bid_access(team);
CREATE INDEX IF NOT EXISTS idx_bid_access_requests_bid_id ON bid_access_requests(bid_id);
CREATE INDEX IF NOT EXISTS idx_bid_access_requests_status ON bid_access_requests(status);
