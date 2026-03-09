import yfinance as yf
import pandas as pd
import numpy as np
import requests
import os
from ta.momentum import RSIIndicator

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram(msg):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url,data={"chat_id": TELEGRAM_CHAT_ID,"text": msg})


# =========================
# GET ALL IDX TICKERS
# =========================
def get_idx_tickers():

    url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"

    # fallback manual IDX list (lebih stabil)
    tickers = pd.read_html("https://id.wikipedia.org/wiki/Daftar_perusahaan_yang_tercatat_di_Bursa_Efek_Indonesia")[0]

    symbols = tickers.iloc[:,0].tolist()

    symbols = [s+".JK" for s in symbols]

    return symbols


tickers = get_idx_tickers()

print("Total saham:",len(tickers))

results = []


# =========================
# SCANNER
# =========================
for ticker in tickers:

    try:

        data = yf.download(ticker, period="6mo", progress=False)

        if len(data) < 60:
            continue

        data["MA50"] = data["Close"].rolling(50).mean()
        data["VolAvg"] = data["Volume"].rolling(20).mean()

        rsi = RSIIndicator(data["Close"], window=14)
        data["RSI"] = rsi.rsi()

        last = data.iloc[-1]

        price = last["Close"]
        ma50 = last["MA50"]
        volume = last["Volume"]
        volavg = last["VolAvg"]
        rsi_val = last["RSI"]

        breakout = price >= data["Close"].rolling(20).max().iloc[-1]
        trend = price > ma50
        vol_spike = volume > 2 * volavg
        early = rsi_val < 65

        score = 0

        if breakout:
            score += 30

        if trend:
            score += 25

        if vol_spike:
            score += 30

        if early:
            score += 15

        if score >= 60:

            results.append({
                "ticker": ticker,
                "score": score,
                "price": round(price,2),
                "vol_ratio": round(volume/volavg,2)
            })

    except:
        pass


# =========================
# RANKING
# =========================
df = pd.DataFrame(results)

if len(df) > 0:

    df = df.sort_values("score",ascending=False).head(10)

    message = "🚀 IDX BANDAR BAGGER SCANNER\n\nTOP SETUP:\n\n"

    for i,row in df.iterrows():

        message += f"{row['ticker']} | Score:{row['score']} | Vol:{row['vol_ratio']}x\n"

else:

    message = "⚠️ Scanner selesai.\n\nTidak ada setup kuat hari ini."


print(message)

send_telegram(message)
