import os
import time
import requests
import pandas as pd
from binance.client import Client
import yfinance as yf

# ================= CONFIG =================
TOKEN = os.getenv("TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))
client = Client()

# ================= TELEGRAM =================
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

# ================= RSI =================
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ================= GET TOP 100 CRYPTO =================
def get_top100_symbols():
    try:
        tickers = client.futures_ticker()
        df = pd.DataFrame(tickers)

        df = df[df['symbol'].str.endswith("USDT")]
        df['quoteVolume'] = pd.to_numeric(df['quoteVolume'], errors='coerce')
        df = df.dropna()
        df = df.sort_values("quoteVolume", ascending=False)

        return df['symbol'].head(100).tolist()
    except:
        return []

# ================= CRYPTO SIGNAL =================
def check_crypto_signal(symbol):
    try:
        klines = client.futures_klines(symbol=symbol, interval='4h', limit=100)
        df = pd.DataFrame(klines)
        df[4] = df[4].astype(float)

        df['MA7'] = df[4].rolling(7).mean()
        df['MA25'] = df[4].rolling(25).mean()
        df['RSI'] = compute_rsi(df[4])

        last = df.iloc[-1]
        prev = df.iloc[-2]

        if prev['MA7'] < prev['MA25'] and last['MA7'] > last['MA25'] and last['RSI'] > 45:
            return "BULLISH"
        if prev['MA7'] > prev['MA25'] and last['MA7'] < last['MA25'] and last['RSI'] < 55:
            return "BEARISH"
        return None
    except:
        return None

# ================= STOCK LIST =================
stocks = list(set([
    "BBCA.JK","BBRI.JK","BMRI.JK","TLKM.JK","ASII.JK",
    "UNTR.JK","ANTM.JK","ADRO.JK","MDKA.JK","GOTO.JK",
    "CPIN.JK","JPFA.JK","BRPT.JK","TPIA.JK","EXCL.JK",
    "ISAT.JK","PTBA.JK","SMGR.JK","KLBF.JK","ICBP.JK",
    "AMMN.JK","BREN.JK","DSNG.JK","ENRG.JK","AADI.JK"
]))

# ================= MAIN LOOP =================
last_crypto_sent = None
last_stock_sent = None

while True:
    now = pd.Timestamp.now()
    hour = now.hour
    minute = now.minute
    today = now.date()

    # ================= CRYPTO =================
    if 6 <= hour <= 20 and hour % 2 == 0 and minute == 0:
        if last_crypto_sent != hour:
            last_crypto_sent = hour

            symbols = get_top100_symbols()
            bullish, bearish = [], []

            for sym in symbols:
                signal = check_crypto_signal(sym)
                coin = sym.replace("USDT", "")
                if signal == "BULLISH":
                    bullish.append(coin)
                elif signal == "BEARISH":
                    bearish.append(coin)

            msg = "CRYPTO :\n\n🟢 BULLISH:\n"
            msg += "\n".join(bullish) if bullish else "-"
            msg += "\n\n🔴 BEARISH:\n"
            msg += "\n".join(bearish) if bearish else "-"

            send_telegram(msg)

    # ================= STOCKS =================
    if hour == 18 and minute == 0:
        if last_stock_sent != today:
            last_stock_sent = today

            bullish_stock, bearish_stock = [], []

            for sym in stocks:
                try:
                    df = yf.download(sym, period="6mo", interval="1d", progress=False)
                    df['MA20'] = df['Close'].rolling(20).mean()
                    df['MA50'] = df['Close'].rolling(50).mean()
                    df['RSI'] = compute_rsi(df['Close'])

                    last = df.iloc[-1]
                    prev = df.iloc[-2]

                    if prev['MA20'] < prev['MA50'] and last['MA20'] > last['MA50'] and last['RSI'] > 50:
                        bullish_stock.append(sym.replace(".JK",""))
                    elif prev['MA20'] > prev['MA50'] and last['MA20'] < last['MA50'] and last['RSI'] < 50:
                        bearish_stock.append(sym.replace(".JK",""))
                except:
                    continue

            msg = "STOCKS :\n\n🟢 BULLISH:\n"
            msg += "\n".join(bullish_stock) if bullish_stock else "-"
            msg += "\n\n🔴 BEARISH:\n"
            msg += "\n".join(bearish_stock) if bearish_stock else "-"

            send_telegram(msg)

    time.sleep(30)
