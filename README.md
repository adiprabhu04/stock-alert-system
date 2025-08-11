# Real-Time Stock Price Alert System

Python + Flask service that fetches minute-level stock prices (Yahoo Finance via `yfinance`), stores them to SQLite, exposes REST APIs, and sends alerts (console + optional Twilio SMS) when absolute thresholds are crossed (edge-triggered) or when % jumps occur over the last N minutes. Optional NSE market-hours filter.

## Tech
- Python, Flask, SQLite
- yfinance (data), schedule (background job)
- Twilio (optional SMS)
- dotenv (env config)

## Run
```bash
python -m venv venv
# activate venv, then:
pip install -r requirements.txt
cp .env.example .env  # fill symbols/alerts; keep Twilio blank to log to console
python app.py
