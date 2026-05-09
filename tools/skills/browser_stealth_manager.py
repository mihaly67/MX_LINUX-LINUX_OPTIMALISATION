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
    print(f"🕵️ Gerilla RAG indítása COOKIE INJECTION módszerrel. Célpont: jules.google.com | Feladat: {query}", file=sys.stderr)

    url = "https://jules.google.com/session"
    cookie_path = "/home/misi/Jules_mx/cookie.json"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            java_script_enabled=True,
            locale="hu-HU",
            timezone_id="Europe/Budapest"
        )

        if os.path.exists(cookie_path):
            print(f"🍪 Sütik betöltése a {cookie_path} fájlból...", file=sys.stderr)
            try:
                with open(cookie_path, 'r') as f:
                    cookies = json.load(f)

                clean_cookies_list = clean_cookies(cookies)
                await context.add_cookies(clean_cookies_list)
                print("✅ Sütik sikeresen injektálva a Playwright kompatibilitási szűrő után!", file=sys.stderr)
            except Exception as e:
                print(f"❌ Hiba a sütik betöltésekor: {e}", file=sys.stderr)
        else:
            print(f"⚠️ FIGYELEM: Nem található a {cookie_path} fájl!", file=sys.stderr)

        page = await context.new_page()

        try:
            print(f"⏳ Átirányítás egyenesen a céloldalra: {url}...", file=sys.stderr)
            await page.goto(url, wait_until="networkidle", timeout=45000)
            await human_like_delay(5.0, 7.0) # Több időt hagyunk a dinamikus tartalmak (codebases) betöltésére

            print("👁️ Interaktív elemek (MINDEN LINK ÉS GOMB) keresése...", file=sys.stderr)

            # Kibővített DOM keresés: Szűrő nélkül hozzuk le az összes linket és gombot!
            interactive_elements = await page.evaluate("""
                () => {
                    const elements = Array.from(document.querySelectorAll('a, button, div[role="button"], div[role="treeitem"]'));
                    return elements.map(el => {
                        return {
                            tag: el.tagName,
                            text: el.innerText ? el.innerText.replace(/\\n/g, ' ').trim() : '',
                            className: el.className,
                            role: el.getAttribute('role')
                        };
                    }).filter(el => el.text.length > 0 && el.text.length < 100);
                }
            """)

            page_title = await page.title()

            result_data = {
                "status": "success",
                "message": "DOM Explorer mód lefutott.",
                "url": url,
                "page_title": page_title,
                "simulated_query": query,
                "all_interactive_elements": interactive_elements
            }

            collector_dir = "/home/misi/Jules_mx/temp/stealth_collector"
            os.makedirs(collector_dir, exist_ok=True)
            import datetime
            filename = f"dom_explorer_{datetime.datetime.now().strftime('%H%M%S')}.json"
            filepath = os.path.join(collector_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)

            print(f"📁 DOM Explorer Eredmény: {filepath}", file=sys.stderr)

            # Kinyomtatjuk a konzolra is az első 15 elemet, hogy lássuk, hol járunk
            print("Kinyert elemek listája (első 15):", file=sys.stderr)
            for i, el in enumerate(interactive_elements[:15]):
                print(f"[{i}] {el['tag']}: {el['text']} (Role: {el.get('role')})", file=sys.stderr)

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
