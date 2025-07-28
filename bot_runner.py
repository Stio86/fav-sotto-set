from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import requests
import time

def send_telegram_message(message):
    token = "7603257716:AAHYHZF8H6S-LyuXp8l-h1W0h40fSPp3WZU"
    chat_id = "66336138"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        r = requests.post(url, data=payload)
        print("📩 Telegram inviato" if r.status_code == 200 else f"❌ Telegram error: {r.text}")
    except Exception as e:
        print(f"❌ Errore Telegram: {e}")

def run_bot():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1200x1000")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    driver.get("https://www.diretta.it/tennis")
    print("[🔎] Apertura pagina Diretta.it...")

    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        ).click()
    except:
        pass

    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH,
                "//div[@class='filters__text filters__text--default' and text()='LIVE']"))
        ).click()
        time.sleep(3)
    except:
        print("[!] Errore click filtro LIVE")

    matches = driver.find_elements(By.CSS_SELECTOR, ".event__match--live")
    print(f"[+] Match live trovati: {len(matches)}")
    links = [f"https://www.diretta.it/partita/tennis/{m.get_attribute('id').split('_')[-1]}"
             for m in matches if m.get_attribute("id")]

    for i, link in enumerate(links):
        print(f"\n[🎾] Analisi partita {i+1}: {link}")
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get(link)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)

        b = driver.find_elements(By.CSS_SELECTOR, "a.wcl-breadcrumbItemLabel_ogiBc span")
        tipo = b[1].text.strip() if len(b) > 1 else "Sconosciuto"
        nome_t = b[2].text.strip() if len(b) > 2 else "Sconosciuto"
        if not any(t in tipo.lower() for t in ["atp", "wta", "challenger"]) or "doppio" in tipo.lower():
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            continue

        p = driver.find_elements(By.CSS_SELECTOR, "a.participant__participantName")
        g1 = p[0].text.strip() if p else "Gioc1"
        g2 = p[1].text.strip() if len(p) > 1 else "Gioc2"

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Quote pre-partita')]"))
            ).click()
            time.sleep(2)
        except:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            continue

        qels = driver.find_elements(By.CSS_SELECTOR, "span[data-testid='wcl-oddsValue']")
        q = [e.text.strip() for e in qels if e.text.strip() != "-"][:2]
        if len(q) < 2:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            continue
        q1, q2 = map(lambda x: float(x.replace(",", ".")), q)
        fav, qfav = (g1, q1) if q1 < q2 else (g2, q2)
        if qfav >= 1.70:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            continue

        try:
            score = driver.find_element(By.CSS_SELECTOR, "div.detailScore__wrapper.detailScore__live")
            punteggio = score.text.strip().replace("\n", "").replace(" ", "")
        except:
            punteggio = "N/A"

        if punteggio in ["0-1", "1-0"]:
            if (fav == g1 and punteggio == "0-1") or (fav == g2 and punteggio == "1-0"):
                msg = (
                    f"🚨 FAVORITO IN DIFFICOLTÀ\n\n"
                    f"📌 Torneo: {tipo} - {nome_t}\n"
                    f"👤 Match: {g1} vs {g2}\n"
                    f"🎯 Favorito: {fav} (quota {qfav})\n"
                    f"🟠 Sta perdendo il 1º set ({punteggio})\n"
                    f"🔗 {link}"
                )
                send_telegram_message(msg)

        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    driver.quit()
    print("\n[✓] Fine esecuzione.")
