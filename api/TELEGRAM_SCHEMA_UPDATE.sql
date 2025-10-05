-- Update users table for Telegram integration
-- Run this in your Supabase SQL editor

-- Option 1: Add columns to existing table
ALTER TABLE users
ADD COLUMN IF NOT EXISTS chat_id BIGINT UNIQUE,
ADD COLUMN IF NOT EXISTS latitude DECIMAL(10, 8),
ADD COLUMN IF NOT EXISTS longitude DECIMAL(11, 8);

-- Option 2: Create new table (if starting fresh)
/*
CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    chat_id BIGINT UNIQUE NOT NULL,
    city VARCHAR(255),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
*/

-- Update RLS policies for Telegram integration
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Allow anonymous inserts for user registration
CREATE POLICY "Allow anonymous inserts" ON users
    FOR INSERT WITH CHECK (true);

-- Allow anonymous selects for reading users
CREATE POLICY "Allow anonymous selects" ON users
    FOR SELECT USING (true);

-- Allow updates for users to change their location
CREATE POLICY "Allow user updates" ON users
    FOR UPDATE USING (true);

-- Create index for faster chat_id lookups
CREATE INDEX IF NOT EXISTS idx_users_chat_id ON users(chat_id);