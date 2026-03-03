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
stocks = list(set([
    "BBCA.JK","BBRI.JK","BMRI.JK","TLKM.JK","ASII.JK",
    "UNTR.JK","ANTM.JK","ADRO.JK","MDKA.JK","GOTO.JK",
    "CPIN.JK","JPFA.JK","BRPT.JK","TPIA.JK","EXCL.JK",
    "ISAT.JK","PTBA.JK","SMGR.JK","KLBF.JK","ICBP.JK",
    "ADHI.JK","BBTN.JK","BJBR.JK","BRMS.JK","DSSA.JK",
    "AMRT.JK","MSIN.JK","RAJA.JK","WIFI.JK","INKP.JK",
    "TBIG.JK","ITMG.JK","TOWR.JK","AKRA.JK","ASRI.JK",
    "AUTO.JK","BBYB.JK","INDF.JK","INCO.JK","MNCN.JK",
    "PTRO.JK","AALI.JK","TBLA.JK","RALS.JK","PTPP.JK",
    "SILO.JK","TKIM.JK","UNVR.JK","WIKA.JK","WSKT.JK",
    "AMMN.JK","BREN.JK","DSNG.JK","ENRG.JK","RATU.JK",
    "TAPG.JK","AADI.JK","KPIG.JK"
]))

# ================= HELPER =================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta>0,0).rolling(period).mean()
    loss = -delta.where(delta<0,0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ================= CRYPTO =================
def get_top100_symbols():
    tickers = client.futures_ticker()
    df = pd.DataFrame(tickers)
    df = df[df['symbol'].str.endswith("USDT")]
    df['quoteVolume'] = df['quoteVolume'].astype(float)
    df = df.sort_values("quoteVolume", ascending=False)
    return df['symbol'].head(100).tolist()

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

        if prev['MA7'] < prev['MA25'] and last['MA7'] > last['MA25'] and last['RSI']>45:
            return "BULLISH"
        if prev['MA7'] > prev['MA25'] and last['MA7'] < last['MA25'] and last['RSI']<55:
            return "BEARISH"
        return None
    except:
        return None

# ================= MAIN LOOP =================
last_crypto_hour = -1
stock_sent_today = False

while True:
    now = pd.Timestamp.now()
    h = now.hour

    # -------- CRYPTO (06:00 - 20:00 tiap 2 jam) --------
    if 6 <= h <= 20 and h % 2 == 0 and last_crypto_hour != h:
        last_crypto_hour = h
        crypto_symbols = get_top100_symbols()

        bullish, bearish = [], []

        for sym in crypto_symbols:
            signal = check_crypto_signal(sym)
            coin = sym.replace("USDT","")
            if signal == "BULLISH":
                bullish.append(coin)
            elif signal == "BEARISH":
                bearish.append(coin)

        msg = "CRYPTO :\n\n🟢 BULLISH:\n" + "\n".join(bullish) + \
              "\n\n🔴 BEARISH:\n" + "\n".join(bearish)

        send_telegram(msg)

    # -------- STOCKS (KIRIM 18:00) --------
    if h == 18 and not stock_sent_today:
        bullish_stock, bearish_stock = [], []

        for sym in stocks:
            try:
                df = yf.download(sym, period="6mo", interval="1d", progress=False)
                df['MA20'] = df['Close'].rolling(20).mean()
                df['MA50'] = df['Close'].rolling(50).mean()
                df['RSI'] = compute_rsi(df['Close'])

                last = df.iloc[-1]
                prev = df.iloc[-2]

                if prev['MA20'] < prev['MA50'] and last['MA20'] > last['MA50'] and last['RSI']>50:
                    bullish_stock.append(sym.replace(".JK",""))
                elif prev['MA20'] > prev['MA50'] and last['MA20'] < last['MA50'] and last['
