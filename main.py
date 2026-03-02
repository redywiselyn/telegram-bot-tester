# ===== Crypto + Saham Scanner Final (Tanpa TP/SL) =====
import os
import time
import requests
import pandas as pd
from binance.client import Client
import yfinance as yf

# ==============================
# CONFIG
# ==============================
TOKEN = os.getenv("TOKEN")        # Telegram Bot Token
CHAT_ID = int(os.getenv("CHAT_ID"))  # Telegram Chat ID

client = Client()

# ==============================
# STOCK LIST (IDX + MSCI)
# ==============================
stocks = [
    "BBCA.JK","BBRI.JK","BMRI.JK","TLKM.JK","ASII.JK",
    "UNTR.JK","ANTM.JK","ADRO.JK","MDKA.JK","GOTO.JK",
    # ... tambahkan semua top IDX + MSCI
]

# ==============================
# HELPER FUNCTIONS
# ==============================
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
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def compute_adx(df, period=14):
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L','H-PC','L-PC']].max(axis=1)
    df['+DM'] = df['High'].diff()
    df['-DM'] = -df['Low'].diff()
    df['+DM'] = df['+DM'].where((df['+DM']>df['-DM']) & (df['+DM']>0),0)
    df['-DM'] = df['-DM'].where((df['-DM']>df['+DM']) & (df['-DM']>0),0)
    TR14 = df['TR'].rolling(period).sum()
    plus14 = df['+DM'].rolling(period).sum()
    minus14 = df['-DM'].rolling(period).sum()
    plusDI = 100 * (plus14 / TR14)
    minusDI = 100 * (minus14 / TR14)
    dx = 100 * abs(plusDI - minusDI) / (plusDI + minusDI)
    adx = dx.rolling(period).mean()
    return adx

# ==============================
# CRYPTO FUNCTIONS
# ==============================
def get_crypto_symbols():
    info = client.futures_exchange_info()
    return [s['symbol'] for s in info['symbols']
            if s['quoteAsset']=="USDT" and s['contractType']=="PERPETUAL" and s['status']=="TRADING"]

def check_crypto_signal(symbol):
    try:
        klines = client.futures_klines(symbol=symbol, interval='30m', limit=150)
        df = pd.DataFrame(klines)
        df[2] = df[2].astype(float)  # High
        df[3] = df[3].astype(float)  # Low
        df[4] = df[4].astype(float)  # Close
        df[5] = df[5].astype(float)  # Volume

        # MA
        df['MA7'] = df[4].rolling(7).mean()
        df['MA25'] = df[4].rolling(25).mean()

        # RSI
        df['RSI'] = compute_rsi(df[4])

        # ADX
        df['ADX'] = compute_adx(df)

        # Volume avg
        df['VolAvg20'] = df[5].rolling(20).mean()

        last = df.iloc[-1]
        prev = df.iloc[-2]

        # Signal bullish
        if prev['MA7'] < prev['MA25'] and last['MA7'] > last['MA25']:
            if last['RSI']>50 and last['ADX']>25 and last[5]>last['VolAvg20']:
                return "BULLISH"
        # Signal bearish
        if prev['MA7'] > prev['MA25'] and last['MA7'] < last['MA25']:
            if last['RSI']<50 and last['ADX']>25 and last[5]>last['VolAvg20']:
                return "BEARISH"
        return None
    except:
        return None

# ==============================
# MAIN LOOP
# ==============================
crypto_symbols = get_crypto_symbols()

while True:
    now_hour = int(pd.Timestamp.now().hour)
    # ================= Crypto 30m 06:00-21:00 =================
    if 6 <= now_hour <= 21:
        bullish, bearish = [], []
        for sym in crypto_symbols:
            signal = check_crypto_signal(sym)
            price = float(client.futures_symbol_ticker(symbol=sym)['price'])
            if signal=="BULLISH":
                bullish.append(f"{sym}: Entry {format_price(price)}")
            elif signal=="BEARISH":
                bearish.append(f"{sym}: Entry {format_price(price)}")

        # Ambil Top 10 strongest
        bullish = bullish[:10]
        bearish = bearish[:10]

        crypto_msg = "CRYPTO :\n\n🟢 BULLISH:\n" + ("\n".join(bullish)) + "\n\n🔴 BEARISH:\n" + ("\n".join(bearish))
    else:
        crypto_msg = "CRYPTO :\n\n🟢 BULLISH:\n\n🔴 BEARISH:\n"

    # ================= Stock Daily =================
    stock_msg = "STOCKS :\n"
    if now_hour == 17:  # market close
        for sym in stocks:
            try:
                df = yf.download(sym, period="6mo", interval="1d", progress=False)
                df['MA20'] = df['Close'].rolling(20).mean()
                df['MA50'] = df['Close'].rolling(50).mean()
                df['VolAvg20'] = df['Volume'].rolling(20).mean()
                df['RSI'] = compute_rsi(df['Close'])
                last = df.iloc[-1]
                prev = df.iloc[-2]

                # Trend bullish
                if prev['MA20'] < prev['MA50'] and last['MA20'] > last['MA50'] and last['RSI']>50 and last['Volume']>last['VolAvg20']:
                    stock_msg += f"{sym}: Entry {format_price(last['Close'])}\n"
                # Trend bearish
                elif prev['MA20'] > prev['MA50'] and last['MA20'] < last['MA50'] and last['RSI']<50 and last['Volume']>last['VolAvg20']:
                    stock_msg += f"{sym}: Entry {format_price(last['Close'])}\n"
            except:
                continue

    # ================= Send Telegram =================
    full_msg = crypto_msg + "\n\n" + stock_msg
    send_telegram(full_msg)

    # ================= Sleep =================
    if 6 <= now_hour <= 21:
        time.sleep(1800)  # 30 menit untuk crypto
    else:
        time.sleep(3600)  # di luar jam crypto scan
