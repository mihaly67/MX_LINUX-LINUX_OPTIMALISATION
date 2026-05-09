#!/usr/bin/env python3
import asyncio
import sys
import json
import random
import os
from playwright.async_api import async_playwright

def load_env():
    """Beolvassa a .env fájlt a gyökérből (ha létezik)."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, val = line.strip().split("=", 1)
                    os.environ[key] = val

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
    load_env()
    google_email = os.environ.get("GOOGLE_EMAIL")
    google_pwd = os.environ.get("GOOGLE_PASSWORD")

    if not google_email or not google_pwd:
        print(json.dumps({"status": "error", "error": "Hiányzó Google Credentials a .env fájlban!"}))
        return

    print(f"🕵️ Gerilla RAG indítása. Célpont: jules.google.com | Feladat: {query}", file=sys.stderr)

    url = "https://jules.google.com/session"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': random.choice([1920, 1366, 1536]), 'height': random.choice([1080, 768, 864])},
            java_script_enabled=True,
            locale="hu-HU",
            timezone_id="Europe/Budapest"
        )
        page = await context.new_page()

        try:
            print("⏳ Google Login oldal betöltése...", file=sys.stderr)
            await page.goto("https://accounts.google.com/", wait_until="networkidle", timeout=45000)
            await human_like_delay(2.0, 3.5)

            # --- EMAIL MEZŐ ---
            email_locator = page.locator("input[type='email']")
            if await email_locator.count() > 0:
                print("📧 E-mail cím beírása...", file=sys.stderr)
                await email_locator.click()
                await human_like_delay(0.5, 1.2)
                await human_like_typing(email_locator, google_email)
                await human_like_delay(1.0, 2.0)
                await page.keyboard.press("Enter")
                await human_like_delay(3.0, 5.0)

            # --- JELSZÓ MEZŐ ---
            pwd_locator = page.locator("input[type='password']")
            if await pwd_locator.count() > 0:
                print("🔑 Jelszó beírása...", file=sys.stderr)
                await pwd_locator.click()
                await human_like_delay(0.5, 1.2)
                await human_like_typing(pwd_locator, google_pwd)
                await human_like_delay(1.0, 2.0)
                await page.keyboard.press("Enter")
                await human_like_delay(4.0, 8.0)

            print(f"⏳ Átirányítás a céloldalra: {url}...", file=sys.stderr)
            await page.goto(url, wait_until="networkidle", timeout=45000)
            await human_like_delay(3.0, 5.0)

            # --- OLDAL ELEMZÉSE (DOM OLVASÁS) ---
            print("👁️ Oldal tartalmának olvasása...", file=sys.stderr)
            page_title = await page.title()
            body_text = await page.evaluate("document.body.innerText")

            # TODO: Ha megvan a pontos HTML szerkezet, ide jön a specifikus kattintás/gépelés.
            # Most kinyerjük az első 500 karaktert, hogy a Karmester lássa, bejutottunk.

            result_data = {
                "status": "success",
                "message": "Bejelentkezés végrehajtva, céloldal letapogatva.",
                "url": url,
                "page_title": page_title,
                "simulated_query": query,
                "extracted_content": body_text[:1000] + "..." if len(body_text) > 1000 else body_text
            }

            collector_dir = "/home/misi/Jules_mx/temp/stealth_collector"
            os.makedirs(collector_dir, exist_ok=True)
            import datetime
            filename = f"raj8_jules_{datetime.datetime.now().strftime('%H%M%S')}.json"
            filepath = os.path.join(collector_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)

            print(f"📁 Raj8 Kutatási Eredmény: {filepath}", file=sys.stderr)
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
