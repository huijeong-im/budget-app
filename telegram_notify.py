import requests
import os

BOT_TOKEN = "8533743870:AAGvNrJ2uEXg-dcr9Yzdmu82lndimMJtsCA"
CHAT_ID_WIFE    = "8783395762"
CHAT_ID_HUSBAND = "7169251813"

def send_telegram(chat_id, message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    res = requests.post(url, data={"chat_id": chat_id, "text": message})
    return res.json()

def send_both(message):
    r1 = send_telegram(CHAT_ID_WIFE, message)
    r2 = send_telegram(CHAT_ID_HUSBAND, message)
    print(f"  희정: {r1.get('ok')} / 기태: {r2.get('ok')}")
