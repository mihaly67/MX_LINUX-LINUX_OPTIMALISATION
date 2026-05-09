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

async def run_stealth_query(query: str):
    print(f"🕵️ Gerilla RAG indítása COOKIE INJECTION módszerrel. Célpont: jules.google.com | Feladat: {query}", file=sys.stderr)

    url = "https://jules.google.com/session"
    cookie_path = "/home/misi/Jules_mx/temp/cookie.json"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': random.choice([1920, 1366, 1536]), 'height': random.choice([1080, 768, 864])},
            java_script_enabled=True,
            locale="hu-HU",
            timezone_id="Europe/Budapest"
        )

        # --- COOKIE INJECTION (A HACKER ÚT) ---
        if os.path.exists(cookie_path):
            print(f"🍪 Sütik (Cookie.json) betöltése a {cookie_path} fájlból...", file=sys.stderr)
            try:
                with open(cookie_path, 'r') as f:
                    cookies = json.load(f)
                await context.add_cookies(cookies)
                print("✅ Sütik sikeresen injektálva a kontextusba!", file=sys.stderr)
            except Exception as e:
                print(f"❌ Hiba a sütik betöltésekor: {e}", file=sys.stderr)
        else:
            print(f"⚠️ FIGYELEM: Nem található a {cookie_path} fájl! A bejelentkezés elbukhat.", file=sys.stderr)

        page = await context.new_page()

        try:
            print(f"⏳ Átirányítás egyenesen a céloldalra: {url}...", file=sys.stderr)
            await page.goto(url, wait_until="networkidle", timeout=45000)
            await human_like_delay(3.0, 5.0)

            # --- OLDAL ELEMZÉSE (DOM OLVASÁS) ---
            print("👁️ Oldal tartalmának olvasása (bizonyíték a belépésről)...", file=sys.stderr)
            page_title = await page.title()
            body_text = await page.evaluate("document.body.innerText")

            result_data = {
                "status": "success",
                "message": "Cookie Injection lefutott, céloldal betöltve (login kikerülve).",
                "url": url,
                "page_title": page_title,
                "simulated_query": query,
                "extracted_content": body_text[:1000] + "..." if len(body_text) > 1000 else body_text
            }

            collector_dir = "/home/misi/Jules_mx/temp/stealth_collector"
            os.makedirs(collector_dir, exist_ok=True)
            import datetime
            filename = f"raj8_cookie_test_{datetime.datetime.now().strftime('%H%M%S')}.json"
            filepath = os.path.join(collector_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)

            print(f"📁 Raj8 Kutatási Eredmény (Cookie módszer): {filepath}", file=sys.stderr)
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
