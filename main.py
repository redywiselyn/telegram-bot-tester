import os
import requests

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TOKEN or not CHAT_ID:
    print("TOKEN atau CHAT_ID belum diset di Environment Variables")
    exit()

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

response = requests.post(
    url,
    data={
        "chat_id": CHAT_ID,
        "text": "✅ TEST BERHASIL! Bot Railway aktif."
    }
)

print(response.json())
