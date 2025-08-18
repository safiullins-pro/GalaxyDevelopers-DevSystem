-- MIGRATION: Add unique salt column to users table
-- Based on Perplexity research on secure password hashing

-- Phase 1: Add new columns for secure password storage
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS password_salt VARCHAR(64), -- 32 bytes as hex = 64 chars
ADD COLUMN IF NOT EXISTS migration_status VARCHAR(20) DEFAULT 'pending';

-- Add constraints to ensure salt is never empty for new users
ALTER TABLE users 
ADD CONSTRAINT check_password_salt_not_empty 
CHECK (password_salt IS NULL OR length(password_salt) = 64);

-- Phase 2: Mark existing users for password reset
UPDATE users 
SET migration_status = 'reset_required'
WHERE password_salt IS NULL;

-- Phase 3: Create migration log table
CREATE TABLE IF NOT EXISTS password_migration_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    migrated_at TIMESTAMP DEFAULT NOW(),
    migration_type VARCHAR(50)
);

-- Phase 4: After all users migrated, you can:
-- ALTER TABLE users ALTER COLUMN password_salt SET NOT NULL;
-- ALTER TABLE users DROP COLUMN migration_status;

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_users_migration_status ON users(migration_status);

-- View to track migration progress
CREATE OR REPLACE VIEW migration_progress AS
SELECT 
    COUNT(*) FILTER (WHERE migration_status = 'pending') as pending_users,
    COUNT(*) FILTER (WHERE migration_status = 'reset_required') as reset_required,
    COUNT(*) FILTER (WHERE migration_status = 'migrated') as migrated_users,
    COUNT(*) as total_users,
    ROUND(100.0 * COUNT(*) FILTER (WHERE migration_status = 'migrated') / NULLIF(COUNT(*), 0), 2) as migration_percentage
FROM users;

-- Function to check if user needs migration
CREATE OR REPLACE FUNCTION needs_password_migration(user_email VARCHAR)
RETURNS BOOLEAN AS $$
DECLARE
    user_status VARCHAR(20);
BEGIN
    SELECT migration_status INTO user_status
    FROM users
    WHERE email = user_email;
    
    RETURN user_status != 'migrated' OR user_status IS NULL;
END;
$$ LANGUAGE plpgsql;

COMMENT ON COLUMN users.password_salt IS 'Unique 32-byte salt for password hashing (hex encoded)';
COMMENT ON COLUMN users.migration_status IS 'Password migration status: pending, reset_required, migrated';

-- Show migration status
SELECT * FROM migration_progress;