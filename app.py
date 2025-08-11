import os
import threading
import time
import schedule
from datetime import datetime, timezone, time as dtime
import pytz
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template

from fetch_stock import get_latest_price
from store_data import init_db, insert_price, latest, last_n
from alerts import send_alert, crossed_absolute, pct_jump

# ---------- env & config ----------
load_dotenv()
init_db()

SYMBOLS = [s.strip().upper() for s in os.getenv("SYMBOLS", "AAPL").split(",") if s.strip()]
PCT_WINDOW_MIN = int(os.getenv("PCT_WINDOW_MIN", "5"))
PCT_JUMP = float(os.getenv("PCT_JUMP", "0"))  # 0 disables
MARKET_HOURS_ONLY = os.getenv("MARKET_HOURS_ONLY", "false").lower() == "true"

# De-dupe set: "SYM:ISO_TS:ABS" or "SYM:ISO_TS:PCT"
ALERT_CACHE: set[str] = set()

app = Flask(__name__)

# ---------- helpers ----------
def in_nse_hours(now_utc: datetime) -> bool:
    if not MARKET_HOURS_ONLY:
        return True
    ist = pytz.timezone("Asia/Kolkata")
    now_ist = now_utc.astimezone(ist)
    if now_ist.weekday() > 4:  # Mon..Fri = 0..4
        return False
    return dtime(9, 15) <= now_ist.time() <= dtime(15, 30)

# ---------- polling ----------
def poll_once():
    now_utc = datetime.now(timezone.utc)
    if not in_nse_hours(now_utc):
        return

    for sym in SYMBOLS:
        price, ts = get_latest_price(sym)
        if price is None:
            continue

        ts = ts or now_utc.isoformat()
        insert_price(sym, price, ts)

        # ---- ABSOLUTE THRESHOLD (edge-triggered) ----
        th = crossed_absolute(sym, price)
        if th is not None:
            rows = last_n(sym, n=2)
            prev_price = rows[0]["price"] if len(rows) >= 2 else None
            crossed_edge = False
            if prev_price is None:
                crossed_edge = True  # first observation already above threshold
            else:
                if prev_price < th <= price:
                    crossed_edge = True

            if crossed_edge:
                key_abs = f"{sym}:{ts}:ABS"
                if key_abs not in ALERT_CACHE:
                    send_alert(f"{sym} crossed {th:.2f}: {price:.2f} at {ts}")
                    ALERT_CACHE.add(key_abs)

        # ---- PERCENT JUMP ----
        if PCT_JUMP > 0 and PCT_WINDOW_MIN > 0:
            rows = last_n(sym, n=max(PCT_WINDOW_MIN, 2))
            if len(rows) >= 2:
                old = rows[0]["price"]
                if pct_jump(old, price, PCT_JUMP):
                    key_pct = f"{sym}:{ts}:PCT"
                    if key_pct not in ALERT_CACHE:
                        send_alert(f"{sym} +{PCT_JUMP}% in ~{PCT_WINDOW_MIN}m → {price:.2f} at {ts}")
                        ALERT_CACHE.add(key_pct)

def scheduler_loop():
    # run immediately, then every minute
    poll_once()
    schedule.every(1).minutes.do(poll_once)
    while True:
        schedule.run_pending()
        time.sleep(1)

# ---------- API ----------
@app.get("/")
def home():
    return render_template("index.html")

@app.get("/health")
def health():
    return {"status": "ok", "symbols": SYMBOLS, "market_hours_only": MARKET_HOURS_ONLY}

@app.get("/price/<symbol>")
def price(symbol):
    row = latest(symbol)
    if not row:
        return jsonify({"error": "No data"}), 404
    return jsonify({"symbol": symbol.upper(), "price": row[0], "timestamp": row[1]})

@app.get("/history/<symbol>")
def history(symbol):
    n = int(request.args.get("n", 100))
    n = max(1, min(n, 1000))
    return jsonify({"symbol": symbol.upper(), "data": last_n(symbol, n)})

@app.post("/alert/test")
def alert_test():
    msg = (request.json or {}).get("msg", "Test alert from stock-alert-system")
    send_alert(msg)
    return {"sent": True}

@app.post("/debug/poll")
def debug_poll():
    poll_once()
    return {"ran": True, "at": datetime.now(timezone.utc).isoformat()}

# ---------- run ----------
if __name__ == "__main__":
    t = threading.Thread(target=scheduler_loop, daemon=True)
    t.start()
    app.run(port=5000, debug=True, use_reloader=False)
