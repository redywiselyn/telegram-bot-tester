import os
import requests
import pandas as pd
from binance.client import Client
import time
from datetime import datetime
import pytz

# ======================
# CONFIG
# ======================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

TIMEZONE = pytz.timezone("Asia/Jakarta")
START_HOUR = 6
END_HOUR = 21

client = Client()
sent_signals = set()

# ======================
# TELEGRAM
# ======================
def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}
    )

# ======================
# GET TOP 100 USDT PERP
# ======================
def get_top100_symbols():
    tickers = client.futures_ticker()
    usdt_pairs = [t for t in tickers if t['symbol'].endswith("USDT")]

    # Urutkan berdasarkan volume terbesar
    sorted_pairs = sorted(
        usdt_pairs,
        key=lambda x: float(x['quoteVolume']),
        reverse=True
    )

    top100 = [p['symbol'] for p in sorted_pairs[:100]]
    return top100

# ======================
# MA CROSS CHECK
# ======================
def check_ma(symbol):
    try:
        klines = client.futures_klines(symbol=symbol, interval='30m', limit=120)
        df = pd.DataFrame(klines)
        df['Close'] = df[4].astype(float)

        df['ma7'] = df['Close'].rolling(7).mean()
        df['ma25'] = df['Close'].rolling(25).mean()
        df['ma99'] = df['Close'].rolling(99).mean()

        last = df.iloc[-1]
        prev = df.iloc[-2]

        if prev['ma7'] < prev['ma25'] and last['ma7'] > last['ma25'] \
           and last['ma7'] > last['ma99'] and last['ma25'] > last['ma99']:
            return "BULLISH"

        if prev['ma7'] > prev['ma25'] and last['ma7'] < last['ma25'] \
           and last['ma7'] < last['ma99'] and last['ma25'] < last['ma99']:
            return "BEARISH"

        return None
    except:
        return None

# ======================
# START
# ======================
send("🚀 TOP 100 Crypto MA 30M Scanner Aktif")

symbols = get_top100_symbols()

while True:
    now = datetime.now(TIMEZONE)
    minute = now.minute
    hour = now.hour

    # Hanya scan tepat menit 00 & 30
    if minute in [0, 30]:

        if START_HOUR <= hour <= END_HOUR:

            print("Scanning Top 100...")
            found = False

            for symbol in symbols:
                signal = check_ma(symbol)
                key = f"{symbol}_{signal}"

                if signal and key not in sent_signals:
                    price = float(client.futures_symbol_ticker(symbol=symbol)['price'])

                    msg = f"{symbol}\n{'🟢 BULLISH' if signal=='BULLISH' else '🔴 BEARISH'}\nPrice: {price}"
                    send(msg)

                    sent_signals.add(key)
                    found = True
                    time.sleep(0.3)

            if not found:
                print("Tidak ada signal.")

        time.sleep(60)

    time.sleep(10)
