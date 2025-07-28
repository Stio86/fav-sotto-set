from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import requests, time

TELEGRAM_TOKEN = "7603257716:AAHYHZF8H6S-LyuXp8l-h1W0h40fSPp3WZU"
TELEGRAM_CHAT_ID = "66336138"

def invia_messaggio(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, data=payload)
        print(f"📬 Notifica inviata: {response.text}")
    except Exception as e:
        print(f"[❌] Errore Telegram: {e}")

def analizza_partite():
    URL = "https://www.diretta.it/tennis"

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(URL)
    print("[🔎] Apertura pagina Diretta.it...")

    try:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))).click()
    except: pass

    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH,
                "//div[@class='filters__text filters__text--default' and text()='LIVE']"))
        ).click()
        time.sleep(2)
    except: pass

    matches = driver.find_elements(By.CSS_SELECTOR, ".event__match--live")
    links = []
    for match in matches:
        mid = match.get_attribute("id")
        if mid:
            code = mid.split("_")[-1]
            links.append(f"https://www.diretta.it/partita/tennis/{code}")

    for idx, link in enumerate(links):
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get(link)
        time.sleep(2)

        try:
            b = driver.find_elements(By.CSS_SELECTOR, "a.wcl-breadcrumbItemLabel_ogiBc span")
            tipo = b[1].text.strip() if len(b) > 1 else ""
            nome_t = b[2].text.strip() if len(b) > 2 else ""
            tipo_low = tipo.lower()
            if not any(x in tipo_low for x in ["atp", "wta", "challenger"]) or "doppio" in tipo_low:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                continue
        except:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            continue

        giocatori = driver.find_elements(By.CSS_SELECTOR, "a.participant__participantName")
        g1 = giocatori[0].text.strip() if giocatori else "Gioc1"
        g2 = giocatori[1].text.strip() if len(giocatori) > 1 else "Gioc2"

        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Quote pre-partita')]"))
            ).click()
            time.sleep(2)
        except:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            continue

        quote_el = driver.find_elements(By.CSS_SELECTOR, "span[data-testid='wcl-oddsValue']")
        qvals = [e.text.strip() for e in quote_el if e.text.strip() != "-"][:2]
        if len(qvals) < 2:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            continue

        q1, q2 = map(lambda x: float(x.replace(",", ".")), qvals)
        if q1 < q2:
            fav, qfav, opp = g1, q1, g2
        else:
            fav, qfav, opp = g2, q2, g1

        if qfav >= 1.70:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            continue

        try:
            live_score = driver.find_element(By.CSS_SELECTOR, "div.detailScore__wrapper.detailScore__live").text.strip().replace(" ", "").replace(" ", "")
        except:
            live_score = "N/A"

        if live_score == "0-1" and fav == g1:
            msg = f"⚠️ *FAVORITO SOTTO 0-1!*

                    🏆 {tipo} - {nome_t}
                    👤 {g1} vs {g2}
                    📉 Favorito: {fav} @ {qfav:.2f}
                    🔗 {link}"
            invia_messaggio(msg)
        elif live_score == "1-0" and fav == g2:
            msg = f"⚠️ *FAVORITO SOTTO 0-1!*

                    🏆 {tipo} - {nome_t}
                    👤 {g1} vs {g2}
                    📉 Favorito: {fav} @ {qfav:.2f}
                    🔗 {link}"
            invia_messaggio(msg)

        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    driver.quit()
