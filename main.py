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

# ================= STOCK LIST =================
stocks = [
    "BBCA.JK","BBRI.JK","BMRI.JK","TLKM.JK","ASII.JK",
    "UNTR.JK","ANTM.JK","ADRO.JK","MDKA.JK","GOTO.JK",
    "CPIN.JK","JPFA.JK","BRPT.JK","TPIA.JK","EXCL.JK",
    "ISAT.JK","PTBA.JK","SMGR.JK","KLBF.JK","ICBP.JK"
]
stocks = list(set(stocks))  # hapus duplikat

# ================= HELPER =================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def format_price(price):
    if price >= 1000:
        return "{:,.2f}".format(price)
    elif price >= 1:
        return "{:,.3f}".format(price)
    else:
        return "{:,.5f}".format(price)

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta>0,0).rolling(period).mean()
    loss = -delta.where(delta<0,0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ================= CRYPTO =================
def get_crypto_symbols():
    info = client.futures_exchange_info()
    return [s['symbol'] for s in info['symbols']
            if s['quoteAsset']=="USDT" and s['contractType']=="PERPETUAL" and s['status']=="TRADING"]

def check_crypto_signal(symbol):
    try:
        klines = client.futures_klines(symbol=symbol, interval='4h', limit=100)
        df = pd.DataFrame(klines)
        df[4] = df[4].astype(float)
        df[5] = df[5].astype(float)

        df['MA7'] = df[4].rolling(7).mean()
        df['MA25'] = df[4].rolling(25).mean()
        df['RSI'] = compute_rsi(df[4])

        last = df.iloc[-1]
        prev = df.iloc[-2]

        if prev['MA7'] < prev['MA25'] and last['MA7'] > last['MA25'] and last['RSI']>45:
            return "BULLISH"
        if prev['MA7'] > prev['MA25'] and last['MA7'] < last['MA25'] and last['RSI']<55:
            return "BEARISH"
        return None
    except:
        return None

# ================= MAIN =================
crypto_symbols = get_crypto_symbols()
stored_stock_message = ""
last_crypto_hour = -1
stock_report_sent = False

while True:
    now = pd.Timestamp.now()
    h, m = now.hour, now.minute

    # ---------------- CRYPTO ----------------
    if 6 <= h <= 20 and h % 2 == 0 and last_crypto_hour != h:
        last_crypto_hour = h
        bullish, bearish = [], []
        for sym in crypto_symbols:
            signal = check_crypto_signal(sym)
            price = float(client.futures_symbol_ticker(symbol=sym)['price'])
            coin_name = sym.replace("USDT","")
            if signal == "BULLISH":
                bullish.append(f"{coin_name}: Entry {format_price(price)}")
            elif signal == "BEARISH":
                bearish.append(f"{coin_name}: Entry {format_price(price)}")

        msg = "CRYPTO :\n\n🟢 BULLISH:\n" + "\n".join(bullish) + "\n\n🔴 BEARISH:\n" + "\n".join(bearish)
        send_telegram(msg)

    # ---------------- STOCKS SCAN ----------------
    if h == 17 and m < 5:  # market close
        stock_msg = ""
        for sym in stocks:
            try:
                df = yf.download(sym, period="6mo", interval="1d", progress=False)
                df['MA20'] = df['Close'].rolling(20).mean()
                df['MA50'] = df['Close'].rolling(50).mean()
                df['RSI'] = compute_rsi(df['Close'])
                last = df.iloc[-1]
                prev = df.iloc[-2]
                if prev['MA20'] < prev['MA50'] and last['MA20'] > last['MA50'] and last['RSI']>50:
                    stock_msg += f"{sym}: Entry {format_price(last['Close'])}\n"
                elif prev['MA20'] > prev['MA50'] and last['MA20'] < last['MA50'] and last['RSI']<50:
                    stock_msg += f"{sym}: Entry {format_price(last['Close'])}\n"
            except:
                continue
        stored_stock_message = stock_msg
        stock_report_sent = False

    # ---------------- SEND STOCKS JAM 18:00 ----------------
    if h == 18 and not stock_report_sent:
        if stored_stock_message:
            send_telegram("STOCKS :\n\n" + stored_stock_message)
        stock_report_sent = True  # pastikan hanya sekali

    time.sleep(60)
