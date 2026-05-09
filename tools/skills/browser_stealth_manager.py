#!/usr/bin/env python3
import asyncio
import sys
import json
import random
import os
from playwright.async_api import async_playwright

async def human_like_typing(locator, text: str):
    for char in text:
        delay = random.uniform(0.05, 0.15)
        if random.random() < 0.05:
            delay += random.uniform(0.3, 0.8)
        await locator.type(char, delay=int(delay * 1000))
        await asyncio.sleep(delay)

async def human_like_delay(min_sec=1.5, max_sec=4.0):
    await asyncio.sleep(random.uniform(min_sec, max_sec))

def clean_cookies(cookies):
    valid_same_site = ["Strict", "Lax", "None"]
    for cookie in cookies:
        if 'sameSite' in cookie:
            if cookie['sameSite'] is None:
                cookie.pop('sameSite')
            elif cookie['sameSite'] not in valid_same_site:
                if str(cookie['sameSite']).lower() == "no_restriction":
                    cookie['sameSite'] = "None"
                else:
                    cookie.pop('sameSite')
        for key in ['hostOnly', 'session', 'storeId', 'id', 'partitionKey']:
            if key in cookie:
                cookie.pop(key)
    return cookies

async def run_stealth_query(query: str):
    print(f"🕵️ Gerilla RAG AI-to-AI Indítása. Feladat: {query}", file=sys.stderr)

    url = "https://jules.google.com/session"
    cookie_path = "/home/misi/Jules_mx/cookie.json"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            java_script_enabled=True,
            locale="hu-HU"
        )

        if os.path.exists(cookie_path):
            with open(cookie_path, 'r') as f:
                cookies = json.load(f)
            await context.add_cookies(clean_cookies(cookies))
            print("✅ Sütik betöltve.", file=sys.stderr)
        else:
            print("❌ Sütifájl nem található! Kilépés.", file=sys.stderr)
            await browser.close()
            return

        page = await context.new_page()

        try:
            print(f"⏳ Navigálás: {url}", file=sys.stderr)
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await human_like_delay(3.0, 5.0)

            # 1. BIZTONSÁGI ELLENŐRZÉS: Csak a Raj8 codebase választható ki!
            print("👁️ Keresem a 'mihaly67 / Raj8' Codebaset...", file=sys.stderr)

            # Többféleképpen próbáljuk megtalálni a Raj8-at a bal menüben
            raj8_btn = page.locator("a.source-row", has_text="Raj8").first

            if await raj8_btn.count() > 0:
                print("✅ Raj8 Codebase megtalálva! Kattintás...", file=sys.stderr)
                await raj8_btn.click()
                await human_like_delay(4.0, 6.0) # Várjuk meg az Overview betöltését
            else:
                print("⚠️ Nem találtam a bal menüben a Raj8 gombot. Megpróbáljuk az URL-t közvetlenül elérni.", file=sys.stderr)
                await page.goto("https://jules.google.com/repo/github/mihaly67/Raj8", wait_until="domcontentloaded", timeout=45000)
                await human_like_delay(4.0, 6.0)

            # 2. SESSION KIVÁLASZTÁSA
            # A Karmester instrukciója alapján: Completed fül -> Legutolsó inaktív session
            print("👁️ Keresem a korábbi sessionöket (Taskokat)...", file=sys.stderr)

            # Megkeressük az első linket, ami a 'session' szót tartalmazza a href-ben és 'task-container'-ben van
            session_link = page.locator("a.task-container[href^='/session/']").first

            if await session_link.count() > 0:
                print("✅ Megtaláltam a legutóbbi Session-t! Kattintás...", file=sys.stderr)
                await session_link.click()
                await human_like_delay(5.0, 7.0) # Várjuk meg a chatablak DOM felépülését
            else:
                print("⚠️ Nem találtam korábbi sessiont. A kód nem folytatható új session nyitása nélkül, ami a protokoll ellen van!", file=sys.stderr)
                raise Exception("Nincs meglévő session.")

            # 3. CHAT MEZŐ KERESÉSE ÉS GÉPELÉS
            print("👁️ Keresem a Chat beviteli mezőt...", file=sys.stderr)

            # Amikor belépünk egy sessionbe, általában egy textarea, contenteditable div vagy 'chat-input' jelenik meg.
            chat_input = None
            selectors = [
                "div[contenteditable='true']",
                "textarea[placeholder*='essage']",
                "textarea",
                "input[type='text'][placeholder*='essage']"
            ]

            for selector in selectors:
                loc = page.locator(selector).first
                if await loc.count() > 0 and await loc.is_visible():
                    chat_input = loc
                    print(f"✅ Beviteli mező megtalálva: {selector}", file=sys.stderr)
                    break

            if not chat_input:
                # Végső próbálkozásként egy screenshotot csinálunk a VPS-en a hiba okáról
                await page.screenshot(path="/home/misi/Jules_mx/temp/error_screenshot.png")
                raise Exception("Nem találtam a chat beviteli mezőt a sessionön belül! Képernyőkép mentve.")

            # 4. ÜZENET KÜLDÉSE (EMBERI GÉPELÉS)
            print("⌨️ Üzenet gépelése a Raj8 számára...", file=sys.stderr)
            await chat_input.click()
            await human_like_delay(0.5, 1.5)
            await human_like_typing(chat_input, query)
            await human_like_delay(1.0, 2.5)

            print("🚀 Üzenet küldése (Enter)...", file=sys.stderr)
            # Több platform (pl. Gemini) a Shift+Enter-re új sort csinál, a sima Enterre küld.
            await chat_input.press("Enter")

            print("⏳ Várunk 10 másodpercet a szerver válaszára...", file=sys.stderr)
            await human_like_delay(10.0, 12.0)

            result_data = {
                "status": "success",
                "message": "AI-to-AI feladat elküldve Raj8-nak.",
                "url": page.url,
                "simulated_query": query
            }

            import datetime
            collector_dir = "/home/misi/Jules_mx/temp/stealth_collector"
            os.makedirs(collector_dir, exist_ok=True)
            filename = f"raj8_ai_chat_{datetime.datetime.now().strftime('%H%M%S')}.json"
            filepath = os.path.join(collector_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)

            print(f"📁 Eredmény mentve: {filepath}", file=sys.stderr)
            print(json.dumps(result_data, ensure_ascii=False, indent=2))

        except Exception as e:
            print(json.dumps({"status": "error", "error": str(e)}))
        finally:
            await browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Használat: python3 browser_stealth_manager.py <query>")
        sys.exit(1)

    user_query = " ".join(sys.argv[1:])
    asyncio.run(run_stealth_query(user_query))
