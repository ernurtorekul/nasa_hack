# Telegram Bot Setup for WeatherSphere

## 1. Create Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` command
3. Follow the prompts to create your bot
4. Note your bot token (looks like: `1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

## 2. Update Environment Variables

Add to your `.env` file:
```env
TELEGRAM_BOT_TOKEN=your_actual_bot_token_here
API_BASE_URL=http://localhost:8000  # or your deployed API URL
```

## 3. Update Supabase Database

Run the SQL in `TELEGRAM_SCHEMA_UPDATE.sql` in your Supabase SQL editor to add:
- `chat_id` column (unique)
- `latitude` and `longitude` columns
- Proper indexes and RLS policies

## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## 5. Test the API

Start the FastAPI server:
```bash
python3 main.py
```

Test the updated endpoint:
```bash
curl -X POST "http://localhost:8000/register_location" \
     -H "Content-Type: application/json" \
     -d '{"chat_id": 123456789, "city": "London"}'
```

## 6. Run the Telegram Bot

```bash
python3 telegram_bot.py
```

## 7. Test the Bot Flow

1. Find your bot on Telegram and send `/start`
2. Choose either:
   - **📍 Share Location** - Share GPS coordinates
   - **✏️ Enter Manually** - Type city name
3. Bot will register your location and send confirmation
4. You'll get a dashboard button (currently placeholder)

## 8. Bot Features

### Commands:
- `/start` - Begin registration process
- `/help` - Show help information

### Registration Flow:
1. User sends `/start`
2. Bot shows location options (buttons)
3. User chooses location sharing method
4. Bot sends location data to API endpoint
5. Bot shows success message with dashboard button

### API Integration:
- Calls `/register_location` endpoint with chat_id and location data
- Handles both city names and GPS coordinates
- Supports user updates (existing chat_id gets updated location)
- Error handling for failed registrations

## 9. Deployment Notes

For production deployment:
1. Deploy API to a public server
2. Update `API_BASE_URL` in `.env`
3. Set up webhook for Telegram bot (instead of polling)
4. Configure HTTPS for webhook endpoint
5. Set up proper logging and monitoring

## 10. Dashboard Integration

The "Open Dashboard" button currently links to a placeholder URL. To integrate with your React frontend:
1. Deploy your frontend to a public URL
2. Update the button URL in `telegram_bot.py`
3. Pass chat_id as URL parameter for user identification
4. Implement user authentication in the frontend