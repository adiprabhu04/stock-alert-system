import yfinance as yf
from datetime import datetime, timezone

def get_latest_price(symbol: str):
    """
    Returns (price, ts_iso) using 1m bars if available; falls back to last daily close.
    """
    try:
        tkr = yf.Ticker(symbol)
        hist = tkr.history(period="1d", interval="1m")
        if hist is not None and not hist.empty:
            price = float(hist["Close"].iloc[-1])
            ts = hist.index[-1].to_pydatetime().astimezone(timezone.utc).isoformat()
            return price, ts
        daily = tkr.history(period="5d", interval="1d")
        if daily is not None and not daily.empty:
            price = float(daily["Close"].iloc[-1])
            ts = datetime.now(timezone.utc).isoformat()
            return price, ts
    except Exception as e:
        print(f"[fetch_stock] Error fetching {symbol}: {e}")
    return None, None
