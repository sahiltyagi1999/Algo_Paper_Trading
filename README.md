# 8-30 EMA Algo Trader

Automated options trading on Nifty using the 8 EMA / 30 EMA crossover strategy with Zerodha Kite Connect.

```
/
├── backend/        Flask API (deploy to Railway)
└── frontend/       Static dashboard (deploy to Netlify)
```

---

## Backend — Flask API

### Structure

```
backend/
├── app.py              Flask app factory + startup
├── config.py           All settings (loaded from .env)
├── Procfile            Railway / gunicorn entry-point
├── requirements.txt
├── .env.example        Copy → .env and fill in secrets
├── core/
│   └── database.py     MongoDB singleton (trades, logs, creds, config)
├── routes/
│   ├── trades.py       /api/trades, /api/summary, /api/equity
│   ├── kite.py         /api/kite/login-url, /api/kite/generate-token
│   ├── market.py       /api/vix, /api/oi, /api/candles, /api/status, /api/logs
│   └── settings.py     /api/settings, /api/mongo/connect
└── services/
    ├── kite_service.py
    ├── trade_service.py
    ├── market_service.py
    └── settings_service.py
```

### Local setup

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in MONGO_URL, KITE_API_KEY, KITE_API_SECRET
python app.py                 # → http://localhost:4200
```

### Deploy to Railway

1. Connect this repo → set root directory to `backend/`
2. Add environment variables from `.env.example`
3. Railway uses `Procfile` automatically

---

## Frontend — Static Dashboard

```
frontend/
├── index.html      Single-page dashboard (all JS inline)
└── js/
    └── config.js   Set API_BASE to your Railway URL before deploying
```

### Deploy to Netlify

1. Drag-and-drop the `frontend/` folder to Netlify, **or**
2. Connect repo → set **Publish directory** to `frontend/`

Before deploying, edit `frontend/js/config.js` and replace the placeholder Railway URL with your actual backend URL.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/trades` | All trades |
| GET | `/api/summary` | Win/loss stats (all + today) |
| GET | `/api/equity` | Equity curve data |
| GET | `/api/todays_equity` | Today's equity curve |
| GET | `/api/daily_history` | Daily summary history |
| GET | `/api/vix` | India VIX + danger level |
| GET | `/api/oi` | OI support / resistance levels |
| GET | `/api/candles` | Today's 5-min candles with EMAs |
| GET | `/api/status` | Algo running status + last log |
| GET | `/api/logs?date=YYYY-MM-DD&limit=300` | Log lines |
| GET | `/api/settings` | Current trading settings |
| POST | `/api/settings` | Update settings |
| GET | `/api/mongo/status` | MongoDB connection status |
| POST | `/api/mongo/connect` | Connect MongoDB at runtime |
| POST | `/api/kite/login-url` | Get Zerodha login URL |
| POST | `/api/kite/generate-token` | Exchange request token for access token |
| GET | `/api/kite/status` | Kite connection status |

---

## Algo Runner (local only)

The trading bot itself runs locally on your machine (not deployed). It reads `KITE_API_KEY`, `KITE_API_SECRET`, and the access token written by the dashboard, then logs every trade to MongoDB.

See `Algo_Trading_Guide.pdf` for the full strategy and setup walkthrough.
