"""
Crypto Price Scraper
Fetches BTC, ETH, BNB prices from CoinGecko (free, no API key needed)
and stores them in PostgreSQL every 60 seconds.
"""

import os
import time
import logging
import requests
import psycopg2
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

DB_URL = os.getenv("DATABASE_URL", "postgresql://user:password@postgres:5432/crypto")
SCRAPE_INTERVAL = int(os.getenv("SCRAPE_INTERVAL", "60"))
COINS = ["bitcoin", "ethereum", "binancecoin"]
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"

def get_conn():
    return psycopg2.connect(DB_URL)

def init_db(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS crypto_prices (
                id          SERIAL PRIMARY KEY,
                coin        VARCHAR(50) NOT NULL,
                price_usd   NUMERIC(18, 6) NOT NULL,
                market_cap  NUMERIC(24, 2),
                volume_24h  NUMERIC(24, 2),
                change_24h  NUMERIC(8, 4),
                fetched_at  TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            CREATE INDEX IF NOT EXISTS idx_crypto_coin_time
                ON crypto_prices (coin, fetched_at DESC);
        """)
    conn.commit()
    log.info("Database initialised")

def fetch_prices():
    params = {
        "ids": ",".join(COINS),
        "vs_currencies": "usd",
        "include_market_cap": "true",
        "include_24hr_vol": "true",
        "include_24hr_change": "true",
    }
    resp = requests.get(COINGECKO_URL, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()

def store_prices(conn, data: dict):
    rows = []
    for coin, values in data.items():
        rows.append((
            coin,
            values.get("usd"),
            values.get("usd_market_cap"),
            values.get("usd_24h_vol"),
            values.get("usd_24h_change"),
            datetime.now(timezone.utc),
        ))
    with conn.cursor() as cur:
        cur.executemany("""
            INSERT INTO crypto_prices
                (coin, price_usd, market_cap, volume_24h, change_24h, fetched_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, rows)
    conn.commit()
    log.info("Stored %d rows: %s", len(rows), {r[0]: r[1] for r in rows})

def main():
    log.info("Connecting to database…")
    while True:
        try:
            conn = get_conn()
            break
        except Exception as e:
            log.warning("DB not ready (%s), retrying in 5s…", e)
            time.sleep(5)
    init_db(conn)
    log.info("Scraper started — interval: %ds", SCRAPE_INTERVAL)
    while True:
        try:
            data = fetch_prices()
            store_prices(conn, data)
        except requests.RequestException as e:
            log.error("Fetch error: %s", e)
        except Exception as e:
            log.error("Unexpected error: %s", e)
            try:
                conn = get_conn()
            except Exception:
                pass
        time.sleep(SCRAPE_INTERVAL)

if __name__ == "__main__":
    main()