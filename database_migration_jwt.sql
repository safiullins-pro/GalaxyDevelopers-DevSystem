-- JWT REFRESH TOKENS TABLE
-- Based on Perplexity research for secure JWT implementation

-- Create refresh_tokens table
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(512) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);

-- Create indexes separately
CREATE INDEX IF NOT EXISTS idx_refresh_token ON refresh_tokens(token);
CREATE INDEX IF NOT EXISTS idx_user_refresh_tokens ON refresh_tokens(user_id, revoked);
CREATE INDEX IF NOT EXISTS idx_expires_at ON refresh_tokens(expires_at);

-- Function to automatically clean expired tokens
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM refresh_tokens 
    WHERE expires_at < NOW() OR (revoked = true AND revoked_at < NOW() - INTERVAL '7 days');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create scheduled job to clean expired tokens daily (requires pg_cron extension)
-- Uncomment if pg_cron is available:
-- SELECT cron.schedule('cleanup-expired-tokens', '0 3 * * *', 'SELECT cleanup_expired_tokens();');

-- Table for tracking JWT key rotation (for future implementation)
CREATE TABLE IF NOT EXISTS jwt_keys (
    id SERIAL PRIMARY KEY,
    key_id VARCHAR(128) UNIQUE NOT NULL,
    secret_hash VARCHAR(128) NOT NULL, -- Store hash of secret, not the secret itself
    algorithm VARCHAR(10) DEFAULT 'HS256',
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    rotated_at TIMESTAMP
);

-- Session tracking table for audit
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(128) UNIQUE NOT NULL,
    access_token_jti VARCHAR(64),
    refresh_token_id INTEGER REFERENCES refresh_tokens(id),
    started_at TIMESTAMP DEFAULT NOW(),
    last_activity TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    end_reason VARCHAR(50), -- logout, expired, revoked, password_change
    ip_address INET,
    user_agent TEXT
);

-- Index for session lookups
CREATE INDEX idx_user_sessions ON user_sessions(user_id, ended_at);
CREATE INDEX idx_session_id ON user_sessions(session_id);

-- View to monitor active sessions
CREATE OR REPLACE VIEW active_sessions AS
SELECT 
    u.email,
    s.session_id,
    s.started_at,
    s.last_activity,
    s.ip_address,
    EXTRACT(EPOCH FROM (NOW() - s.last_activity)) / 60 as minutes_inactive
FROM user_sessions s
JOIN users u ON s.user_id = u.id
WHERE s.ended_at IS NULL
ORDER BY s.last_activity DESC;

-- View to monitor token usage
CREATE OR REPLACE VIEW token_statistics AS
SELECT 
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(*) as total_refresh_tokens,
    COUNT(*) FILTER (WHERE revoked = true) as revoked_tokens,
    COUNT(*) FILTER (WHERE expires_at < NOW()) as expired_tokens,
    COUNT(*) FILTER (WHERE revoked = false AND expires_at > NOW()) as active_tokens
FROM refresh_tokens;

-- Function to revoke all user tokens (for password change, security breach)
CREATE OR REPLACE FUNCTION revoke_all_user_tokens(p_user_id INTEGER, p_reason VARCHAR DEFAULT 'manual')
RETURNS INTEGER AS $$
DECLARE
    revoked_count INTEGER;
BEGIN
    -- Revoke all refresh tokens
    UPDATE refresh_tokens 
    SET revoked = true, revoked_at = NOW()
    WHERE user_id = p_user_id AND revoked = false;
    
    GET DIAGNOSTICS revoked_count = ROW_COUNT;
    
    -- End all active sessions
    UPDATE user_sessions
    SET ended_at = NOW(), end_reason = p_reason
    WHERE user_id = p_user_id AND ended_at IS NULL;
    
    RETURN revoked_count;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-revoke tokens on password change
CREATE OR REPLACE FUNCTION auto_revoke_on_password_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.password_hash IS DISTINCT FROM NEW.password_hash THEN
        PERFORM revoke_all_user_tokens(NEW.id, 'password_change');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_password_change_revoke
AFTER UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION auto_revoke_on_password_change();

-- Add comments for documentation
COMMENT ON TABLE refresh_tokens IS 'Stores JWT refresh tokens for user sessions';
COMMENT ON TABLE jwt_keys IS 'Tracks JWT signing keys for rotation';
COMMENT ON TABLE user_sessions IS 'Audit trail of user login sessions';
COMMENT ON FUNCTION revoke_all_user_tokens IS 'Revokes all tokens for a user (use on password change or breach)';

-- Initial cleanup
SELECT cleanup_expired_tokens();

-- Show statistics
SELECT * FROM token_statistics;