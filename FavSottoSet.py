import requests
from bs4 import BeautifulSoup
import time
import datetime

# === CONFIG TELEGRAM ===
TELEGRAM_TOKEN = "7603257716:AAHYHZF8H6S-LyuXp8l-h1W0h40fSPp3WZU"
TELEGRAM_CHAT_ID = "66336138"

# === CONFIG ===
CHECK_INTERVAL_MINUTES = 2
QUOTE_MAX = 1.70
sent_alerts = set()

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        requests.post(url, data=payload)
    except:
        print("Errore invio messaggio Telegram")

def check_diretta():
    url = "https://www.diretta.it/tennis/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    for div in soup.select("div.event__match--live"):
        try:
            league = div.get("title", "")
            if not any(t in league.lower() for t in ["atp", "wta"]):
                continue

            home = div.select_one(".event__participant--home").text.strip()
            away = div.select_one(".event__participant--away").text.strip()
            set_home = div.select_one(".event__scores .event__score--home").text.strip()
            set_away = div.select_one(".event__scores .event__score--away").text.strip()

            odds_home = div.get("data-odd1")
            odds_away = div.get("data-odd2")

            if not odds_home or not odds_away:
                continue

            odds_home = float(odds_home)
            odds_away = float(odds_away)

            if odds_home < odds_away:
                favorito = home
                quota_fav = odds_home
                avversario = away
                sfav = odds_away
                ha_perso_set = int(set_home) < int(set_away)
            else:
                favorito = away
                quota_fav = odds_away
                avversario = home
                sfav = odds_home
                ha_perso_set = int(set_away) < int(set_home)

            if quota_fav >= QUOTE_MAX:
                continue

            match_key = f"{favorito} vs {avversario}"

            if ha_perso_set and match_key not in sent_alerts:
                msg = f"""   [{league}]
                           Il favorito {favorito} ha perso il 1° set contro {avversario}.
                           Quote live: {favorito} @{quota_fav:.2f} vs {avversario} @{sfav:.2f}"""
                send_telegram_message(msg)
                sent_alerts.add(match_key)

        except Exception as e:
            continue

while True:
    print(f"[{datetime.datetime.now()}] Controllo in corso...")
    try:
        check_diretta()
    except Exception as e:
        print("Errore:", e)

    time.sleep(CHECK_INTERVAL_MINUTES * 60)
