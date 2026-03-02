# ================= Crypto + Stocks Scanner Final =================
import os
import time
import requests
import pandas as pd
from binance.client import Client
import yfinance as yf

# ================= CONFIG =================
TOKEN = os.getenv("TOKEN")             # Telegram Bot Token
CHAT_ID = int(os.getenv("CHAT_ID"))    # Telegram Chat ID
client = Client()                       # Binance client

# ================= STOCK LIST =================
stocks = [
    # IDX Kompas100
    "AADI.JK","ACES.JK","ADMR.JK","ADRO.JK","AKRA.JK",
    "AMMN.JK","AMRT.JK","ANTM.JK","ARCI.JK","ARTO.JK",
    "ASII.JK","BBCA.JK","BBNI.JK","BBRI.JK","BBTN.JK",
    "BBYB.JK","BRIS.JK","BRMS.JK","BRPT.JK","BSDE.JK",
    "BTPS.JK","BUKA.JK","BUMI.JK","BUVA.JK","CBDK.JK",
    "CMRY.JK","CPIN.JK","CTRA.JK","CUAN.JK","DEWA.JK",
    "DSNG.JK","DSSA.JK","ELSA.JK","EMTK.JK","ENRG.JK",
    "ERAA.JK","ESSA.JK","EXCL.JK","FILM.JK","GOTO.JK",
    "HEAL.JK","HRTA.JK","HRUM.JK","ICBP.JK","IMPC.JK",
    "INET.JK","INCO.JK","INDF.JK","INDY.JK","INKP.JK",
    "INTP.JK","ISAT.JK","ITMG.JK","JPFA.JK","JSMR.JK",
    "KIJA.JK","KLBF.JK","KPIG.JK","MAPA.JK","MAPI.JK",
    "MBMA.JK","MDKA.JK","MEDC.JK","MIKA.JK","MTEL.JK",
    "MYOR.JK","NCKL.JK","PANI.JK","PGAS.JK","PNLF.JK",
    "PSAB.JK","PTBA.JK","PTRO.JK","PWON.JK","RAJA.JK",
    "RATU.JK","SCMA.JK","SGER.JK","SIDO.JK","SMGR.JK",
    "SMIL.JK","SMRA.JK","SSIA.JK","TAPG.JK","TCPI.JK",
    "TINS.JK","TLKM.JK","TOBA.JK","TOWR.JK","TPIA.JK",
    "UNTR.JK","UNVR.JK","WIFI.JK","WIRG.JK",
    
    # MSCI IMI tambahan
    "BREN.JK","DSSA.JK","CUAN.JK"
]

# Hapus duplikat otomatis
stocks = list(set(stocks))

# ================= HELPER FUNCTIONS =================
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

# ================= CRYPTO FUNCTIONS =================
def get_crypto_symbols():
    info = client.futures_exchange_info()
    return [s['symbol'] for s in info['symbols']
            if s['quoteAsset']=="USDT" and s['contractType']=="PERPETUAL" and s['status']=="TRADING"]

def check_crypto_signal(symbol):
    try:
        klines = client.futures_klines(symbol=symbol, interval='30m', limit=150)
        df = pd.DataFrame(klines)
        df[4] = df[4].astype(float)  # Close
        df[5] = df[5].astype(float)  # Volume

        df['MA7'] = df[4].rolling(7).mean()
        df['MA25'] = df[4].rolling(25).mean()
        df['RSI'] = compute_rsi(df[4])

        last = df.iloc[-1]
        prev = df.iloc[-2]

        # BULLISH
        if prev['MA7'] < prev['MA25'] and last['MA7'] > last['MA25'] and last['RSI']>45 and last[5]>0:
            return "BULLISH"
        # BEARISH
        if prev['MA7'] > prev['MA25'] and last['MA7'] < last['MA25'] and last['RSI']<55 and last[5]>0:
            return "BEARISH"
        return None
    except:
        return None

# ================= MAIN LOOP =================
crypto_symbols = get_crypto_symbols()
stored_stock_message = ""  # Simpan hasil scan saham

while True:
    now = pd.Timestamp.now()
    now_hour = now.hour

    # ---------------- CRYPTO 30M ----------------
    crypto_msg = "CRYPTO :\n\n🟢 BULLISH:\n"
    bullish, bearish = [], []

    if 6 <= now_hour <= 21:
        for sym in crypto_symbols:
            signal = check_crypto_signal(sym)
            price = float(client.futures_symbol_ticker(symbol=sym)['price'])
            if signal=="BULLISH":
                bullish.append(f"{sym}: Entry {format_price(price)}")
            elif signal=="BEARISH":
                bearish.append(f"{sym}: Entry {format_price(price)}")

        bullish = bullish[:10]
        bearish = bearish[:10]
        crypto_msg += "\n".join(bullish) + "\n\n🔴 BEARISH:\n" + "\n".join(bearish)
    else:
        crypto_msg += "\n\n🔴 BEARISH:\n"

    # ---------------- STOCKS SCAN ----------------
    if now_hour == 17:  # Market close
        stock_msg = "STOCKS :\n"
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
        stored_stock_message = stock_msg  # simpan hasil scan saham

    # ---------------- SEND TELEGRAM ----------------
    full_msg = crypto_msg
    if now_hour == 8 and stored_stock_message:  # Kirim stocks jam 08:00
        full_msg += "\n\n" + stored_stock_message
        stored_stock_message = ""  # reset setelah kirim

    send_telegram(full_msg)

    # ---------------- SLEEP ----------------
    if 6 <= now_hour <= 21:
        time.sleep(1800)  # 30 menit untuk crypto
    else:
        time.sleep(3600)  # di luar jam crypto scan
