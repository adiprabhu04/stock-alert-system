import sqlite3
from pathlib import Path

DB_PATH = Path("stocks.db")

DDL = """
CREATE TABLE IF NOT EXISTS prices(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol TEXT NOT NULL,
  price REAL NOT NULL,
  ts TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_prices_symbol_ts ON prices(symbol, ts);
"""

def init_db():
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        for stmt in DDL.strip().split(";"):
            if stmt.strip():
                cur.execute(stmt)
        con.commit()

def insert_price(symbol: str, price: float, ts: str):
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            "INSERT INTO prices(symbol, price, ts) VALUES(?,?,?)",
            (symbol.upper(), float(price), ts),
        )
        con.commit()

def latest(symbol: str):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.execute(
            "SELECT price, ts FROM prices WHERE symbol=? ORDER BY ts DESC LIMIT 1",
            (symbol.upper(),),
        )
        return cur.fetchone()

def last_n(symbol: str, n: int = 100):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.execute(
            "SELECT price, ts FROM prices WHERE symbol=? ORDER BY ts DESC LIMIT ?",
            (symbol.upper(), n),
        )
        rows = cur.fetchall()
        return [{"price": r[0], "timestamp": r[1]} for r in rows][::-1]
