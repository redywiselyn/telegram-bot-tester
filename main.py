import yfinance as yf
import pandas as pd
import ta
import requests
from datetime import datetime
import time

TELEGRAM_TOKEN = "ISI_TOKEN_BOT"
CHAT_ID = "ISI_CHAT_ID"

# ================================
# TELEGRAM FUNCTION
# ================================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    requests.post(url, data=payload)

# ================================
# CRYPTO TOP 100
# ================================
crypto_list = [
"BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","ADAUSDT","DOGEUSDT","TRXUSDT",
"TONUSDT","LINKUSDT","MATICUSDT","DOTUSDT","LTCUSDT","BCHUSDT","AVAXUSDT","SHIBUSDT",
"APTUSDT","NEARUSDT","ATOMUSDT","FILUSDT","ARBUSDT","OPUSDT","INJUSDT","SUIUSDT",
"PEPEUSDT","SEIUSDT","RUNEUSDT","AAVEUSDT","GRTUSDT","RNDRUSDT","STXUSDT","IMXUSDT",
"FETUSDT","ALGOUSDT","VETUSDT","HBARUSDT","MKRUSDT","EGLDUSDT","XTZUSDT","THETAUSDT",
"SANDUSDT","MANAUSDT","AXSUSDT","FLOWUSDT","KAVAUSDT","NEOUSDT","EOSUSDT","KLAYUSDT",
"CHZUSDT","MINAUSDT","ROSEUSDT","DYDXUSDT","LDOUSDT","GMXUSDT","ZECUSDT","COMPUSDT",
"SNXUSDT","1INCHUSDT","CRVUSDT","ENJUSDT","CAKEUSDT","BATUSDT","ZILUSDT","ONTUSDT",
"ICXUSDT","KSMUSDT","QTUMUSDT","DASHUSDT","ANKRUSDT","CELRUSDT","SKLUSDT","HOTUSDT",
"IOSTUSDT","SCUSDT","ZENUSDT","STORJUSDT","ARUSDT","CFXUSDT","WAVESUSDT","FLMUSDT",
"BANDUSDT","OCEANUSDT","BALUSDT","UMAUSDT","YFIUSDT","SXPUSDT","RSRUSDT","REEFUSDT",
"CTSIUSDT","API3USDT","LRCUSDT","MAGICUSDT","HOOKUSDT","TLMUSDT","ALPHAUSDT"
]

# ================================
# STOCK LIST (100 IDX)
# ================================
stock_list = [
"BBCA.JK","BMRI.JK","BBRI.JK","TLKM.JK","ASII.JK","ICBP.JK","UNVR.JK","INDF.JK",
"ADRO.JK","MDKA.JK","AMRT.JK","BRPT.JK","CPIN.JK","GOTO.JK","HRUM.JK","ITMG.JK",
"PGAS.JK","PTBA.JK","SMGR.JK","ANTM.JK","KLBF.JK","ACES.JK","AKRA.JK","ARTO.JK",
"BBNI.JK","BBTN.JK","BDMN.JK","BJBR.JK","BJTM.JK","BRIS.JK","BTPS.JK","CTRA.JK",
"DMAS.JK","ERAA.JK","EXCL.JK","HMSP.JK","INCO.JK","INKP.JK","JPFA.JK","JSMR.JK",
"LSIP.JK","MAIN.JK","MEDC.JK","MIKA.JK","MNCN.JK","PGEO.JK","PNLF.JK","PPRO.JK",
"PWON.JK","SCMA.JK","SIDO.JK","SMRA.JK","TBIG.JK","TINS.JK","TKIM.JK","TOWR.JK",
"UNTR.JK","WIKA.JK","WSKT.JK","ADHI.JK","DOID.JK","ELSA.JK","ESSA.JK","HEAL.JK",
"INDY.JK","ISAT.JK","MAPA.JK","MAPB.JK","MLBI.JK","MTDL.JK","MYOR.JK","NISP.JK",
"PNBN.JK","PTPP.JK","RAJA.JK","SAME.JK","SIMP.JK","SMSM.JK","SSMS.JK","TAPG.JK",
"TARA.JK","TPIA.JK","TRAM.JK","WEGE.JK","WOOD.JK","WTON.JK","ZINC.JK"
]

# ================================
# INDICATOR FUNCTION
# ================================
def analyze(df):
    df["EMA20"] = ta.trend.ema_indicator(df["Close"], window=20)
    df["EMA50"] = ta.trend.ema_indicator(df["Close"], window=50)
    df["RSI"] = ta.momentum.rsi(df["Close"], window=14)
    df["VOL_SMA10"] = df["Volume"].rolling(10).mean()

    last = df.iloc[-1]

    bullish = (
        last["Close"] > last["EMA20"] and
        last["EMA20"] > last["EMA50"] and
        last["RSI"] > 50 and
        last["Volume"] > last["VOL_SMA10"]
    )

    bearish = (
        last["Close"] < last["EMA20"] and
        last["EMA20"] < last["EMA50"] and
        last["RSI"] < 50 and
        last["Volume"] > last["VOL_SMA10"]
    )

    return bullish, bearish

# ================================
# CRYPTO SCAN
# ================================
def scan_crypto():
    bullish = []
    bearish = []

    for coin in crypto_list:
        try:
            symbol = coin.replace("USDT","-USDT")
            df = yf.download(symbol, interval="4h", period="10d")

            if len(df) < 50:
                continue

            bull, bear = analyze(df)

            name = coin.replace("USDT","")

            if bull:
                bullish.append(name)

            if bear:
                bearish.append(name)

        except:
            pass

    message = "CRYPTO\n\n"

    if bullish:
        message += "🟢 BULLISH:\n" + "\n".join(bullish) + "\n\n"

    if bearish:
        message += "🔴 BEARISH:\n" + "\n".join(bearish)

    send_telegram(message)

# ================================
# STOCK SCAN
# ================================
def scan_stocks():
    bullish = []
    bearish = []

    for stock in stock_list:
        try:
            df = yf.download(stock, period="6mo", interval="1d")

            if len(df) < 50:
                continue

            bull, bear = analyze(df)

            name = stock.replace(".JK","")

            if bull:
                bullish.append(name)

            if bear:
                bearish.append(name)

        except:
            pass

    message = "STOCKS\n\n"

    if bullish:
        message += "🟢 BULLISH:\n" + "\n".join(bullish) + "\n\n"

    if bearish:
        message += "🔴 BEARISH:\n" + "\n".join(bearish)

    send_telegram(message)

# ================================
# LOOP
# ================================
while True:

    now = datetime.now()

    hour = now.hour
    minute = now.minute

    # CRYPTO setiap 2 jam 06-20
    if hour in [6,8,10,12,14,16,18,20] and minute == 0:
        scan_crypto()
        time.sleep(60)

    # STOCKS jam 18:00
    if hour == 18 and minute == 0:
        scan_stocks()
        time.sleep(60)

    time.sleep(30)
