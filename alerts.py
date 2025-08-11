import os
from twilio.rest import Client

def _twilio_client():
    sid = os.getenv("TWILIO_SID")
    token = os.getenv("TWILIO_TOKEN")
    if not sid or not token:
        return None
    try:
        return Client(sid, token)
    except Exception:
        return None

def send_alert(message: str):
    """
    If Twilio creds exist, send SMS; otherwise print to console.
    """
    client = _twilio_client()
    to = os.getenv("TWILIO_TO")
    from_ = os.getenv("TWILIO_FROM")
    if client and to and from_:
        client.messages.create(body=message, from_=from_, to=to)
    print(f"[ALERT] {message}")

def crossed_absolute(symbol: str, price: float) -> float | None:
    """
    Returns threshold if an absolute threshold is active for this symbol; else None.
    """
    default = float(os.getenv("ALERT_DEFAULT", "999999"))
    per = os.getenv(f"ALERT_{symbol.upper()}")
    threshold = float(per) if per else default
    return threshold if threshold < 999999 else None

def pct_jump(old: float, new: float, pct: float) -> bool:
    if old <= 0:
        return False
    return ((new - old) / old) * 100.0 >= pct
