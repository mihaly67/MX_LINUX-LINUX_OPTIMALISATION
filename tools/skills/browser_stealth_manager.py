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

    # 1. BIZTONSÁGI LÉPÉS: Közvetlen ugrás a Raj8 Codebase Overview-ba
    url = "https://jules.google.com/repo/github/mihaly67/Raj8/overview"
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
            print(f"⏳ Navigálás a Raj8 Codebase-be: {url}", file=sys.stderr)
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await human_like_delay(4.0, 6.0)

            # 2. SESSION KIVÁLASZTÁSA JS ALAPJÁN
            print("👁️ Keresem az utolsó sessiont (Completed) JavaScript alapú kattintással...", file=sys.stderr)
            clicked = await page.evaluate("""
                () => {
                    // Megkeressük a felül lévő 'All' gombot
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const allBtn = buttons.find(b => b.textContent && b.textContent.trim() === 'All');
                    if (allBtn) {
                        allBtn.click();
                    }

                    // Kis késleltetés kellhet az All gomb után, de mi most lekérjük egyből
                    const links = Array.from(document.querySelectorAll('a[href^="/session/"]'));

                    // Szűrjük ki azokat a linkeket, amik a bal oldali Sidebar-ban (Recent sessions) vannak.
                    // A Sidebar általában balra van, tehát rect.left < 300,
                    // a középső tartalmi részen lévő linkek rect.left > 300 lesz.
                    const contentLinks = links.filter(link => {
                        const rect = link.getBoundingClientRect();
                        return rect.left > 300 && rect.width > 0;
                    });

                    if (contentLinks.length > 0) {
                        contentLinks[0].click(); // Legelső a listában = legutóbbi session
                        return true;
                    } else if (links.length > 0) {
                        // Fallback, ha a fenti szűrés nem működik valamiért
                        links[0].click();
                        return true;
                    }

                    return false;
                }
            """)

            if clicked:
                print("✅ Sikeres belépés az utolsó sessionbe!", file=sys.stderr)
                await human_like_delay(6.0, 8.0) # Várunk, amíg betölt a chatmező alul
            else:
                raise Exception("Nem találtam sessiont a Raj8 Overview-ban!")

            # 3. CHAT MEZŐ KERESÉSE
            print("👁️ Keresem az alsó Chat beviteli mezőt...", file=sys.stderr)
            chat_input = None
            selectors = [
                "textarea[placeholder*='essage']",
                "textarea",
                "div[contenteditable='true']",
                "input[type='text']"
            ]

            for selector in selectors:
                locs = await page.locator(selector).all()
                for loc in locs:
                    if await loc.is_visible():
                        chat_input = loc
                        print(f"✅ Beviteli mező megtalálva ({selector})", file=sys.stderr)
                        break
                if chat_input:
                    break

            if not chat_input:
                await page.screenshot(path="/home/misi/Jules_mx/temp/error_screenshot.png")
                raise Exception("Nem találtam a chat beviteli mezőt! Képernyőkép mentve.")

            # 4. ÜZENET KÜLDÉSE
            print("⌨️ Üzenet gépelése a Raj8 számára...", file=sys.stderr)
            await chat_input.focus()
            await human_like_delay(0.5, 1.5)
            await human_like_typing(chat_input, query)
            await human_like_delay(1.0, 2.5)

            print("🚀 'Nyíl' Küldés gomb megnyomása...", file=sys.stderr)

            # Enter lenyomása az elküldéshez
            print("🚀 Enter billentyű lenyomása az elküldéshez...", file=sys.stderr)

            await page.evaluate("""
                () => {
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const sendBtn = buttons.find(b => {
                        const svg = b.querySelector('svg');
                        return svg && svg.innerHTML.includes('M6 10c-1.1 0-2');
                    });
                    if (sendBtn) {
                        sendBtn.click();
                        return true;
                    }
                    return false;
                }
            """)


            await human_like_delay(8.0, 10.0)
            await page.screenshot(path="/home/misi/Jules_mx/temp/success_screenshot.png")

            result_data = {
                "status": "success",
                "message": "AI-to-AI köszöntés elküldve Raj8-nak.",
                "url": page.url,
                "simulated_query": query
            }

            import datetime
            collector_dir = "/home/misi/Jules_mx/temp/stealth_collector"
            os.makedirs(collector_dir, exist_ok=True)
            filename = f"raj8_greeting_{datetime.datetime.now().strftime('%H%M%S')}.json"
            filepath = os.path.join(collector_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)

            print(f"📁 Eredmény mentve: {filepath}", file=sys.stderr)

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
