import yfinance as yf
import pandas as pd
import requests

# ==============================
# TELEGRAM CONFIG
# ==============================
TOKEN = "ISI_TOKEN_KAMU"
CHAT_ID = "ISI_CHAT_ID"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})

# ==============================
# LIST 100 SAHAM INDONESIA
# ==============================

stocks = list(set([
"BBCA.JK","BBRI.JK","BMRI.JK","BBNI.JK","TLKM.JK",
"ASII.JK","UNTR.JK","ANTM.JK","ADRO.JK","MDKA.JK",
"GOTO.JK","CPIN.JK","JPFA.JK","BRPT.JK","TPIA.JK",
"EXCL.JK","ISAT.JK","PTBA.JK","SMGR.JK","KLBF.JK",
"ICBP.JK","INDF.JK","INCO.JK","ITMG.JK","TBIG.JK",
"TOWR.JK","AKRA.JK","AMRT.JK","MNCN.JK","RAJA.JK",
"WIFI.JK","INKP.JK","AUTO.JK","BJBR.JK","BBTN.JK",
"BRMS.JK","DSSA.JK","ADHI.JK","PTRO.JK","MSIN.JK",
"ENRG.JK","DSNG.JK","AADI.JK","KPIG.JK","RATU.JK",
"TAPG.JK","BREN.JK","AMMN.JK","PGAS.JK","MEDC.JK",
"ACES.JK","ERAA.JK","SIDO.JK","HMSP.JK","MYOR.JK",
"SCMA.JK","PWON.JK","CTRA.JK","BSDE.JK","SMRA.JK",
"DMAS.JK","KIJA.JK","WIKA.JK","PTPP.JK","JSMR.JK",
"BUKA.JK","DOID.JK","HRUM.JK","INDY.JK","ADMR.JK",
"DEWA.JK","ELSA.JK","HEAL.JK","MIKA.JK","SILO.JK",
"RALS.JK","LPPF.JK","MAPA.JK","MAPB.JK","UNVR.JK",
"STTP.JK","ULTJ.JK","WOOD.JK","FREN.JK","MTEL.JK",
"BDMN.JK","BNGA.JK","BNLI.JK","PNBN.JK","ARTO.JK",
"BBYB.JK","MEGA.JK","NISP.JK","BTPS.JK","BFIN.JK"
]))

# ==============================
# SCAN STOCKS
# ==============================

bullish = []
bearish = []

print("Scanning Stocks...")

for stock in stocks:

    try:
        df = yf.download(stock, period="6mo", interval="1d", progress=False)

        if len(df) < 60:
            continue

        df['MA20'] = df['Close'].rolling(20).mean()
        df['MA50'] = df['Close'].rolling(50).mean()

        last = df.iloc[-1]
        prev = df.iloc[-2]

        # Bullish cross
        if prev['MA20'] < prev['MA50'] and last['MA20'] > last['MA50']:
            bullish.append(stock.replace(".JK",""))

        # Bearish cross
        elif prev['MA20'] > prev['MA50'] and last['MA20'] < last['MA50']:
            bearish.append(stock.replace(".JK",""))

    except:
        continue

# ==============================
# FORMAT MESSAGE
# ==============================

msg = "STOCKS :\n\n"

msg += "🟢 BULLISH:\n"
if bullish:
    msg += ", ".join(bullish)
else:
    msg += "-"

msg += "\n\n🔴 BEARISH:\n"
if bearish:
    msg += ", ".join(bearish)
else:
    msg += "-"

# ==============================
# SEND TELEGRAM
# ==============================

send_telegram(msg)

print("Scan selesai")
