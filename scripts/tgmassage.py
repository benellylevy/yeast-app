import requests
import time

TELEGRAM_BOT_TOKEN = "PUT_YOUR_TELEGRAM_BOT_TOKEN_HERE"  # הכנס כאן את הטוקן שלך
TELEGRAM_CHAT_ID = "PUT_YOUR_CHAT_ID_HERE"  # הצ'אט האישי שלך (כמספר)

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)

    if response.status_code == 200:
        pass
    else:
        print(f"❌ שגיאה בשליחת הודעת טלגרם: {response.status_code} - {response.json()}")

def Vacuum():
    switch_url = "http://192.168.1.78/netio.cgi?pass=netio&output3=1"

    # Send a GET request and store the response
    response = requests.get(switch_url)
    print(response)


    # Wait for 15 seconds
    time.sleep(15)

    switch_url = "http://192.168.1.78/netio.cgi?pass=netio&output3=0"

    # Send a GET request and store the response
    response = requests.get(switch_url)
    print(response)

def send_telegram_photo(photo_path, caption=None):
    """
    שולחת תמונה דרך Telegram.
    
    :param photo_path: הנתיב לקובץ התמונה (למשל "graph.png").
    :param caption: טקסט (אופציונלי) שילווה את התמונה.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "caption": caption if caption else "",
        "parse_mode": "Markdown"
    }
    try:
        with open(photo_path, "rb") as photo_file:
            files = {"photo": photo_file}
            response = requests.post(url, data=data, files=files)
        
        if response.status_code == 200:
            print("✅ התמונה נשלחה בהצלחה!")
        else:
            print(f"❌ שגיאה בשליחת התמונה: {response.status_code} - {response.json()}")
    except Exception as e:
        print("❌ שגיאה בקוד:", e)