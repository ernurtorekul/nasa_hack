-- SIMPLE SQL TO UPDATE DATABASE FOR TELEGRAM INTEGRATION
-- Copy and paste this into your Supabase SQL Editor and run it

-- Add missing columns for Telegram bot
ALTER TABLE users
ADD COLUMN IF NOT EXISTS chat_id BIGINT UNIQUE,
ADD COLUMN IF NOT EXISTS latitude DECIMAL(10, 8),
ADD COLUMN IF NOT EXISTS longitude DECIMAL(11, 8);

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create policies
DROP POLICY IF EXISTS "Allow anonymous inserts" ON users;
CREATE POLICY "Allow anonymous inserts" ON users
    FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Allow anonymous selects" ON users;
CREATE POLICY "Allow anonymous selects" ON users
    FOR SELECT USING (true);

-- Create index for chat_id
CREATE INDEX IF NOT EXISTS idx_users_chat_id ON users(chat_id);

-- Verify the table structure
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'users'
ORDER BY ordinal_position;