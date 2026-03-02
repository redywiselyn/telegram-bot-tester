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

# ======================
# TELEGRAM
# ======================
def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}
    )

# ======================
# GET TOP 100 PERP USDT
# ======================
def get_top100():
    tickers = client.futures_ticker()
    usdt = [t for t in tickers if t['symbol'].endswith("USDT")]

    sorted_pairs = sorted(
        usdt,
        key=lambda x: float(x['quoteVolume']),
        reverse=True
    )

    return [p['symbol'] for p in sorted_pairs[:100]]

# ======================
# CHECK MA CROSS
# ======================
def check_signal(symbol):
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
            return "🟢"

        if prev['ma7'] > prev['ma25'] and last['ma7'] < last['ma25'] \
           and last['ma7'] < last['ma99'] and last['ma25'] < last['ma99']:
            return "🔴"

        return None
    except:
        return None

# ======================
# START
# ======================
send("🚀 TOP 100 Crypto MA 30M Scanner Aktif")

symbols = get_top100()

while True:
    now = datetime.now(TIMEZONE)
    minute = now.minute
    hour = now.hour

    if minute in [0, 30] and START_HOUR <= hour <= END_HOUR:

        bullish = []
        bearish = []

        for symbol in symbols:
            signal = check_signal(symbol)
            if signal == "🟢":
                bullish.append(symbol.replace("USDT",""))
            elif signal == "🔴":
                bearish.append(symbol.replace("USDT",""))

        if bullish or bearish:

            message = f"⏰ {now.strftime('%H:%M WIB')}\n\n"

            if bullish:
                message += "🟢 BULLISH:\n"
                message += ", ".join(bullish) + "\n\n"

            if bearish:
                message += "🔴 BEARISH:\n"
                message += ", ".join(bearish)

            send(message)

        time.sleep(60)

    time.sleep(10)
