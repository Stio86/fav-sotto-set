from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import requests

# Config
URL = "https://www.diretta.it/tennis"
BOT_TOKEN = "7603257716:AAHYHZF8H6S-LyuXp8l-h1W0h40fSPp3WZU"
CHAT_ID = "66336138"

def avvia_bot_loop():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1200,1000")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(URL)
    print("[🔎] Apertura pagina Diretta.it...")

    try:
        accept_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        accept_btn.click()
        print("[✓] Cookie banner accettato.")
    except:
        print("[!] Cookie banner non trovato o già accettato.")

    try:
        live_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH,
                "//div[@class='filters__text filters__text--default' and text()='LIVE']"))
        )
        live_btn.click()
        print("[✓] Filtro LIVE cliccato.")
        time.sleep(3)
    except:
        print("[!] Errore nel click su filtro LIVE")

    matches = driver.find_elements(By.CSS_SELECTOR, ".event__match--live")
    print(f"[+] Match live trovati: {len(matches)}")

    links = []
    for match in matches:
        mid = match.get_attribute("id")
        if mid:
            code = mid.split("_")[-1]
            links.append(f"https://www.diretta.it/partita/tennis/{code}")

    for idx, link in enumerate(links):
        print(f"\n[🎾] Analisi partita {idx+1}: {link}")
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get(link)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)

        b = driver.find_elements(By.CSS_SELECTOR, "a.wcl-breadcrumbItemLabel_ogiBc span")
        tipo = b[1].text.strip() if len(b) > 1 else "Sconosciuto"
        nome_t = b[2].text.strip() if len(b) > 2 else "Sconosciuto"
        tipo_low = tipo.lower()
        if not any(x in tipo_low for x in ["atp", "wta", "challenger"]) or "doppio" in tipo_low:
            print(f"[⏭] Escluso: {tipo} - {nome_t}")
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            continue

        players = driver.find_elements(By.CSS_SELECTOR, "a.participant__participantName")
        g1 = players[0].text.strip() if players else "Gioc1"
        g2 = players[1].text.strip() if len(players)>1 else "Gioc2"

        try:
            tab = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Quote pre-partita')]"))
            )
            driver.execute_script("arguments[0].click();", tab)
            time.sleep(2)
        except Exception as e:
            print(f"[❌] Errore quote : {e}")
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            continue

        qs = driver.find_elements(By.CSS_SELECTOR, "span[data-testid='wcl-oddsValue']")
        qvals = [e.text.strip() for e in qs if e.text.strip() != "-"][:2]
        if len(qvals) < 2:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            continue
        q1, q2 = map(lambda x: float(x.replace(",", ".")), qvals)
        if q1 < q2:
            fav, qfav = g1, q1
            nonfav = g2
        else:
            fav, qfav = g2, q2
            nonfav = g1

        if qfav >= 1.70:
            print(f"ℹ️ Favorito {fav} quota {qfav:.2f} ≥ 1.70 → saltata")
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            continue

        try:
            div = driver.find_element(By.CSS_SELECTOR, "div.detailScore__wrapper.detailScore__live")
            live_score = div.text.strip().replace("\n", "").replace(" ", "")
        except:
            live_score = "N/A"

        print(f"✅ Match valido:")
        print(f"   Torneo: {tipo} - {nome_t}")
        print(f"   Giocatori: {g1} vs {g2}")
        print(f"   Quote: {q1:.2f} – {q2:.2f}, favorito: {fav} ({qfav:.2f})")
        print(f"   Punteggio live: {live_score}")

        # Se favorito sta perdendo il primo set
        try:
            s1, s2 = map(int, live_score.split("-"))
            losing = (fav == g1 and s1 < s2) or (fav == g2 and s2 < s1)
            if losing:
                msg = f"⚠️ Il favorito {fav} sta perdendo il primo set!\n"                       f"Torneo: {tipo} - {nome_t}\n"                       f"Match: {g1} vs {g2}\n"                       f"Quote: {q1} – {q2}\n"                       f"Punteggio: {live_score}\n"                       f"Link: {link}"
                send_telegram(msg)
        except:
            pass

        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    driver.quit()
    print("[✓] Fine esecuzione.")

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except Exception as e:
        print(f"❌ Errore invio Telegram: {e}")
