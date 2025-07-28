import time
from bot_core import avvia_bot_loop

while True:
    try:
        print("🔁 Avvio ciclo di analisi...")
        avvia_bot_loop()
        print("⏳ Attesa 120 secondi prima del prossimo ciclo...\n")
        time.sleep(120)
    except Exception as e:
        print(f"[❌] Errore nel ciclo: {e}")
        time.sleep(60)
