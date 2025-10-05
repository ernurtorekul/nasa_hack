# WeatherSphere

A weather monitoring web application with Telegram notifications for the NASA hackathon.

## Project Structure

```
nasa_hackathon/
├── api/          # FastAPI backend
├── frontend/     # React + Vite + TailwindCSS frontend
├── telegram/     # Telegram bot integration (placeholder)
└── README.md
```

## Setup

### Backend (FastAPI)
```bash
cd api
pip install -r requirements.txt
python main.py
```

### Frontend (React + Vite + TailwindCSS)
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

- `GET /` - Hello World endpoint