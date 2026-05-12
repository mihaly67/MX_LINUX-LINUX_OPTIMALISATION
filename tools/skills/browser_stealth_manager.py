import os
import sys
import asyncio
import json
import random
import argparse
from playwright.async_api import async_playwright

async def human_like_typing(element, text):
    for char in text:
        await element.type(char, delay=random.uniform(30, 80))
    await asyncio.sleep(random.uniform(0.5, 1.2))

def parse_accessibility_tree(node, elements, target_roles=['button', 'textbox', 'link']):
    if 'role' in node and node['role'] in target_roles:
        name = node.get('name', '')
        if name or node['role'] == 'textbox':
            elements.append(node)

    if 'children' in node:
        for child in node['children']:
            parse_accessibility_tree(child, elements, target_roles)

async def analyze_and_act(page, query):
    print(">> Oldal elemzése (Accessibility Tree kinyerése)...")
    await page.wait_for_timeout(3000)

    # 1. Navigáció a sessionre (Overview oldalon)
    try:
        print(">> Legutóbbi session kiválasztása...")
        snapshot = await page.accessibility.snapshot()
        elements = []
        parse_accessibility_tree(snapshot, elements)

        session_clicked = False
        for e in elements:
            if e.get('role') == 'link' and ('Máj' in e.get('name', '') or 'May' in e.get('name', '') or 'Jules VPS' in e.get('name', '')):
                print(f">> Kattintás a session linkre: {e.get('name')}")
                await page.get_by_role("link", name=e.get('name')).first.click(force=True)
                await page.wait_for_timeout(4000)
                session_clicked = True
                break

        if not session_clicked:
            print(">> Próbálkozás a JS alapú navigációval (koordináta alapján)...")
            await page.evaluate("""() => {
                const links = document.querySelectorAll('a');
                for (let a of links) {
                    const rect = a.getBoundingClientRect();
                    if (rect.left > 300 && rect.width > 200) {
                        a.click();
                        return;
                    }
                }
            }""")
            await page.wait_for_timeout(4000)

    except Exception as e:
        print(f">> Session navigációs kísérlet befejeződött: {e}")

    # Újra kinyerjük a fát az új oldalon
    snapshot = await page.accessibility.snapshot()
    elements = []
    parse_accessibility_tree(snapshot, elements)

    print(">> Letisztított interaktív elemek (A11y Tree):")
    textarea_name = None

    for idx, e in enumerate(elements):
        role = e.get('role')
        name = e.get('name', '')
        print(f"   - [ID: {idx}] {role.upper()}: \"{name}\"")

        if role == 'textbox' or "Type a message" in name or "Message" in name or "Chat" in name:
            textarea_name = name

    try:
        print(f">> Megtaláltam a beviteli mezőt. Gépelés...")
        input_element = None

        if textarea_name:
            input_element = page.get_by_placeholder(textarea_name).first

        if not input_element or not await input_element.is_visible():
            input_element = page.locator('textarea').first

        await input_element.click(force=True)
        await human_like_typing(input_element, query)

        print(">> Próbálom elküldeni...")
        try:
            button_found = await page.evaluate('''() => {
                const svgs = document.querySelectorAll('svg path');
                for(let p of svgs) {
                    if(p.getAttribute('d').startsWith('M6 10c-1.1 0-2')) {
                        const btn = p.closest('button');
                        if (btn) {
                            btn.click();
                            return true;
                        }
                    }
                }
                return false;
            }''')

            if not button_found:
                raise Exception("Send button SVG nem található az oldalon")
        except Exception as e:
            print(f">> Fallback Enter gomb lenyomása... ({e})")
            await input_element.press("Enter")

        return True
    except Exception as e:
        print(f"HIBA a kattintás/gépelés során: {e}")
        return False

async def run(query: str):
    print(">> Indítom a Gerilla Playwright szimulátort (Firefox Native Agent Mód)...")

    cookie_path = "/home/misi/Jules_mx/cookie.json"
    temp_auth_path = "/home/misi/Jules_mx/temp/cline_auth.json"

    if not os.path.exists(cookie_path):
        print(f"HIBA: Nem található a cookie fájl: {cookie_path}")
        return

    with open(cookie_path, 'r', encoding='utf-8') as f:
        cookies = json.load(f)

    valid_cookies = []
    for c in cookies:
        if c.get("sameSite") == "NoneType":
            del c["sameSite"]
        if "partitionKey" in c:
            del c["partitionKey"]
        valid_cookies.append(c)

    os.makedirs(os.path.dirname(temp_auth_path), exist_ok=True)
    with open(temp_auth_path, 'w', encoding='utf-8') as f:
        json.dump({"cookies": valid_cookies, "origins": []}, f)

    async with async_playwright() as p:
        # FIREFOX-OT HASZNÁLUNK a blokkolás kikerülésére!
        print(">> Firefox indítása...")
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            storage_state=temp_auth_path,
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()

        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print(">> Navigáció: https://jules.google.com/repo/github/mihaly67/Raj8/overview")

        try:
            # Csak várjuk meg amíg az alap DOM megérkezik
            await page.goto("https://jules.google.com/repo/github/mihaly67/Raj8/overview", wait_until="domcontentloaded", timeout=60000)
            print(">> Oldal letöltve. Várakozás 10mp a React hidratálására...")
            await page.wait_for_timeout(10000)

            # Készítünk egy képet a legelején, hogy egyáltalán eljutottunk-e az Overviewig
            await page.screenshot(path="/home/misi/Jules_mx/temp/debug_firefox_overview.png", full_page=True)
            print(">> Kép lementve: debug_firefox_overview.png")

            success = await analyze_and_act(page, query)

            if success:
                print(">> Üzenet sikeresen elküldve! Várakozás a képernyőképhez...")
                await page.wait_for_timeout(5000)
                screenshot_path = "/home/misi/Jules_mx/temp/success_screenshot_firefox.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                print(f">> Képernyőkép mentve: {screenshot_path}")
            else:
                print(">> Valami megakadt, hiba screenshot...")
                await page.screenshot(path="/home/misi/Jules_mx/temp/error_screenshot_firefox.png", full_page=True)

        except Exception as e:
            print(f">> Kritikus hiba a navigáció során: {e}")

        await browser.close()
        print(">> Folyamat lezárva.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Browser Stealth Manager (Firefox A11y)")
    parser.add_argument("query", help="Az elküldendő üzenet")
    args = parser.parse_args()

    asyncio.run(run(args.query))
