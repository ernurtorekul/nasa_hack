# Supabase Setup for WeatherSphere

## 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Note your project URL and anon key

## 2. Create Database Table

In your Supabase project SQL editor, run:

```sql
CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    city VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Optional: Add RLS (Row Level Security)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Allow anonymous inserts
CREATE POLICY "Allow anonymous inserts" ON users
    FOR INSERT WITH CHECK (true);

-- Allow anonymous selects
CREATE POLICY "Allow anonymous selects" ON users
    FOR SELECT USING (true);
```

## 3. Update Environment Variables

Update your `.env` file with your Supabase credentials:

```env
OPENWEATHER_API_KEY=dc7a7aedf53c9a6dc7c1e07000d04dbc

# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key
```

## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## 5. Test the API

Start the server:
```bash
python3 main.py
```

### Register a Location:
```bash
curl -X POST "http://localhost:8000/register_location" \
     -H "Content-Type: application/json" \
     -d '{"city": "Taraz"}'
```

### Send Weather Alerts:
```bash
curl -X POST "http://localhost:8000/send_alerts"
```

## 6. Alert Conditions

The system sends alerts for:
- Temperature < 0°C (freezing)
- Temperature > 35°C (extreme heat)
- Humidity > 85%
- Wind speed > 10 m/s
- Rain, storms, snow, thunder, or hail