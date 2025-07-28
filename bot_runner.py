import asyncio
from playwright.async_api import async_playwright
import requests

def send_telegram_message(message):
    token = "7603257716:AAHYHZF8H6S-LyuXp8l-h1W0h40fSPp3WZU"
    chat_id = "66336138"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        response = requests.post(url, data=payload)
        print("📩 Telegram inviato" if response.status_code == 200 else "❌ Errore Telegram:", response.text)
    except Exception as e:
        print("❌ Errore Telegram:", e)

def run_bot():
    asyncio.run(scrape())

async def scrape():
    print("🔁 Bot partito con Playwright")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://www.diretta.it/tennis", timeout=60000)
            print("📄 Pagina caricata")

            try:
                await page.click("#onetrust-accept-btn-handler", timeout=5000)
                print("✅ Cookie accettato")
            except:
                print("⚠️ Cookie già accettati")

            try:
                await page.click("text='LIVE'", timeout=10000)
                print("📍 Filtro LIVE cliccato")
                await page.wait_for_timeout(3000)
            except:
                print("❌ Filtro LIVE non trovato")

            matches = await page.query_selector_all(".event__match--live")
            print(f"[+] Match live trovati: {len(matches)}")
            if not matches:
                await browser.close()
                return

            for idx, match in enumerate(matches[:5]):
                try:
                    mid = await match.get_attribute("id")
                    if mid:
                        code = mid.split("_")[-1]
                        match_url = f"https://www.diretta.it/partita/tennis/{code}"
                        print(f"🎾 Analisi partita {idx+1}: {match_url}")

                        new_page = await browser.new_page()
                        await new_page.goto(match_url, timeout=60000)
                        await new_page.wait_for_timeout(2000)

                        tipo_torneo = await new_page.inner_text("a.wcl-breadcrumbItemLabel_ogiBc span:nth-child(2)")
                        if not any(x in tipo_torneo.lower() for x in ["atp", "wta", "challenger"]) or "doppio" in tipo_torneo.lower():
                            print("⏭ Torneo escluso")
                            await new_page.close()
                            continue

                        giocatori = await new_page.query_selector_all("a.participant__participantName")
                        g1 = await giocatori[0].inner_text()
                        g2 = await giocatori[1].inner_text()

                        try:
                            await new_page.click("button:has-text('Quote pre-partita')")
                            await new_page.wait_for_timeout(2000)
                        except:
                            print("❌ Quote pre-partita non trovate")
                            await new_page.close()
                            continue

                        q_spans = await new_page.query_selector_all("span[data-testid='wcl-oddsValue']")
                        qvals = []
                        for q in q_spans:
                            val = (await q.inner_text()).strip()
                            if val and val != "-":
                                qvals.append(val.replace(",", "."))
                            if len(qvals) == 2:
                                break

                        if len(qvals) < 2:
                            print("❌ Meno di 2 quote trovate")
                            await new_page.close()
                            continue

                        q1, q2 = float(qvals[0]), float(qvals[1])
                        fav, qfav = (g1, q1) if q1 < q2 else (g2, q2)
                        if qfav >= 1.70:
                            print(f"ℹ️ Favorito {fav} quota {qfav} ≥ 1.70 → salto")
                            await new_page.close()
                            continue

                        try:
                            live = await new_page.inner_text("div.detailScore__wrapper.detailScore__live")
                            score = live.replace("
", "").replace(" ", "")
                        except:
                            score = "N/A"

                        print(f"✅ Favorito: {fav} ({qfav}), score: {score}")
                        if score in ["0-1", "1-0"]:
                            perdente = g1 if fav == g1 and score == "0-1" else g2 if fav == g2 and score == "1-0" else None
                            if perdente == fav:
                                msg = (
                                    f"🚨 FAVORITO IN DIFFICOLTÀ

"
                                    f"👤 Match: {g1} vs {g2}
"
                                    f"🎯 Favorito: {fav} (quota {qfav})
"
                                    f"🟠 Sta perdendo il 1º set ({score})
"
                                    f"🔗 {match_url}"
                                )
                                send_telegram_message(msg)
                        await new_page.close()

                except Exception as e:
                    print(f"❌ Errore partita {idx+1}: {e}")
            await browser.close()
            print("✅ Fine esecuzione bot")
    except Exception as e:
        print("❌ Errore generale:", e)
