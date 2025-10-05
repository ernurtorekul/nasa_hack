-- URGENT: Run this SQL in your Supabase SQL Editor immediately!
-- This will fix the "Failed to register location" error

-- First, let's see what columns currently exist
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users';

-- Add the missing columns for Telegram integration
ALTER TABLE users
ADD COLUMN IF NOT EXISTS chat_id BIGINT UNIQUE,
ADD COLUMN IF NOT EXISTS latitude DECIMAL(10, 8),
ADD COLUMN IF NOT EXISTS longitude DECIMAL(11, 8);

-- If the table doesn't exist or has issues, create a new one:
-- DROP TABLE IF EXISTS users CASCADE;
-- CREATE TABLE users (
--     id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
--     chat_id BIGINT UNIQUE NOT NULL,
--     city VARCHAR(255),
--     latitude DECIMAL(10, 8),
--     longitude DECIMAL(11, 8),
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
-- );

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create policies for anonymous access (needed for bot to work)
DROP POLICY IF EXISTS "Allow anonymous inserts" ON users;
CREATE POLICY "Allow anonymous inserts" ON users
    FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Allow anonymous selects" ON users;
CREATE POLICY "Allow anonymous selects" ON users
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow user updates" ON users;
CREATE POLICY "Allow user updates" ON users
    FOR UPDATE USING (true);

-- Create index for faster chat_id lookups
CREATE INDEX IF NOT EXISTS idx_users_chat_id ON users(chat_id);

-- Test the table structure
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'users'
ORDER BY ordinal_position;